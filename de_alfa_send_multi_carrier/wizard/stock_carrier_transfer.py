# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockCarrierTransfer(models.TransientModel):
    _name = "stock.carrier.transfer"

    def compute_package(self):
        record = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        num = 0
        for r in record:
            if r.package_ids:
                num = num + len(record.package_ids)
            else:
                num = num + 1

    pick_ids = fields.Many2many('stock.picking')

    carrier_id = fields.Many2one('delivery.carrier', 'Carrier')


    number_of_packages = fields.Integer(readonly=1,
        help="Set the number of packages for this picking(s)",
    )

    def test_fun(self):

        return {'type': 'ir.actions.act_window_close'}
    def apply(self):
        if self.carrier_id:
            print ("hello apply")
            if self.env.context.get('active_ids'):
                print (self.env.context.get('active_ids'))
                pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
                pickings.write({"carrier_id": self.carrier_id.id})
                self.carrier_id.send_shipping(pickings)
                pickings.tracking_send()
                return (self.env['stock.picking'].action_all_picking(pickings))


