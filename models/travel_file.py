from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .travel_service import PER_PAX_TYPES


class TravelFile(models.Model):
    _name = "travel.file"
    _description = "Dossier de voyage"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_departure desc, id desc"

    name = fields.Char(
        string="N° Dossier", required=True, copy=False, readonly=True, default="/"
    )
    partner_id = fields.Many2one("res.partner", string="Client Facturé", tracking=True)
    file_type = fields.Selection(
        [
            ("ticket", "Billetterie"),
            ("hotel", "Hotel"),
            ("package", "Sejour / Circuit"),
            ("omra", "Omra / Hajj"),
            ("visa", "Visa"),
            ("vol", "Vol"),
            ("b2b", "B2B agence"),
            ("other", "Autre"),
        ],
        string="Type de dossier",
        default="ticket",
        required=True,
        tracking=True,
    )
    user_id = fields.Many2one(
        "res.users", string="Agent de Voyage", default=lambda self: self.env.user, tracking=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", string="Devise societe", store=True
    )

    # --- Modele de dossier ---
    is_template = fields.Boolean(
        string="Modele de dossier",
        copy=False,
        help="Un modele n'est pas un vrai dossier. Il sert de point de depart "
        "pour creer de nouveaux dossiers identiques.",
    )
    template_name = fields.Char(
        string="Nom du modele", help="Exemple : Omra 10 jours, Istanbul 7 nuits"
    )
    invoice_ids = fields.One2many(
        "account.move",
        "travel_file_id",
        string="Factures",
    )
    date_open = fields.Date(string="Date ouverture", default=fields.Date.context_today)
    date_departure = fields.Date(string="Départ Prévu", tracking=True)
    date_return = fields.Date(string="Retour Prévu")
    destination_id = fields.Many2one("travel.destination", string="Destination")

    service_ids = fields.One2many("travel.service", "file_id", string="Services Inclus")
    passenger_ids = fields.One2many("travel.passenger", "file_id", string="Liste des Voyageurs")
    payment_plan_ids = fields.One2many(
        "travel.payment.plan", "file_id", string="Echeancier"
    )
    document_ids = fields.One2many("travel.document", "file_id", string="Documents")
    passenger_count = fields.Integer(compute="_compute_counts", store=True)
    document_missing_count = fields.Integer(
        string="Documents manquants", compute="_compute_counts", store=True
    )

    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Compte analytique", copy=False
    )
    sale_order_ids = fields.One2many("sale.order", "travel_file_id", string="Commandes")
    sale_order_count = fields.Integer(compute="_compute_counts")
    facilitate = fields.Many2one(
        "travel.facilitate", string="faciliter"
    )
    target_margin_rate = fields.Float(
        string="Marge cible du dossier (%)",
        help="Applique ce taux a toutes les prestations via le bouton dedie.",
    )
    amount_sale = fields.Monetary(
        string="Total vente", compute="_compute_amounts", store=True
    )
    amount_cost = fields.Monetary(
        string="Total cout", compute="_compute_amounts", store=True
    )
    margin = fields.Monetary(string="Marge", compute="_compute_amounts", store=True)
    margin_rate = fields.Float(
        string="Taux de marge (%)", compute="_compute_amounts", store=True
    )
    discount = fields.Monetary(
        string="Discount",
        currency_field="currency_id",
        tracking=True,
    )

    total_discount = fields.Monetary(
        string="Totale avec remise",
        currency_field="currency_id",
        compute="_compute_amounts",
        store=True,
    )
    next_deadline = fields.Date(
        string="Prochaine limite d'annulation",
        compute="_compute_next_deadline",
        store=True,
    )

    is_upcoming = fields.Boolean(
        compute="_compute_is_upcoming",
        search="_search_upcoming"
    )
    is_deadline_soon = fields.Boolean(
        compute="_compute_is_deadline_soon",
        search="_search_deadline_soon"
    )

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("option", "Option"),
            ("confirmed", "Confirme"),
            ("done", "Cloture"),
            ("cancel", "Annule"),
        ],
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    note = fields.Html(string="Notes internes")
    # ---------------------------------------------------------
    # ROOM
    # ---------------------------------------------------------

    room_type = fields.Selection(
        [
            ("individuelle", "individuelle"),
            ("double", "Double"),
            ("tripler", "tripler"),
            ("quadruple", "Quadruple"),
            ("suite", "Suite"),
            ("famille", "Famille"),
            ("autre", "Autre"),
        ],
        string="Type de chambre",
        required=True,
        tracking=True,
    )

    number_of_rooms = fields.Integer(
        string="Nombre de chambres",
        default=1,
        required=True,
    )

    room_number = fields.Char(
        string=" N° de chamber",
    )
    room_view = fields.Many2one("room.view" , string=" vue de chamber")
    # -------------------------------
    number_of_nights = fields.Integer(
        string="Nombre de nuits",
        compute="_compute_number_of_nights",
        store=True,
    )
    board_type = fields.Selection[("petit_dejeuner","Petit Dejeuner")
                                  ("demi_pension","Demi Pension")
                                  ("pension_complete","Pension Complete")]

    # =========================================================
    # FLIGHT
    # =========================================================

    flight_type = fields.Selection(
        [
            ("aller_retour", "Aller / Retour"),
            ("aller_simple", "Aller simple"),
            ("multi_destination", "Multi destination"),
        ],
        string="Type de vol",
        tracking=True,
    )

    flight_class = fields.Selection(
        [
            ("indifferent", "Indifferent"),
            ("economique", "Economique"),
            ("premium", "Premium"),
            ("affaires", "Affaires"),
            ("premiere", "Premiere"),
        ],
        string="Class de vol",
        default="indifferent",
        tracking=True,
    )

    with_baggage = fields.Boolean(
        string="avec bagage",
        default=False,
    )

    direct_flight = fields.Boolean(
        string="vol Direct ",
        default=False,
    )

    flexibility_id = fields.Many2one(
        "travel.flight.flexibility",
        string="Flexibility",
    )
    # -------------------------------


     # -------------------------------
    _sql_constraints = [
        ("name_uniq", "unique(name, company_id)", "Cette reference existe deja."),
    ]

    # ------------------------------------------------------------------
    # Calculs
    # ------------------------------------------------------------------

    @api.depends("date_departure", "date_return")
    def _compute_number_of_nights(self):
        for record in self:
            if record.date_departure and record.date_return:
                delta = record.date_departure - record.date_return
                record.number_of_nights = max(delta.days, 0)
            else:
                record.number_of_nights = 0

    @api.depends("service_ids.sale_subtotal", "service_ids.cost_company")
    def _compute_amounts(self):
        for rec in self:
            sale = sum(rec.service_ids.mapped("sale_subtotal"))
            cost = sum(rec.service_ids.mapped("cost_company"))
            discount = rec.discount
            rec.amount_sale = sale
            rec.amount_cost = cost
            rec.total_discount = rec.amount_sale - discount
            rec.margin = sale - cost
            rec.margin_rate = (rec.margin / sale * 100.0) if sale else 0.0

    @api.depends(
        "passenger_ids",
        "document_ids.state",
        "passenger_ids.passport_state",
    )
    def _compute_counts(self):
        for rec in self:
            rec.passenger_count = len(rec.passenger_ids)
            rec.sale_order_count = len(rec.sale_order_ids)
            rec.document_missing_count = len(
                rec.document_ids.filtered(lambda d: d.state == "missing")
            )

    @api.depends("service_ids.cancellation_deadline")
    def _compute_next_deadline(self):
        for rec in self:
            dates = [
                s.cancellation_deadline
                for s in rec.service_ids
                if s.cancellation_deadline
            ]
            rec.next_deadline = min(dates) if dates else False

    def _compute_is_upcoming(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.is_upcoming = bool(rec.date_departure and rec.date_departure >= today)

    def _search_upcoming(self, operator, value):
        today = fields.Date.context_today(self)
        if operator == '=' and value:
            return [('date_departure', '>=', today)]
        return []

    def _compute_is_deadline_soon(self):
        today = fields.Date.context_today(self)
        limit = today + relativedelta(days=7)
        for rec in self:
            rec.is_deadline_soon = bool(rec.next_deadline and today <= rec.next_deadline <= limit)

    def _search_deadline_soon(self, operator, value):
        today = fields.Date.context_today(self)
        limit = today + relativedelta(days=7)
        if operator == '=' and value:
            return [('next_deadline', '!=', False), ('next_deadline', '<=', limit)]
        return []

    # ------------------------------------------------------------------
    # Creation et duplication
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/" and not vals.get("is_template"):
                vals["name"] = self.env["ir.sequence"].next_by_code("travel.file") or "/"
            elif vals.get("is_template") and vals.get("name", "/") == "/":
                vals["name"] = _("MODELE")
        return super().create(vals_list)

    def copy_data(self, default=None):
        """A la duplication : nouveau numero, etat brouillon, references videes."""
        vals_list = super().copy_data(default=default)
        default = default or {}
        for vals in vals_list:
            vals.setdefault("name", "/")
            vals.setdefault("date_open", fields.Date.context_today(self))
            if "is_template" not in default:
                vals["is_template"] = False
        return vals_list

    def action_create_from_template(self):
        """Cree un nouveau dossier a partir de ce modele."""
        self.ensure_one()
        if not self.is_template:
            raise UserError(_("Ce dossier n'est pas un modele."))
        new_file = self.copy({"is_template": False, "template_name": False})
        return {
            "type": "ir.actions.act_window",
            "name": _("Nouveau dossier"),
            "res_model": "travel.file",
            "res_id": new_file.id,
            "view_mode": "form",
        }

    # ------------------------------------------------------------------
    # Outils de saisie
    # ------------------------------------------------------------------
    def action_apply_target_margin(self):
        """Recalcule le prix de vente de toutes les prestations."""
        for rec in self:
            if not rec.target_margin_rate:
                raise UserError(_("Renseignez d'abord la marge cible du dossier."))
            lines = rec.service_ids.filtered(lambda s: s.cost_amount)
            lines.write({"markup_rate": rec.target_margin_rate})
            lines._apply_markup()

    def action_qty_from_passengers(self):
        """Aligne la quantite des prestations par personne sur le nb de passagers."""
        for rec in self:
            nb = len(rec.passenger_ids)
            if not nb:
                raise UserError(_("Ce dossier ne contient aucun passager."))
            rec.service_ids.filtered(
                lambda s: s.service_type in PER_PAX_TYPES
            ).write({"quantity": nb})

    def action_generate_documents(self):
        """Cree la liste des documents a fournir pour ce dossier."""
        Doc = self.env["travel.document"]
        Type = self.env["travel.document.type"]
        for rec in self:
            types = Type.search([])
            for dtype in types:
                if dtype.file_types:
                    codes = [c.strip() for c in dtype.file_types.split(",")]
                    if rec.file_type not in codes:
                        continue
                if dtype.per_passenger:
                    for pax in rec.passenger_ids:
                        exists = rec.document_ids.filtered(
                            lambda d: d.type_id == dtype and d.passenger_id == pax
                        )
                        if not exists:
                            Doc.create({
                                "file_id": rec.id,
                                "type_id": dtype.id,
                                "name": "%s - %s" % (dtype.name, pax.name),
                                "passenger_id": pax.id,
                                "sequence": dtype.sequence,
                            })
                else:
                    exists = rec.document_ids.filtered(lambda d: d.type_id == dtype)
                    if not exists:
                        Doc.create({
                            "file_id": rec.id,
                            "type_id": dtype.id,
                            "name": dtype.name,
                            "sequence": dtype.sequence,
                        })

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------
    def _prepare_analytic_account(self):
        self.ensure_one()
        plan = self.env.ref("benamor_travel.analytic_plan_travel", raise_if_not_found=False)
        if not plan:
            plan = self.env["account.analytic.plan"].search([], limit=1)
        return {
            "name": self.name,
            "partner_id": self.partner_id.id,
            "plan_id": plan.id,
            "company_id": self.company_id.id,
        }

    def action_option(self):
        self.write({"state": "option"})

    def _create_invoice(self):
        self.ensure_one()

        if self.invoice_id:
            return self.invoice_id

        invoice_lines = []

        for service in self.service_ids:
            if not service.product_id:
                raise UserError(
                    _("La prestation %s n'a pas de produit.")
                    % service.name
                )

            invoice_lines.append(
                (
                    0,
                    0,
                    {
                        "product_id": service.product_id.id,
                        "name": service.description or service.name,
                        "quantity": service.quantity,
                        "price_unit": service.sale_price,
                        "discount": service.discount,
                        "account_id": (
                                service.product_id.property_account_income_id.id
                                or service.product_id.categ_id.property_account_income_categ_id.id
                        ),
                    },
                )
            )

        if not invoice_lines:
            raise UserError(
                _("Impossible de créer une facture sans lignes.")
            )

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_id.id,
                "invoice_date": fields.Date.context_today(self),
                "currency_id": self.currency_id.id,
                "travel_file_id": self.id,
                "invoice_line_ids": invoice_lines,
            }
        )

        self.invoice_id = invoice.id

        return invoice

    def action_confirm(self):
        for rec in self:
            if rec.is_template:
                raise UserError(_("Un modele ne peut pas etre confirme."))
            if not rec.partner_id:
                raise UserError(_("Renseignez le client avant de confirmer."))
            if not rec.service_ids:
                raise UserError(_("Ajoutez au moins une prestation avant de confirmer."))
            if not rec.analytic_account_id:
                rec.analytic_account_id = self.env["account.analytic.account"].create(
                    rec._prepare_analytic_account()
                )
            rec.state = "confirmed"
            rec.action_generate_documents()
            # Création de la facture
            rec._create_invoice()

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_draft(self):
        self.write({"state": "draft"})

    def action_create_sale_order(self):
        self.ensure_one()
        if self.state == "draft":
            raise UserError(_("Confirmez le dossier avant de generer la commande."))
        lines = []
        for srv in self.service_ids.filtered(lambda s: not s.excluded_from_invoice):
            if not srv.product_id:
                raise UserError(
                    _("La prestation '%s' n'a pas d'article defini.") % srv.description
                )
                
            # Enrichissement de la description pour la facture client
            desc = srv.description or srv.product_id.name
            details = []
            if srv.date_start or srv.date_end:
                d_start = srv.date_start.strftime('%d/%m/%Y') if srv.date_start else ""
                d_end = srv.date_end.strftime('%d/%m/%Y') if srv.date_end else ""
                if d_start and d_end:
                    details.append(f"Du {d_start} au {d_end}")
                elif d_start:
                    details.append(f"Le {d_start}")
                    
            if srv.pnr:
                details.append(f"PNR: {srv.pnr}")
            if getattr(srv, 'hotel_id', False) and srv.hotel_id:
                details.append(f"Hôtel: {srv.hotel_id.name}")
            if srv.passenger_ids:
                pax = ", ".join(srv.passenger_ids.mapped('name'))
                details.append(f"Passagers: {pax}")
                
            if details:
                desc = f"{desc}\n" + "\n".join(details)

            lines.append((0, 0, {
                "product_id": srv.product_id.id,
                "name": desc,
                "product_uom_qty": srv.quantity,
                "price_unit": srv.sale_price_unit,
            }))
        if not lines:
            raise UserError(_("Aucune prestation facturable."))
        order = self.env["sale.order"].create({
            "partner_id": self.partner_id.id,
            "travel_file_id": self.id,
            "origin": self.name,
        })
        order.order_line = lines
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": order.id,
            "view_mode": "form",
        }

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Commandes"),
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("travel_file_id", "=", self.id)],
            "context": {"default_travel_file_id": self.id,
                        "default_partner_id": self.partner_id.id},
        }

    # ------------------------------------------------------------------
    # Alertes automatiques (planificateur)
    # ------------------------------------------------------------------
    @api.model
    def _cron_travel_alerts(self, days_before=5):
        """Cree une activite quand une limite d'annulation approche."""
        today = fields.Date.context_today(self)
        limit = today + relativedelta(days=days_before)
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        model_id = self.env["ir.model"]._get("travel.file").id
        files = self.search([
            ("state", "in", ("option", "confirmed")),
            ("is_template", "=", False),
            ("next_deadline", "!=", False),
            ("next_deadline", ">=", today),
            ("next_deadline", "<=", limit),
        ])
        for rec in files:
            existing = self.env["mail.activity"].search_count([
                ("res_model_id", "=", model_id),
                ("res_id", "=", rec.id),
                ("summary", "like", "Limite d'annulation"),
            ])
            if existing:
                continue
            self.env["mail.activity"].create({
                "res_model_id": model_id,
                "res_id": rec.id,
                "activity_type_id": activity_type.id if activity_type else False,
                "summary": _("Limite d'annulation le %s") % rec.next_deadline,
                "note": _("Confirmer ou annuler avant cette date pour eviter "
                          "des frais fournisseur."),
                "date_deadline": rec.next_deadline,
                "user_id": rec.user_id.id or self.env.uid,
            })
        return True
