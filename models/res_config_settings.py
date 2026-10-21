from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    api_key = fields.Char(
        string="Google API Key",
        config_parameter="benamor_travel.api_key",
        groups="base.group_system",
    )