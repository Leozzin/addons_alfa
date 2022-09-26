# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    @api.model
    def _print_document(self, label, printer):
        """ Print a label, do not return the document file """
        if not printer:
            log_message = (_("No direct printer defined! Please check the "
                    "configuration of your delivery method."))
            self.message_post(body=log_message)
            return False
        return printer.print_document(self, label,
            doc_format='pdf', action='server', tray='Main')

    def select_relaypoint(self, pickings):
        """Call the method to select relay points of the selected carrier"""
        self.ensure_one()
        _logger.debug('select_relaypoint: %s' % pickings)
        if hasattr(self, '%s_select_relaypoint' % self.delivery_type):
            return getattr(
                self, '%s_select_relaypoint' % self.delivery_type)(pickings)
