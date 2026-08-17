from odoo import api, fields, models


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

    @api.depends("travel_file_id.passenger_ids.name")
    def _compute_travel_passenger_names(self):
        for move in self:
            names = move.travel_file_id.passenger_ids.mapped("name")
            move.travel_passenger_names = ", ".join(names) if names else False
