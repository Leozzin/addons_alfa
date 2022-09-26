# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

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
        # print("hello pick")
        # print(self.pick_ids[0])
        super().process()
        attachment_ids = self.env['ir.attachment'].search(
            [('res_id', 'in', self.pick_ids.ids), ('res_model', '=', 'stock.picking')])


        return attachment_ids.action_download_attachment()

        # return super().process()




