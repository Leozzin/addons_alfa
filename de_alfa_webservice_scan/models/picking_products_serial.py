from odoo import api, fields, models

class PickingProductsSerials(models.Model):
    _name = "picking.products.serial"
    _description = "Picking Products Serials"

    picking_id = fields.Char(string="Picking ID", required=True)
    product_id = fields.Char(string="Product ID", required=True)
    product_name = fields.Char(string="Product Name")
    serial_number = fields.Char(string="Serial Number")