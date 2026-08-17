# -*- coding: utf-8 -*-
from odoo import models, fields

class TravelDossier(models.Model):
    _name = 'travel.dossier'
    _description = 'Dossier de Voyage'

    name = fields.Char(string='Référence Dossier', required=True, copy=False, index=True)
    description = fields.Char(string='Description / Destination')
