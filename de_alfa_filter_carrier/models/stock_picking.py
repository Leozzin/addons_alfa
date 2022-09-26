from odoo import _, api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    def correction_weight(self):
        for record in self.env['stock.picking'].search([]):
            record._cal_weight()


    @api.depends('move_lines','move_line_ids.product_id','move_line_ids.product_id.weight','move_line_ids.product_uom_qty')
    def _cal_weight(self):
        for picking in self:
            picking.weight = sum([(p.product_uom_qty * p.product_id.weight) for p in picking.move_line_ids])

