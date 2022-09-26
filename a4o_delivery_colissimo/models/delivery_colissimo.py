# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from .colissimo_request import ColissimoRequest, LABEL_FORMAT
import re
import json
import logging

_logger = logging.getLogger(__name__)
           

class Module(models.Model):
    _inherit = "ir.module.module"

    def button_immediate_upgrade(self):
        super().button_immediate_upgrade()
        for module in list(self):
            if module.name == 'a4o_delivery_colissimo':
                return self._button_immediate_function(
                    type(self).button_upgrade)


class ProviderColissimo(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('colissimo', "Colissimo")], ondelete={'colissimo': 'set default'})
    coli_service_type = fields.Selection([
            ('relaypoint', 'Relay point'),
            ('wo_signature', 'Without signature'),
            ('signature', 'With signature'),
            ('eco', 'Eco (Only for Oversea)'),
            ], string='Service type', default='relaypoint',
        help="To select.")
    coli_country_origin_id = fields.Many2one('res.country',
        string='Default Country of Origin', ondelete='restrict',
        help="Country of origin of the product by default (if it is not "
            "indicated on the product)")
    coli_account_number = fields.Char(
        string='Account Number', groups="base.group_system", size=6,
        help="Colissimo contract number (the same is used for the production "
             "and the tests).")
    coli_passwd = fields.Char(
        string='Password', groups="base.group_system",
        help="Password to use for connection")
    coli_label_format = fields.Selection(
        LABEL_FORMAT, string="Label Colissimo Format",
        default='PDF_10x15_300dpi')
    coli_remove_label = fields.Boolean(
        'Remove the attached colissimo label', default=False,
        help="When canceling a shipment, remove the attached labels.")
    coli_shipping_url = fields.Char(
        string='Shipping URL (colissimo)', groups="base.group_system",
        help="WSDL url for shipping.")
    coli_relaypoint_url = fields.Char(
        string='Relay Point URL', groups="base.group_system",
        help="WSDL url for searching relay point.")
    coli_max_point = fields.Integer(
        string="Relay Points Max", default=5,
        help="Max number of relay points returned by the search request.")
    coli_distance_search = fields.Integer(
        string="Search distance", default=10,
        help="Maximum search distance of relay points in the request.")
    coli_customs_category = fields.Selection([
            ('1', 'Gift'),
            ('2', 'Commercial sample'),
            ('3', 'Commercial shipment'),
            ('4', 'Document'),
            ('5', 'Other'),
            ('6', 'Merchandise return'),
            ], string='Customs category', default='3',
        help="Nature of the shipment used in the CN23 declaration.")
    coli_insurance_level = fields.Selection([
            ('0.0', 'Without'),
            ('150.00', '150 EUR'),
            ('300.00', '300 EUR'),
            ('500.00', '500 EUR'),
            ('1000.00', '1000 EUR'),
            ('2000.00', '2000 EUR'),
            ('5000.00', '5000 EUR'),
            ], string='Default Level of Insurance', default=0,
        help="Default insurance level if the value of the shipment does not "
             "exceed the minimum value to be insured")
    coli_insurance_min_value = fields.Float('Minimum value to be insured',
        required=True, digits='Product Price', default=0.0)
    coli_direct_printing = fields.Boolean('Direct Printing', default=False,
        help="Directly print the label when the delivery is validate,"
             "if the module : base_report_to_printer is installed")
    coli_printer_name = fields.Char()
    coli_printer_id = fields.Many2one('printing.printer', string='Printer',
        compute='compute_printer_id',
        help="printer")

    @api.onchange('coli_direct_printing')
    def onchange_coli_direct_printing(self):
        result = {}
        try:
            printer = self.env['printing.printer']
        except KeyError:
            _logger.error('Please install and configure module :'
                          'base_report_to_printer')
            self.coli_direct_printing = False
            result['warning'] = {
                'title': _('Error!'),
                'message': _('Please install and configure module :'
                             'base_report_to_printer')
                }
            return result   

    @api.depends('coli_printer_name')
    def compute_printer_id(self):
        for record in self:
            record.coli_printer_id = False
            if record.coli_printer_name:
                record.coli_printer_id = int(
                    record.coli_printer_name.split(',')[1])

    def action_get_printer(self):
        context = dict(self.env.context or {})
        # Get printer
        context.update({
            'carrier_id': self.id,
            'default_printer_id': (self.coli_printer_id
                and self.coli_printer_id.id
                or False),
            })
        return {
            'name': _('Select the printer'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'select.printer',
            'view_id': self.env.ref(
                'a4o_delivery_colissimo.select_printer_view_form').id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }

    def _check_value(self, value, size):
        if re.search("[^0-9]", value):
            raise UserError(
                _('Only digit chars are authorised in this field!'))
        if len(value) != size:
            raise UserError(_('This field must have to %s characters!') % size)
        return value

    @api.onchange('coli_account_number')
    def onchange_coli_account_number(self):
        if self.coli_account_number:
            self.coli_account_number = self._check_value(
                self.coli_account_number, 6)

    def colissimo_get_delivery_slip(self, pickings):
        _logger.debug("colissimo_get_delivery_slip: begin")
        DeliverySlip = self.env['delivery.slip']

        if not all([x.carrier_tracking_ref for x in pickings]):
            raise UserError(
                _("Some selected pickings are no tracking number!"))

        tracking_numbers = []
        for picking in pickings:
            tracking_numbers.extend(picking.carrier_tracking_ref.split(', '))
        coli = ColissimoRequest(self.prod_environment, self.log_xml)
        delivery_slip = coli.delivery_slip_request(self, tracking_numbers)
        if not delivery_slip:
            raise UserError(
                _("No delivery slip was returned!"))
        dl = DeliverySlip.create({
            'name': delivery_slip['name'],
            'date': delivery_slip['date'],
            'delivery_type': self.delivery_type,
            'pickings': [(6, 0, [x.id for x in pickings])],
            })
        if dl:
            log_message = (
                _("Delivery slip getting from Colissimo<br/> "
                    "<b>with number:</b> %s") % delivery_slip['name'])
            attachments = [(
                    _('Delivery_Slip_%s.pdf') % delivery_slip['name'],
                    delivery_slip['pdf'])]
            dl.message_post(body=log_message, attachments=attachments)
            form = self.env.ref('a4o_delivery_slip.delivery_slip_view_form')
            return {
                'name': _('Delivery Slip'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'delivery.slip',
                'views': [(form.id, 'form')],
                'view_id': form.id,
                'target': 'current',
                'res_id': dl.id,
                }

    def colissimo_send_shipping(self, pickings):
        _logger.debug("colissimo_send_shipping: begin")
        res = []
        coli = ColissimoRequest(self.prod_environment, self.log_xml)
        for picking in pickings:
            package_count = len(picking.package_ids) or 1
            _logger.debug(
                "colissimo_send_shipping: Pack. count: %s" % package_count)
            shipping = coli.shipping_request(picking, self)

            shipping_price = (float(shipping['price']) / 100)
            currency = (
                picking.sale_id.currency_id or picking.company_id.currency_id)
            if currency.name == shipping['currency']:
                carrier_price = currency.round(shipping_price)
            else:
                quote_currency = self.env['res.currency'].search([
                    ('name', '=', shipping['currency']),
                    ], limit=1)
                carrier_price = quote_currency._convert(
                    shipping_price, currency, picking.company_id,
                    picking.sale_id.date_order or fields.Date.today())

            package_labels = coli.get_response()
            carrier_tracking_ref = ', '.join(package_labels['parcelNumber'])
            log_message = (
                _("Shipment created into Colissimo<br/> "
                    "<b>Tracking Numbers:</b> %s<br/>"
                    "<b>Packages:</b> %s") % (
                        carrier_tracking_ref, carrier_tracking_ref))

            attachments = []
            if picking.carrier_id.coli_label_format.startswith('PDF_'):
                labels = pdf.merge_pdf(package_labels['label'])
                attachments.append((_('Label_Colissimo.pdf'), labels))
                if picking.carrier_id.coli_direct_printing:
                    self._print_document(labels,
                        picking.carrier_id.coli_printer_id)
            else:
                for idx, label in enumerate(package_labels['label']):
                    attachments.append((
                        _('Label_Colissimo-%s.%s') % (
                            package_labels['parcelNumber'][idx],
                            self.coli_label_format),
                        label))
                    if picking.carrier_id.coli_direct_printing:
                        self._print_document(label,
                            picking.carrier_id.coli_printer_id)
            if 'cn23' in package_labels:
                attachments.append((
                        'cn23.pdf',
                        pdf.merge_pdf(package_labels['cn23'])))
            picking.message_post(body=log_message, attachments=attachments)

            shipping_data = {
                'exact_price': carrier_price,
                'tracking_number': carrier_tracking_ref,
                }
            res += [shipping_data]
        return res

    def colissimo_cancel_shipment(self, picking):
        picking.message_post(
            body=_("Colissimo does not offer cancellation of requests."
                "Do not put the package %s acts as "
                "cancellation!") % (picking.carrier_tracking_ref))
        picking.write({
            'carrier_tracking_ref': '',
            'carrier_price': 0.0,
            })
        # Remove attachment ...
        if self.coli_remove_label:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', picking._name),
                ('res_id', '=', picking.id),
                ('name', 'like', '_Colissimo'),
                ])
            if attachments:
                attachments.unlink()

    def colissimo_get_tracking_link(self, picking):
        tracking_urls = []
        for nb in picking.carrier_tracking_ref.split(', '):
            tracking_urls.append((
                _("Package %s") % nb,
                'https://www.laposte.fr/outils/suivre-vos-envois?code=%s' % nb,
                ))
        return (len(tracking_urls) == 1
            and tracking_urls[0][1]
            or json.dumps(tracking_urls))

    def colissimo_rate_shipment(self, order):
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

    def colissimo_select_relaypoint(self, pickings):
        _logger.debug('colissimo_select_relaypoint:' % pickings)
        relaypoints = []
        coli = ColissimoRequest(self.prod_environment, self.log_xml)
        for picking in pickings:
            relaypoints += coli.relaypoint_request(picking, self)
        return relaypoints

    def get_ftd(self, partner_id):
        Countries = self.env["res.country.group"]
        dom_tom = Countries.search(
            [('name', '=', 'DOM-TOM')], limit=1)
        if (partner_id
                and partner_id.country_id
                and partner_id.country_id.id in dom_tom.country_ids.ids
                and partner_id.country_id.code not in ['YT', 'PM']):
            return True
        return False

    def needs_cn23(self, partner_id):
        Countries = self.env["res.country.group"]
        if not partner_id or not partner_id.country_id:
            # No partner_id or no country defined = no cn23 needed.
            return False
        country = partner_id.country_id
        zipcode = partner_id.zip
        exception_countries = Countries.search(
            [('name', '=', 'Specific territory')], limit=1)
        if country.id in exception_countries.country_ids.ids:
            if (country.code == 'ES'
                    and zipcode[:2] in ['35', '38', '51', '52']):
                return True
            if (country.code == 'IT'
                    and zipcode in ['23030', '22060']):
                return True
            if (country.code == 'DE'
                    and zipcode in ['27498', '78266']):
                return True
            if (country.code == 'UK'
                    and zipcode[:2] in ['JE', 'IM', 'GY']):
                return True
            if (country.code == 'GR'
                    and (zipcode.replace(' ', '')
                        in ['63075', '60386', '63086', '63087'])):
                return True
        europe = Countries.search([('name', '=', 'Europe')], limit=1)
        if country.id not in europe.country_ids.ids:
            return True
        return False
