from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    travel_file_id = fields.Many2one(
        "travel.file", string="Dossier voyage", index=True, copy=False
    )
    travel_destination_id = fields.Many2one(
        related="travel_file_id.destination_id", string="Destination"
    )
    travel_date_departure = fields.Date(
        related="travel_file_id.date_departure", string="Date de depart"
    )
    travel_date_return = fields.Date(
        related="travel_file_id.date_return", string="Date de retour"
    )
    travel_passenger_names = fields.Char(
        string="Passagers", compute="_compute_travel_passenger_names"
    )

    ocr_ids = fields.One2many(
        "ocr.invoice",
        "invoice_id",
        string="ocr",
    )
    ocr_is_invoiced = fields.Boolean(
        compute="_compute_ocr_is_invoiced",
    )

    @api.depends("travel_file_id.passenger_ids.name")
    def _compute_travel_passenger_names(self):
        for move in self:
            names = move.travel_file_id.passenger_ids.mapped("name")
            move.travel_passenger_names = ", ".join(names) if names else False

    @api.depends("ocr_ids.status")
    def _compute_ocr_is_invoiced(self):
        for move in self:
            move.ocr_is_invoiced = any(
                ocr.status == "invoiced"
                for ocr in move.ocr_ids
            )

    def action_create_ocr(self):
        self.ensure_one()

        ocr = self.env["ocr.invoice"].create({
            "name": self.name or _("New ocr"),
            "invoice_id": self.id,
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("Ocr"),
            "res_model": "ocr.invoice",
            "view_mode": "form",
            "res_id": ocr.id,
            "target": "current",
        }

    def action_view_ocr(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "base_addons.action_ocr_invoice"
        )

        ocr_ids = self.ocr_ids

        if not ocr_ids:
            action.update({
                "view_mode": "form",
                "views": [
                    (self.env.ref("base_addons.view_ocr_invoice_form").id, "form")
                ],
                "res_id": False,
                "domain": [],
                "context": {
                    "default_invoice_id": self.id,
                    "default_date": fields.Date.context_today(self),
                },
            })

        elif len(ocr_ids) == 1:
            action.update({
                "view_mode": "form",
                "views": [
                    (self.env.ref("base_addons.view_ocr_invoice_form").id, "form")
                ],
                "res_id": ocr_ids.id,
                "domain": [("id", "=", ocr_ids.id)],
                "context": {
                    "default_invoice_id": self.id,
                },
            })

        else:
            action.update({
                "view_mode": "list,form",
                "views": [
                    (self.env.ref("base_addons.view_ocr_invoice_list").id, "list"),
                    (self.env.ref("base_addons.view_ocr_invoice_form").id, "form"),
                ],
                "res_id": False,
                "domain": [("invoice_id", "=", self.id)],
                "context": {
                    "default_invoice_id": self.id,
                },
            })

        return action
