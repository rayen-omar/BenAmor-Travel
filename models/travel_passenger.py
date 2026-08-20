from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class TravelPassenger(models.Model):
    _name = "travel.passenger"
    _description = "Passager"
    _order = "file_id, pax_type, name"

    name = fields.Char(string="Nom & Prénom", required=True)
    file_id = fields.Many2one(
        "travel.file", string="Dossier", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact lie",
        help="Lier a un contact permet de reutiliser ses documents "
        "d'un dossier a l'autre.",
    )
    pax_type = fields.Selection(
        [("adt", "Adulte"), ("chd", "Enfant"), ("inf", "Bebe")],
        string="Type",
        default="adt",
        required=True,
    )
    gender = fields.Selection([("m", "Masculin"), ("f", "Feminin")], string="Genre")
    birthdate = fields.Date(string="Date de naissance")
    nationality_id = fields.Many2one("res.country", string="Nationalite")
    phone = fields.Char()
    email = fields.Char()

    passport_number = fields.Char(string="N° de Passeport")
    passport_expiry = fields.Date(string="Date d'Expiration")
    passport_state = fields.Selection(
        [
            ("missing", "Non renseigne"),
            ("valid", "Valide"),
            ("warning", "Expire bientot"),
            ("expired", "Expire"),
        ],
        string="Etat passeport",
        compute="_compute_passport_state",
        store=True,
    )
    visa_state = fields.Selection(
        [
            ("na", "Non requis"),
            ("todo", "A deposer"),
            ("pending", "En cours"),
            ("granted", "Obtenu"),
            ("refused", "Refuse"),
        ],
        string="Visa",
        default="na",
        copy=False,
    )
    note = fields.Text()
    cin_number = fields.Char(string="N° de cin")

    is_tunisian = fields.Boolean(
        compute='_compute_is_tunisian'
    )

    @api.depends('nationality_id')
    def _compute_is_tunisian(self):
        for record in self:
            record.is_tunisian = (
                    record.nationality_id.code == 'TN'
            )
    @api.depends("passport_expiry", "file_id.date_departure")
    def _compute_passport_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.passport_expiry:
                rec.passport_state = "missing"
                continue
            ref = rec.file_id.date_departure or today
            if rec.passport_expiry < ref:
                rec.passport_state = "expired"
            elif rec.passport_expiry < ref + relativedelta(months=6):
                rec.passport_state = "warning"
            else:
                rec.passport_state = "valid"

    # ------------------------------------------------------------------
    # Reutilisation des donnees du contact
    # ------------------------------------------------------------------
    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Reprend les informations deja connues du contact."""
        p = self.partner_id
        if not p:
            return
        self.name = self.name or p.name
        self.phone = self.phone or p.phone
        self.email = self.email or p.email
        self.birthdate = self.birthdate or p.travel_birthdate
        self.nationality_id = self.nationality_id or p.travel_nationality_id
        self.passport_number = self.passport_number or p.travel_passport_number
        self.cin_number = self.cin_number
        self.passport_expiry = self.passport_expiry or p.travel_passport_expiry

    def _sync_to_partner(self):
        """Enregistre les documents sur le contact pour les prochains dossiers."""
        for rec in self:
            p = rec.partner_id
            if not p:
                continue
            vals = {"is_traveler": True}
            if rec.passport_number and p.travel_passport_number != rec.passport_number:
                vals["travel_passport_number"] = rec.passport_number
            if rec.passport_expiry and p.travel_passport_expiry != rec.passport_expiry:
                vals["travel_passport_expiry"] = rec.passport_expiry
            if rec.birthdate and not p.travel_birthdate:
                vals["travel_birthdate"] = rec.birthdate
            if rec.nationality_id and not p.travel_nationality_id:
                vals["travel_nationality_id"] = rec.nationality_id.id
            p.write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_to_partner()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {"passport_number", "passport_expiry", "birthdate", "nationality_id",
            "partner_id"} & set(vals):
            self._sync_to_partner()
        return res

    def action_create_partner(self):
        """Cree un contact a partir du passager, et le lie."""
        for rec in self.filtered(lambda r: not r.partner_id):
            rec.partner_id = self.env["res.partner"].create(
                {
                    "name": rec.name,
                    "phone": rec.phone,
                    "email": rec.email,
                    "is_traveler": True,
                    "travel_birthdate": rec.birthdate,
                    "travel_nationality_id": rec.nationality_id.id,
                    "travel_passport_number": rec.passport_number,
                    "travel_passport_expiry": rec.passport_expiry,
                }
            )
