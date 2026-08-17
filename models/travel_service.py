from odoo import api, fields, models

SERVICE_TYPES = [
    ("flight", "Vol"),
    ("hotel", "Hebergement"),
    ("package", "Forfait / Circuit"),
    ("omra", "Prestation Omra"),
    ("visa", "Visa"),
    ("insurance", "Assurance"),
    ("transfer", "Transfert"),
    ("car", "Location voiture"),
    ("other", "Autre"),
]

# Types de prestation factures par personne
PER_PAX_TYPES = ("flight", "visa", "insurance", "omra", "package")


class TravelService(models.Model):
    _name = "travel.service"
    _description = "Prestation de voyage"
    _order = "file_id, sequence, id"

    file_id = fields.Many2one(
        "travel.file", string="N° Dossier", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    service_type = fields.Selection(
        SERVICE_TYPES, string="Type", required=True, default="flight"
    )
    product_id = fields.Many2one(
        "product.product", string="Service", domain=[("type", "=", "service")]
    )
    description = fields.Char(string="Designation", required=True)
    passenger_ids = fields.Many2many("travel.passenger", string="Voyageurs concernés")

    date_start = fields.Date(string="Date debut")
    date_end = fields.Date(string="Date fin")
    quantity = fields.Float(string="Qte", default=1.0, required=True)

    # --- Achat ---
    supplier_id = fields.Many2one("res.partner", string="Prestataire")
    supplier_ref = fields.Char(string="Réf. Prestataire", copy=False)
    cost_currency_id = fields.Many2one(
        "res.currency",
        string="Devise achat",
        default=lambda self: self.env.company.currency_id,
    )
    cost_amount = fields.Monetary(
        string="Prix d'Achat Net", currency_field="cost_currency_id"
    )
    cost_company = fields.Monetary(
        string="Cout (devise societe)",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )

    # --- Vente ---
    markup_rate = fields.Float(
        string="Marge cible (%)",
        help="Saisir un taux pour calculer automatiquement le prix de vente "
        "a partir du cout. Laisser vide pour fixer le prix a la main.",
    )
    sale_price_unit = fields.Monetary(string="Prix de Vente Unitaire", currency_field="currency_id")
    sale_subtotal = fields.Monetary(
        string="Total vente",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    margin = fields.Monetary(
        string="Marge",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    margin_rate = fields.Float(
        string="Taux reel (%)", compute="_compute_amounts", store=True
    )
    excluded_from_invoice = fields.Boolean(
        string="Hors facture", help="Prestation suivie mais non refacturee au client."
    )

    currency_id = fields.Many2one(related="file_id.currency_id", store=True)
    company_id = fields.Many2one(related="file_id.company_id", store=True)

    # --- Annulation ---
    cancellation_deadline = fields.Date(
        string="Limite d'annulation",
        help="Date au-dela de laquelle l'annulation devient payante.",
    )
    cancellation_policy = fields.Char(
        string="Conditions d'annulation",
        help="Exemple : gratuit jusqu'a J-15, puis 50 %, non remboursable a J-7.",
    )
    deadline_state = fields.Selection(
        [
            ("none", "Non renseignee"),
            ("ok", "Delai confortable"),
            ("soon", "Echeance proche"),
            ("passed", "Delai depasse"),
        ],
        string="Etat du delai",
        compute="_compute_deadline_state",
        store=True,
    )

    # --- Champs specifiques Vol ---
    airline_id = fields.Many2one("travel.airline", string="Compagnie")
    pnr = fields.Char(string="N° PNR (GDS)", copy=False)
    ticket_number = fields.Char(string="N° Billet Électronique", copy=False)
    route = fields.Char(string="Itineraire", help="Ex: TUN-CDG-TUN")

    # --- Champs specifiques Hebergement ---
    hotel_id = fields.Many2one("travel.hotel", string="Hotel")
    room_type = fields.Selection(
        [
            ("single", "Single"),
            ("double", "Double"),
            ("triple", "Triple"),
            ("quad", "Quadruple"),
        ],
        string="Type de chambre",
    )
    board = fields.Selection(
        [
            ("ro", "Sans repas"),
            ("bb", "Petit dejeuner"),
            ("hb", "Demi-pension"),
            ("fb", "Pension complete"),
            ("ai", "All inclusive"),
        ],
        string="Formule",
    )
    nights = fields.Integer(string="Nuitees", compute="_compute_nights", store=True)

    @api.depends("date_start", "date_end")
    def _compute_nights(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end > rec.date_start:
                rec.nights = (rec.date_end - rec.date_start).days
            else:
                rec.nights = 0

    @api.depends("cancellation_deadline")
    def _compute_deadline_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.cancellation_deadline:
                rec.deadline_state = "none"
            elif rec.cancellation_deadline < today:
                rec.deadline_state = "passed"
            elif (rec.cancellation_deadline - today).days <= 7:
                rec.deadline_state = "soon"
            else:
                rec.deadline_state = "ok"

    @api.depends(
        "cost_amount", "cost_currency_id", "quantity", "sale_price_unit",
        "date_start", "currency_id",
    )
    def _compute_amounts(self):
        for rec in self:
            company = rec.company_id or rec.env.company
            comp_cur = company.currency_id
            date = rec.date_start or fields.Date.context_today(rec)
            if rec.cost_currency_id and rec.cost_currency_id != comp_cur:
                cost = rec.cost_currency_id._convert(
                    rec.cost_amount, comp_cur, company, date
                )
            else:
                cost = rec.cost_amount
            qty = rec.quantity or 1.0
            rec.cost_company = cost * qty
            rec.sale_subtotal = rec.sale_price_unit * qty
            rec.margin = rec.sale_subtotal - rec.cost_company
            rec.margin_rate = (
                rec.margin / rec.sale_subtotal * 100.0 if rec.sale_subtotal else 0.0
            )

    # ------------------------------------------------------------------
    # Calcul du prix de vente a partir de la marge cible
    # ------------------------------------------------------------------
    def _cost_in_company_currency(self):
        """Cout unitaire converti dans la devise de la societe."""
        self.ensure_one()
        company = self.company_id or self.env.company
        comp_cur = company.currency_id
        date = self.date_start or fields.Date.context_today(self)
        if self.cost_currency_id and self.cost_currency_id != comp_cur:
            return self.cost_currency_id._convert(
                self.cost_amount, comp_cur, company, date
            )
        return self.cost_amount

    def _apply_markup(self):
        """Prix de vente = cout / (1 - taux). Taux = marge sur prix de vente."""
        for rec in self:
            if not rec.markup_rate:
                continue
            cost = rec._cost_in_company_currency()
            rate = min(rec.markup_rate, 99.0) / 100.0
            rec.sale_price_unit = cost / (1.0 - rate) if rate else cost

    @api.onchange("markup_rate", "cost_amount", "cost_currency_id")
    def _onchange_markup(self):
        if self.markup_rate:
            self._apply_markup()

    # ------------------------------------------------------------------
    # Quantite basee sur le nombre de passagers
    # ------------------------------------------------------------------
    @api.onchange("service_type")
    def _onchange_service_type_qty(self):
        """Pour les prestations vendues par personne, propose le nb de passagers."""
        if self.service_type in PER_PAX_TYPES and self.file_id.passenger_ids:
            self.quantity = len(self.file_id.passenger_ids)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            if not self.sale_price_unit and not self.markup_rate:
                self.sale_price_unit = self.product_id.list_price

    def name_get(self):
        return [(r.id, r.description or "/") for r in self]
