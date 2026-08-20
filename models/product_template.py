from odoo import _, api, fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    latitude = fields.Float(
        string="Latitude",
        digits=(10, 7),
    )

    longitude = fields.Float(
        string="Longitude",
        digits=(10, 7),
    )

    map_url = fields.Char(
        string="Google Maps",
        compute="_compute_map_url",
    )

    photo_ids = fields.One2many(
        "travel.photo",
        "product_id",
        string="Photos",
    )
    equipment_ids = fields.Many2many(
    "travel.hotel.facility",
    "product_facility_rel",
    "product_tmpl_id",
    "facility_id",
    string="Services & équipements",
)
    @api.depends(
        "latitude",
        "longitude",
    )
    def _compute_map_url(self):
        for product in self:
            if (
                product.latitude
                and product.longitude
            ):
                product.travel_map_url = (
                    "https://www.google.com/maps?q=%s,%s"
                    % (
                        product.latitude,
                        product.longitude,
                    )
                )
            else:
                product.map_url = False