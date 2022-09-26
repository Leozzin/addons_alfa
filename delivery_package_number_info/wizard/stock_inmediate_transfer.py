# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    def compute_package(self):
        record=self.env['stock.picking'].browse(self.env.context.get('active_id'))

        num=1
        if record.package_ids:
            if len(record.package_ids)>1:
                num=len(record.package_ids)
        return num


    number_of_packages = fields.Integer(default=compute_package,readonly=1,
        help="Set the number of packages for this picking(s)",
    )


