# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.move"

    tracking_ws=fields.Char(related='sale_line_id.tracking')
    custom_carrier=fields.Char(related='sale_line_id.custom_carrier')
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    tracking_ws=fields.Char(related='move_id.tracking_ws')
    custom_carrier = fields.Char(related='move_id.custom_carrier')