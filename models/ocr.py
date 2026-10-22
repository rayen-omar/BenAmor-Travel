import datetime

from odoo import models, fields, _

import base64
import io
import os
import logging
import pytesseract
from PIL import Image, UnidentifiedImageError
from pdf2image import convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
import json

from google import genai
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class OcrInvoice(models.Model):
    _name = "ocr.invoice"
    _description = "OCR Invoice"

    name = fields.Char(string="Invoice Name", required=True)

    invoice_file = fields.Binary(
        string="Invoice Image / PDF",
        attachment=True,
        required=True,
    )

    invoice_filename = fields.Char(string="Filename")

    extracted_text = fields.Text(
        string="Extracted Invoice Text",
        readonly=True,
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        ondelete="cascade",
    )
    json_text = fields.Text(
        string="Gemini JSON Result",
        readonly=True,
    )
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("text_extracted", "Text Extracted"),
            ("analyzed", "Analyzed"),
            ("invoiced", "Invoiced"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    type = fields.Selection(selection=[("image", "Image"),
            ("pdf", "Pdf"),], string="Status", default="image", required=True, tracking=True,)

    def action_extract_ocr(self):
        self.ensure_one()

        if not self.invoice_file:
            raise UserError("Please upload an invoice image or PDF.")

        pytesseract.pytesseract.tesseract_cmd = (
            r"/usr/bin/tesseract"
        )
        file_bytes = base64.b64decode(self.invoice_file)
        filename = (self.invoice_filename or "").lower()

        try:
            if filename.endswith(".pdf"):
                # Update this path to your Poppler installation.
                poppler_path = (
                    r"/usr/bin"
                )

                if not os.path.isdir(poppler_path):
                    raise UserError(
                        "Poppler was not found. Update poppler_path "
                        "to your actual Poppler bin directory."
                    )

                images = convert_from_bytes(
                    file_bytes,
                    dpi=200,
                    poppler_path=poppler_path,
                    first_page=1,
                    last_page=10,
                )

            elif filename.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")):
                image = Image.open(io.BytesIO(file_bytes))
                images = [image.convert("RGB")]

            else:
                raise UserError(
                    "Unsupported file. Upload a PDF, PNG, JPG, or TIFF."
                )

            extracted_pages = []

            for page_number, image in enumerate(images, start=1):
                text = pytesseract.image_to_string(
                    image,
                    lang="eng+fra",
                )
                extracted_pages.append(
                    f"--- Page {page_number} ---\n{text.strip()}"
                )

            self.extracted_text = "\n\n".join(extracted_pages)

            if not self.extracted_text.strip():
                raise UserError(
                    "No text was detected. Check the document quality "
                    "and installed OCR languages."
                )

        except (UnidentifiedImageError, PDFSyntaxError):
            raise UserError("The uploaded file could not be read.")
        except (PDFInfoNotInstalledError, PDFPageCountError):
            raise UserError(
                "Unable to process the PDF. Check the Poppler installation."
            )
        except pytesseract.TesseractNotFoundError:
            raise UserError("Tesseract was not found on this computer.")
        self.write({
            "status": "text_extracted",
        })
        return True

    def action_parse_with_gemini(self):
        self.ensure_one()
        api = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("benamor_travel.api_key")
        )
        api_key = os.environ.get(api=api)

        if not api_key:
            raise UserError(
                _(
                    "Gemini API key is not configured. Set the "
                    "benamor_travel.api_key system parameter."
                )
            )
        if not self.extracted_text:
            raise UserError(_("Please extract the invoice text first."))

        client = genai.Client(api_key=api_key)

        prompt = """
    You are an invoice data extraction assistant.
    Extract information from the invoice text below.

    Return ONLY valid JSON using exactly this structure:

    {
      "invoice_number": "",
      "invoice_date": "",
      "due_date": "",
      "vendor": {
        "name": "",
        "country": ""
      },
      "customer": {
        "name": ""
      },
      "line_items": [
        {
          "description": "",
          "quantity": 0.0,
          "unit_price": 0.0,
          "tax_rate": "0%",
          "amount": 0.0
        }
      ],
      "payment_communication": "",
      "summary": {
        "untaxed_amount": 0.0,
        "tax_rate": "0%",
        "tax_amount": 0.0,
        "total_amount": 0.0,
        "currency": ""
      }
    }

    Rules:
    - Always include every field shown in the schema.
    - Use an empty string for missing text values.
    - Use 0.0 for missing numeric values.
    - Dates must use ISO format YYYY-MM-DD.
    - Convert dates carefully. Do not confuse month and day.
    - quantity, unit_price, amount, and summary amounts must be numbers.
    - tax_rate must be a string such as "15%".
    - Each invoice product or service must be a separate line_items entry.
    - amount means the line amount excluding tax, unless the invoice clearly
      specifies otherwise.
    - Do not invent missing information.
    - Preserve the invoice currency code, such as USD, EUR, or TND.
    - Do not include Markdown fences or explanations.

    INVOICE TEXT:
    """ + self.extracted_text

        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0,
                },
            )

            result = json.loads(response.text or "{}")

            required_keys = {
                "invoice_number",
                "invoice_date",
                "due_date",
                "vendor",
                "customer",
                "line_items",
                "payment_communication",
                "summary",
            }

            missing = required_keys - result.keys()
            if missing:
                raise UserError(
                    _("Gemini JSON is missing fields: %s")
                    % ", ".join(sorted(missing))
                )

            # Save the structured JSON in the OCR record.
            self.write({
                "json_text": json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=2,
                ),
                "status": "analyzed",
            })

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Invoice Analysis"),
                    "message": _("Invoice data extracted successfully."),
                    "type": "success",
                    "sticky": False,
                },
            }

        except UserError:
            raise
        except Exception as exc:
            _logger.exception("Gemini invoice analysis failed")
            raise UserError(
                _("Gemini invoice analysis failed: %s") % str(exc)
            ) from exc

    def parse_invoice_date(self,date_value, field_name):
        if not date_value:
            return False

        date_value = str(date_value).strip()

        formats = (
            "%Y-%m-%d",  # 2026-10-13
            "%d/%m/%Y",  # 13/10/2026
            "%m/%d/%Y",  # 10/13/2026
        )

        for date_format in formats:
            try:
                return datetime.datetime.strptime(
                    date_value, date_format
                ).date()
            except ValueError:
                continue

        raise UserError(_(
            "Invalid %s: %s. Expected YYYY-MM-DD, DD/MM/YYYY "
            "or MM/DD/YYYY."
        ) % (field_name, date_value))

    def action_create_invoice(self):
        self.ensure_one()
        if not self.json_text:
            raise UserError(_("Please analyze the invoice first."))

        try:
            data = json.loads(self.json_text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise UserError(_("The Gemini result is not valid JSON.")) from exc

        # Seller = supplier for a vendor bill.
        seller = data.get("seller") or data.get("customer") or {}
        supplier_name = seller.get("name")

        if not supplier_name:
            raise UserError(_("The seller name is missing from the JSON."))

        partner = self.env["res.partner"].search([
            ("name", "=", supplier_name),
        ], limit=1)

        if not partner:
            partner = self.env["res.partner"].create({
                "name": supplier_name,
                "company_type": "company",
                "supplier_rank": 1,
                "country_id": self.env["res.country"].search([
                    ("name", "=", data.get("vendor", {}).get("country", ""))
                ], limit=1).id or False,
            })

        # Parse invoice date: JSON example uses DD/MM/YYYY.
        invoice_date = self.parse_invoice_date(
            data.get("invoice_date"),
            "invoice date",
        )

        due_date = self.parse_invoice_date(
            data.get("due_date"),
            "due date",
        )

        # Optional defaults
        if not invoice_date:
            invoice_date = fields.Date.context_today(self)

        # Currency from the financial summary or first item.
        summary = data.get("financial_summary") or {}
        currency_name = (
                summary.get("currency")
                or (data.get("items") or [{}])[0].get("currency")
        )

        # Map DT to TND if your database uses Tunisia's standard currency code.
        if currency_name == "DT":
            currency_name = "TND"

        currency = self.env["res.currency"].search([
            ("name", "=", currency_name),
            ("active", "=", True),
        ], limit=1)


        items = data.get("items") or data.get("line_items") or []
        if not items:
            raise UserError(_("No invoice items were found in the JSON."))

        invoice_lines = []

        for item in items:
            description = item.get("description")
            quantity = float(item.get("quantity") or 0)
            unit_price = float(item.get("unit_price") or 0)

            if not description or quantity <= 0:
                raise UserError(_(
                    "Each item must have a description and a positive quantity."
                ))

            # Search for an existing product
            product = self.env["product.product"].search([
                ("name", "=", description),
            ], limit=1)

            # Create the product if it does not exist
            if not product:
                product = self.env["product.product"].create({
                    "name": description,
                    "default_code": item.get("item_code") or False,
                    "type": "consu",
                    "purchase_ok": True,
                    "sale_ok": True,
                    "list_price": float(item.get("unit_price") or 0),
                })

            line_vals = {
                "product_id": product.id,
                "name": description,
                "quantity": quantity,
                "price_unit": unit_price,
            }

            # Apply the VAT rate if an appropriate purchase tax exists.
            vat_text = str(item.get("vat_rate") or "").replace("%", "").strip()
            if vat_text:
                try:
                    vat_rate = float(vat_text)
                except ValueError as exc:
                    raise UserError(_(
                        "Invalid VAT rate '%s'."
                    ) % item.get("vat_rate")) from exc

                taxes = self.env["account.tax"].search([
                    ("type_tax_use", "=", "purchase"),
                    ("company_id", "=", self.env.company.id),
                    ("amount_type", "=", "percent"),
                    ("amount", "=", vat_rate),
                    ("active", "=", True),
                ], limit=1)

                if not taxes:
                    raise UserError(_(
                        "No purchase VAT tax of %s%% exists for this company."
                    ) % vat_rate)

                line_vals["tax_ids"] = [(6, 0, taxes.ids)]

            invoice_lines.append((0, 0, line_vals))

        invoice = self.invoice_id

        if not invoice:
            raise UserError(_("No existing invoice is linked to this OCR record."))

        if invoice.move_type in ("in_invoice", "in_refund"):
            move_type = "in_invoice"
        elif invoice.move_type in ("out_invoice", "out_refund"):
            move_type = "out_invoice"
        else:
            raise UserError(_("Unsupported invoice type."))

        if invoice.state != "draft":
            raise UserError(_("Only draft invoices can be updated."))

        # Update the existing invoice header and replace its lines
        invoice.write({
            "move_type": move_type,
            "partner_id": partner.id,
            "currency_id": currency.id if currency else self.env.company.currency_id.id,
            "invoice_date": invoice_date,
            "ref": data.get("invoice_number") or False,
            "invoice_line_ids": [
                (5, 0, 0),  # Remove existing invoice lines
                *invoice_lines,
            ],
        })
        self.write({
            "status": "invoiced",
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }