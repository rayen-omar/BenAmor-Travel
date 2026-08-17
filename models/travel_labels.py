"""Personnalisation du vocabulaire natif pour le metier agence de voyage.

Ce fichier ne modifie AUCUN comportement : il ne change que les libelles
affiches. Les noms techniques des champs restent inchanges, donc la
compatibilite avec les autres modules et les migrations est preservee.

Pour revenir au vocabulaire Odoo standard, il suffit de retirer ce fichier
de models/__init__.py et de mettre le module a jour.
"""

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_line = fields.One2many(string="Prestations")
    client_order_ref = fields.Char(string="Reference client")
    validity_date = fields.Date(string="Option valable jusqu'au")
    commitment_date = fields.Datetime(string="Date de depart prevue")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_id = fields.Many2one(string="Prestation")
    name = fields.Text(string="Designation")
    product_uom_qty = fields.Float(string="Qte (pax / nuits)")
    price_unit = fields.Float(string="Prix unitaire")


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_line_ids = fields.One2many(string="Prestations")
    invoice_origin = fields.Char(string="Dossier d'origine")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_id = fields.Many2one(string="Prestation")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    order_line = fields.One2many(string="Prestations achetees")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_id = fields.Many2one(string="Prestation")
