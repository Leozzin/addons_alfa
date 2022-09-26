# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(selection_add=[("tnt_alfa", "TNT")])

class stock_quant_package(models.Model):
    _inherit = "stock.quant.package"
    carrier_tracking_ref = fields.Char(string='Tracking Reference', copy=False)
    carrier_tracking_url = fields.Char(string='Tracking URL')
    status_code = fields.Char('Code')
    delivery_state = fields.Selection([
            ("shipping_recorded_in_carrier", "Shipping recorded in carrier"),
            ("in_transit", "In transit"),
            ("canceled_shipment", "Canceled shipment"),
            ("incidence", "Incidence"),
            ("customer_delivered", "Customer delivered"),
            ("warehouse_delivered", "Warehouse delivered"),
        ])

