from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # --- Profil voyageur ---
    is_traveler = fields.Boolean(
        string="Voyageur",
        help="Ce contact voyage lui-meme. Ses documents sont conserves ici.",
    )
    travel_birthdate = fields.Date(string="Date de naissance")
    travel_nationality_id = fields.Many2one("res.country", string="Nationalite")
    travel_passport_number = fields.Char(string="N. Passeport")
    travel_cin_number = fields.Char(string="N. Cin")
    travel_passport_expiry = fields.Date(string="Expiration passeport")
    travel_note = fields.Text(
        string="Preferences de voyage",
        help="Siege, repas special, allergies, remarques.",
    )

    # --- Historique ---
    travel_file_count = fields.Integer(
        string="Dossiers", compute="_compute_travel_stats"
    )
    travel_trip_count = fields.Integer(
        string="Voyages effectues", compute="_compute_travel_stats"
    )
    travel_last_date = fields.Date(
        string="Dernier voyage", compute="_compute_travel_stats"
    )

    travel_is_tunisian = fields.Boolean(
        compute='_compute_travel_is_tunisian'
    )

    @api.depends('travel_nationality_id')
    def _compute_travel_is_tunisian(self):
        for record in self:
            record.travel_is_tunisian = (
                    record.travel_nationality_id.code == 'TN'
            )

    def _compute_travel_stats(self):
        File = self.env["travel.file"]
        Passenger = self.env["travel.passenger"]
        for partner in self:
            files = File.search([("partner_id", "=", partner.id)])
            partner.travel_file_count = len(files)
            trips = files.filtered(lambda f: f.state in ("confirmed", "done"))
            as_pax = Passenger.search([("partner_id", "=", partner.id)])
            partner.travel_trip_count = len(trips) + len(
                as_pax.mapped("file_id").filtered(
                    lambda f: f.state in ("confirmed", "done") and f not in trips
                )
            )
            dates = (trips | as_pax.mapped("file_id")).mapped("date_departure")
            dates = [d for d in dates if d]
            partner.travel_last_date = max(dates) if dates else False

    def action_view_travel_files(self):
        self.ensure_one()
        passenger_files = self.env["travel.passenger"].search(
            [("partner_id", "=", self.id)]
        ).mapped("file_id")
        domain = [
            "|",
            ("partner_id", "=", self.id),
            ("id", "in", passenger_files.ids),
        ]
        return {
            "type": "ir.actions.act_window",
            "name": _("Dossiers de voyage"),
            "res_model": "travel.file",
            "view_mode": "list,form",
            "domain": domain,
            "context": {"default_partner_id": self.id},
        }
