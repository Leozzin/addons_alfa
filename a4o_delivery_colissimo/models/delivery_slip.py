# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DeliverySlip(models.Model):
    _inherit = "delivery.slip"

    delivery_type = fields.Selection(
        selection_add=[('colissimo', "Colissimo")], ondelete={'colissimo': 'set default'})
