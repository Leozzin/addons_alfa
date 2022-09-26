# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.tools import float_is_zero




class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _check_immediate(self):
        immediate_pickings = self.browse()
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for picking in self:
            if all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel'))):
                immediate_pickings |= picking
            elif not picking.carrier_id:
                immediate_pickings |= picking


        return immediate_pickings