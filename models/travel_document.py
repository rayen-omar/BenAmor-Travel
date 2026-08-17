from odoo import fields, models


class TravelDocumentType(models.Model):
    _name = "travel.document.type"
    _description = "Type de document a fournir"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    file_types = fields.Char(
        string="Types de dossier",
        help="Codes separes par des virgules (ticket, package, omra, visa, b2b, "
        "other). Laisser vide pour appliquer a tous les dossiers.",
    )
    per_passenger = fields.Boolean(
        string="Par passager",
        help="Coche si le document est demande a chaque passager.",
    )
    active = fields.Boolean(default=True)


class TravelDocument(models.Model):
    _name = "travel.document"
    _description = "Document du dossier"
    _order = "file_id, sequence, id"

    file_id = fields.Many2one(
        "travel.file", string="Dossier", required=True, ondelete="cascade", index=True
    )
    sequence = fields.Integer(default=10)
    type_id = fields.Many2one("travel.document.type", string="Type de document")
    name = fields.Char(string="Document", required=True)
    passenger_id = fields.Many2one("travel.passenger", string="Passager")
    state = fields.Selection(
        [
            ("todo", "A obtenir"),
            ("received", "Recu"),
            ("na", "Sans objet"),
        ],
        string="Etat",
        default="todo",
        required=True,
        copy=False,
    )
    date_received = fields.Date(string="Recu le", copy=False)
    note = fields.Char()
