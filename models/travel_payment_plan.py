from odoo import fields, models


class TravelPaymentPlan(models.Model):
    _name = "travel.payment.plan"
    _description = "Echeance de paiement dossier"
    _order = "date_due, id"

    file_id = fields.Many2one(
        "travel.file", string="Dossier", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Libelle", required=True, default="Echeance")
    date_due = fields.Date(string="Echeance", required=True)
    amount = fields.Monetary(string="Montant", required=True)
    currency_id = fields.Many2one(related="file_id.currency_id", store=True)
    state = fields.Selection(
        [("todo", "A encaisser"), ("done", "Encaisse"), ("late", "En retard")],
        default="todo",
        string="Etat",
        copy=False,
    )
    note = fields.Char()
