from odoo import fields, models


class TravelDestination(models.Model):
    _name = "travel.destination"
    _description = "Destination"
    _order = "name"

    name = fields.Char(required=True)
    country_id = fields.Many2one("res.country", string="Pays")
    city = fields.Char(string="Ville")
    active = fields.Boolean(default=True)


class TravelAirline(models.Model):
    _name = "travel.airline"
    _description = "Compagnie aerienne"
    _order = "name"

    name = fields.Char(required=True)
    iata_code = fields.Char(string="Code IATA", size=3)
    partner_id = fields.Many2one("res.partner", string="Fournisseur lie")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("iata_uniq", "unique(iata_code)", "Ce code IATA existe deja."),
    ]


class TravelHotel(models.Model):
    _name = "travel.hotel"
    _description = "Hotel"
    _order = "name"

    name = fields.Char(required=True)
    destination_id = fields.Many2one("travel.destination", string="Destination")
    category = fields.Selection(
        [("2", "2*"), ("3", "3*"), ("4", "4*"), ("5", "5*")], string="Categorie"
    )
    partner_id = fields.Many2one("res.partner", string="Fournisseur lie")
    address = fields.Char(string="Adresse")
    active = fields.Boolean(default=True)
