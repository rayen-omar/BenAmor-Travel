from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    travel_file_id = fields.Many2one(
        "travel.file", string="Dossier voyage", index=True, copy=False
    )

    def _prepare_invoice(self):
        """Propage le dossier de voyage vers la facture."""
        vals = super()._prepare_invoice()
        if self.travel_file_id:
            vals["travel_file_id"] = self.travel_file_id.id
        return vals
