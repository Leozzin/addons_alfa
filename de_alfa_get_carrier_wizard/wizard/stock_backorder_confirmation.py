from odoo import fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    def compute_carrier_id(self):
        records=self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        for i in records:
            if i.carrier_id:
                return i.carrier_id.id

        return False

    carrier_id = fields.Many2one('delivery.carrier', 'Carrier', default=compute_carrier_id)
    
    def process(self):
        if self.carrier_id:
            self.pick_ids.write({"carrier_id": self.carrier_id.id})
        super().process()
        attachment_ids = self.env['ir.attachment'].search(
            [('res_id', 'in', self.pick_ids.ids), ('res_model', '=', 'stock.picking')])

        return attachment_ids.action_download_attachment()