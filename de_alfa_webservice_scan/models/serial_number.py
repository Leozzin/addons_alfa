from odoo import api, fields, models

class SerialNumber(models.Model):
    _inherit = 'stock.move.line'

    serial_number = fields.Char(string="Serial Number")