from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class TravelDashboard(models.TransientModel):
    _name = "travel.dashboard"
    _description = "Tableau de bord agence"

    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    # --- Activite ---
    file_open_count = fields.Integer(
        string="Dossiers en cours", compute="_compute_kpi"
    )
    file_option_count = fields.Integer(
        string="Dossiers en option", compute="_compute_kpi"
    )
    departure_week_count = fields.Integer(
        string="Départs sous 7 jours", compute="_compute_kpi"
    )
    departure_month_count = fields.Integer(
        string="Départs ce mois", compute="_compute_kpi"
    )

    # --- Finance du mois en cours ---
    month_sale = fields.Monetary(
        string="Ventes du mois", compute="_compute_kpi", currency_field="currency_id"
    )
    month_cost = fields.Monetary(
        string="Couts du mois", compute="_compute_kpi", currency_field="currency_id"
    )
    month_margin = fields.Monetary(
        string="Marge du mois", compute="_compute_kpi", currency_field="currency_id"
    )
    month_margin_rate = fields.Float(
        string="Taux de marge", compute="_compute_kpi"
    )
    year_sale = fields.Monetary(
        string="Ventes de l'annee", compute="_compute_kpi", currency_field="currency_id"
    )
    year_margin = fields.Monetary(
        string="Marge de l'annee", compute="_compute_kpi", currency_field="currency_id"
    )

    # --- Alertes ---
    passport_alert_count = fields.Integer(
        string="Passeports à contrôler", compute="_compute_kpi"
    )
    payment_late_count = fields.Integer(
        string="Echeances en retard", compute="_compute_kpi"
    )
    payment_late_amount = fields.Monetary(
        string="Montant en retard", compute="_compute_kpi", currency_field="currency_id"
    )
    payment_todo_amount = fields.Monetary(
        string="Reste a encaisser", compute="_compute_kpi", currency_field="currency_id"
    )

    current_month_passenger_count = fields.Integer(
        string="Voyageurs du Mois", compute="_compute_kpi"
    )
    upcoming_departure_ids = fields.Many2many(
        "travel.file", relation="dash_upcoming_rel", string="Prochains Départs", compute="_compute_kpi"
    )
    option_file_ids = fields.Many2many(
        "travel.file", relation="dash_option_rel", string="Dossiers à relancer", compute="_compute_kpi"
    )

    @api.depends("create_date")
    def _compute_kpi(self):
        File = self.env["travel.file"]
        Passenger = self.env["travel.passenger"]
        Plan = self.env["travel.payment.plan"]
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        week_end = today + relativedelta(days=7)
        month_end = month_start + relativedelta(months=1)

        active_states = ("draft", "option", "confirmed")

        for rec in self:
            rec.file_open_count = File.search_count(
                [("state", "in", active_states)]
            )
            rec.file_option_count = File.search_count([("state", "=", "option")])
            rec.departure_week_count = File.search_count(
                [
                    ("state", "=", "confirmed"),
                    ("date_departure", ">=", today),
                    ("date_departure", "<=", week_end),
                ]
            )
            rec.departure_month_count = File.search_count(
                [
                    ("state", "=", "confirmed"),
                    ("date_departure", ">=", month_start),
                    ("date_departure", "<", month_end),
                ]
            )

            month_files = File.search(
                [
                    ("state", "in", ("confirmed", "done")),
                    ("date_open", ">=", month_start),
                    ("date_open", "<", month_end),
                ]
            )
            rec.month_sale = sum(month_files.mapped("amount_sale"))
            rec.month_cost = sum(month_files.mapped("amount_cost"))
            rec.month_margin = rec.month_sale - rec.month_cost
            rec.month_margin_rate = (
                rec.month_margin / rec.month_sale * 100.0 if rec.month_sale else 0.0
            )

            year_files = File.search(
                [
                    ("state", "in", ("confirmed", "done")),
                    ("date_open", ">=", year_start),
                ]
            )
            rec.year_sale = sum(year_files.mapped("amount_sale"))
            rec.year_margin = sum(year_files.mapped("margin"))

            rec.passport_alert_count = Passenger.search_count(
                [
                    ("passport_state", "in", ("expired", "warning", "missing")),
                    ("file_id.state", "in", ("option", "confirmed")),
                ]
            )

            late_plans = Plan.search(
                [("state", "=", "todo"), ("date_due", "<", today)]
            )
            rec.payment_late_count = len(late_plans)
            rec.payment_late_amount = sum(late_plans.mapped("amount"))
            rec.payment_todo_amount = sum(
                Plan.search([("state", "=", "todo")]).mapped("amount")
            )
            
            # Nouveau Cockpit
            rec.current_month_passenger_count = Passenger.search_count([
                ("file_id.state", "in", ("confirmed", "done")),
                ("file_id.date_departure", ">=", month_start),
                ("file_id.date_departure", "<", month_end),
            ])
            rec.upcoming_departure_ids = [(6, 0, File.search([
                ("state", "=", "confirmed"),
                ("date_departure", ">=", today),
                ("date_departure", "<=", today + relativedelta(days=30))
            ], order="date_departure asc", limit=15).ids)]
            rec.option_file_ids = [(6, 0, File.search([
                ("state", "=", "option")
            ], order="date_open desc", limit=10).ids)]

    # ------------------------------------------------------------------
    # Boutons : Actions rapides
    # ------------------------------------------------------------------
    def action_new_file(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Nouveau Dossier",
            "res_model": "travel.file",
            "view_mode": "form",
            "target": "current",
        }

    def action_new_partner(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Nouveau Client",
            "res_model": "res.partner",
            "view_mode": "form",
            "target": "current",
        }

    def action_new_service(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Nouveau Service",
            "res_model": "travel.service",
            "view_mode": "form",
            "target": "current",
        }

    # ------------------------------------------------------------------
    # Boutons : ouverture des listes filtrees
    # ------------------------------------------------------------------
    def _open(self, name, model, domain, view_mode="list,form"):
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": view_mode,
            "domain": domain,
            "target": "current",
        }

    def action_open_files(self):
        return self._open(
            "Dossiers en cours",
            "travel.file",
            [("state", "in", ("draft", "option", "confirmed"))],
        )

    def action_open_options(self):
        return self._open(
            "Dossiers en option", "travel.file", [("state", "=", "option")]
        )

    def action_open_departures_week(self):
        today = fields.Date.context_today(self)
        return self._open(
            "Departs sous 7 jours",
            "travel.file",
            [
                ("state", "=", "confirmed"),
                ("date_departure", ">=", today),
                ("date_departure", "<=", today + relativedelta(days=7)),
            ],
        )

    def action_open_passport_alerts(self):
        return self._open(
            "Passeports à contrôler",
            "travel.passenger",
            [
                ("passport_state", "in", ("expired", "warning", "missing")),
                ("file_id.state", "in", ("option", "confirmed")),
            ],
        )

    def action_open_late_payments(self):
        return self._open(
            "Echeances en retard",
            "travel.payment.plan",
            [("state", "=", "todo"), ("date_due", "<", fields.Date.context_today(self))],
        )

    def action_open_margin_analysis(self):
        return self._open(
            "Analyse des marges",
            "travel.file",
            [("state", "not in", ("draft", "cancel"))],
            view_mode="pivot,graph,list",
        )
