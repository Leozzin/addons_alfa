# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    status_code=fields.Char('Code')
    last_pack=fields.Char("Last pack")
    pdf_label=fields.Text('PDF')

    def create_one_pack(self):
        self.ensure_one()
        package = self.env['stock.quant.package'].create({})
        self.last_pack=package.name
