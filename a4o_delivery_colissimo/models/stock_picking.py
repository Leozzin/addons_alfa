# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, _
from odoo.exceptions import UserError
from .colissimo_request import PRODUCT_CODES
import logging

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def colissimo_compute_mandatory_weight(self):
        return True


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def colissimo_get_delivery_relaypoint(self):
        if self.carrier_id.coli_service_type == 'relaypoint':
            return True
        return False

    def _get_zone(self, country_id):
        '''returns the zone (among 'oversea', 'europe', 'international')
        according to the country of destination.'''
        Countries = self.env["res.country.group"]
        countries = Countries.search([('name', '=', 'DOM-TOM')], limit=1)
        if country_id.id in countries.country_ids.ids:
            return 'oversea'
        countries = Countries.search([('name', '=', 'Europe')], limit=1)
        if country_id.id in countries.country_ids.ids:
            return 'europe'
        return 'international'

    def colissimo_get_product_code(self):
        service = False
        zone = 'france'
        if (self.partner_id.country_id
                and self.partner_id.country_id.code != 'FR'):
            zone = self._get_zone(self.partner_id.country_id)

        service = False
        if zone == 'international':
            service = PRODUCT_CODES[zone][0]
        elif zone in ['oversea', 'france', 'europe']:
            service = PRODUCT_CODES[zone][self.carrier_id.coli_service_type]
            if self.carrier_id.coli_service_type == 'relaypoint':
                if self.partner_id.point_type in service:
                    service = self.partner_id.point_type
                else:
                    raise UserError(
                        _("The point type (%s) of the destination address is "
                          "not in the list of point type defined (%s) !") % (
                              self.partner_id.point_type, ', '.join(service)))
                if (service == 'PCS'
                        and (zone == 'france'
                            or self.partner_id.country_id.code == 'BE')):
                    country = self.partner_id.country_id.code or 'FR'
                    raise UserError(
                        _("You cannot select a Consigne Pickup Station in "
                            "this country (%s)") % (country))
            else:
                service = service[0]
        if not service:
            raise UserError(
                _('Unable to determine a service (product code) !!!'))
        return service

    @api.depends('partner_id', 'original_partner_id')
    def colissimo_get_names(self, partner_id, original_id=None):
        names = {'lastname': '.', 'firstname': '.', 'company': partner_id.name}

        def set_names(data):
            first, last = data.name.split(' ', 1)
            return {'firstname': first, 'lastname': last}

        if partner_id.code_relaypoint:
            if original_id:
                if ' ' in original_id.name and original_id.is_company == False:
                    names.update(set_names(original_id))
                else:
                    names.update({'lastname': original_id.name})
            elif partner_id.parent_id:
                names.update(set_names(partner_id.parent_id))
        else:
            if ' ' in partner_id.name and partner_id.is_company == False:
                names.update(set_names(partner_id))
                names.update({
                    'company': self.partner_id.parent_id
                        and self.partner_id.parent_id.name
                        or '',
                    })
        return names

    @api.depends('move_line_ids')
    def colissimo_get_invoices(self):
        account_invoice_lines = self.move_line_ids \
            .filtered(lambda r: r.result_package_id) \
            .mapped('move_id') \
            .mapped('sale_line_id') \
            .mapped('invoice_lines')
        return set([il.move_id for il in account_invoice_lines])
        
