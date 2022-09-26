from odoo import _, api, fields, models



class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    domain=fields.Char()



