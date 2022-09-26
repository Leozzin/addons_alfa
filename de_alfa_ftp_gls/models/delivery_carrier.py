# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, api, fields, models

from .gls_request import GlsRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("gls_alfa", "GLS (With FTP)")], ondelete={'gls_alfa': 'set default'})
    gls_alfa_host = fields.Char(string="FTP host")
    gls_alfa_user=fields.Char(string="FTP user")
    gls_alfa_password = fields.Char(string="FTP Password")


    def gls_alfa_rate_shipment(self, order):
        res = {
            'success': False,
            'price': 0.0,
            'warning_message': _("Don't forget to check the price!"),
            'error_message': None,
        }
        vals = self.base_on_rule_rate_shipment(order)
        if vals.get('success'):
            price = vals['price']
            res.update({
                'success': True,
                'price': price,
            })
        return res



    def _gls_alfa_get_response_price(self, response, currency, company):
        raise NotImplementedError(
            _("""GLS ALFA SOIP API does not allow you to get rate.""")
        )

    def _gls_alfa_action_label(self, picking,label):
        raise NotImplementedError(
            _("""GLS ALFA SOIP API does not allow you to get rate.""")
        )
        return self.env["ir.attachment"].create(
                    {
                        "name": "TNT-%s.pdf" % picking.name,
                        "type": "binary",
                        "datas": base64.b64encode(label),
                        "res_model": picking._name,
                        "res_id": picking.id,
                    }
                )

    def gls_alfa_send_shipping(self, pickings):
        return [self.gls_alfa_create_shipping(p) for p in pickings]

    def gls_alfa_create_shipping(self, picking):
        self.ensure_one()
        gls_request = GlsRequest(self, picking)
        if not picking.delivery_state:
            gls_request._send_shipping()

        return {
            "exact_price": 0,
            "tracking_number": picking.carrier_tracking_ref,
        }
     

    def gls_alfa_tracking_state_update(self, picking):
        self.ensure_one()
        if picking.carrier_tracking_ref:
            gls_request = GlsRequest(self, picking)
            response = gls_request.tracking_state_update()
            """picking.delivery_state = response["delivery_state"]
            picking.status_code=response["status_code"]
            picking.tracking_state_history = response["tracking_state_history"]"""

    def gls_alfa_cancel_shipment(self, pickings):
        raise NotImplementedError(
            _("""GLS API does not allow you to cancel a shipment.""")
        )

    def gls_alfa_get_tracking_link(self, picking):
        return "%s=%s" % (
            "https://gls-group.eu/FR/fr/suivi-colis?match",
            picking.carrier_tracking_ref,
        )

