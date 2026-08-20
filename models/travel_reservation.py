from dateutil.relativedelta import relativedelta

from odoo import fields, models


class TravelFlightFlexibility(models.Model):
    _name = "travel.flight.flexibility"
    _description = "Travel Flight Flexibility"
    name = fields.Char(string="Nom", required=True)

class TravelRoom(models.Model):
    _name = "room.view"
    _description = "Room View"
    name = fields.Char(string="Nom", required=True)

class TravelFacilitate(models.Model):
    _name = "travel.facilitate"
    _description = "Travel Facilitate"
    name = fields.Char(string="Nom", required=True)

class TravelPhoto(models.Model):
    _name = "travel.photo"
    _description = "Photo"
    _order = " id"
    _rec_name = "image"

    product_id = fields.Many2one(
        "product.template",
        string="product",
        required=True,
        ondelete="cascade",
    )

    image = fields.Image(
        string="Photo",
        required=True,
        max_width=1920,
        max_height=1920,
    )

class TravelFacility(models.Model):
    _name = "travel.facility"
    _description = "Hotel Service and Facility"
    _order = "id"

    hotel_id = fields.Many2one(
        "travel.hotel",
        string="Hotel",
        required=True,
        ondelete="cascade",
    )

    name = fields.Char(
        string="Service / Équipement",
        required=True,
    )

    icon = fields.Char(
        string="Icône",
        help="Nom de l'icône Font Awesome, par exemple fa-wifi.",
    )

