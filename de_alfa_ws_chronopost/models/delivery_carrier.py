# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, api, fields, models

from .chrono_request import ChronoRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("chrono_alfa", "Chronoalfa")], ondelete={'chrono_alfa': 'set default'})
    chrono_alfa_ws_uid = fields.Char(string="WS uid")





    def chrono_alfa_rate_shipment(self, order):
        raise NotImplementedError(
            _("""Chrono ALFA SOIP API does not allow you to rate.""")
        )

    def _chrono_alfa_get_response_price(self, response, currency, company):
        raise NotImplementedError(
            _("""Chrono ALFA SOIP API does not allow you to get rate.""")
        )

    def _chrono_alfa_action_label(self, picking,label):
        return self.env["ir.attachment"].create(
                    {
                        "name": "TNT-%s.pdf" % picking.name,
                        "type": "binary",
                        "datas": base64.b64encode(label),
                        "res_model": picking._name,
                        "res_id": picking.id,
                    }
                )

    def chrono_alfa_send_shipping(self, pickings):
        return [self.chrono_alfa_create_shipping(p) for p in pickings]

    def chrono_alfa_create_shipping(self, picking):
        self.ensure_one()
        chrono_request = ChronoRequest(self, picking)
        #chrono_request._send_shipping()
        # tnt_request._get_label_info()
        # self._tnt_alfa_action_label(picking)
        return {
            "exact_price": 0,
            "tracking_number": picking.carrier_tracking_ref,
        }

    def chrono_alfa_tracking_state_update(self, picking):
        self.ensure_one()
        if picking.carrier_tracking_ref:
            chrono_request = ChronoRequest(self, picking)
            response = chrono_request.tracking_state_update()
            picking.delivery_state = response["delivery_state"]
            picking.status_code=response["status_code"]
            picking.tracking_state_history = response["tracking_state_history"]

    def chrono_alfa_cancel_shipment(self, pickings):
        raise NotImplementedError(
            _("""TNT API does not allow you to cancel a shipment.""")
        )

    def chrono_alfa_get_tracking_link(self, picking):
        return "%s/%s=%s" % (
            "https://www.chronopost.fr/",
            "tracking-no-cms/suivi-page?listeNumerosLT",
            picking.carrier_tracking_ref,
        )

