# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo.exceptions import UserError
from odoo import _
from datetime import datetime
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from suds.client import Client, WebFault
from suds.sudsobject import asdict
import logging
import re
import binascii
import copy

_logger = logging.getLogger(__name__)
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)

""""
<MODEL_NAME> = [
    {
        'struct': <name> # Define the name of the object that must be created,
                         # and filled with 'content'
        'content': [ # Definition of the content ///
            {
                'src': <string>
                'dst': <string>
                'default': default value if 'src' isn't defined,
                'required': must have a value (not only present)
                'evaluate_default': if True the default value will be evaluate,
                            else the default value is the value
                'max_size': ...
                },
            { ... },
            ]
        },
    { ... },
"""

LABEL_FORMAT = [
    ('PDF', 'PDF standard'),
    ('PPR', 'PDF with relay points'),
    ('SPD', 'PDF without proof'),
    ('THE', 'PDF thermal printer without proof'),
    ('THEPSG', 'THE format in landscape'),
    ('Z2DPSG', 'ZPL format in landscape'),
    ('Z2D', 'ZPL for thermal printer'),
    ('PDF|XML', 'For automaton in PO'),
    ('ZPL300', 'ZPL 300dpi for thermal printer'),
    ]

WEIGHT_REC20 = {
    't': 'TNE',
    'kg': 'KGM',
    'g': 'GRM',
    }

TYPEPOINT = {
    'A': _('Chronopost Agency'),
    'B': _('Post office'),
    'P': _('Relay point'),
    }

DAYS = {
    '1': _('Monday'),
    '2': _('Tuesday'),
    '3': _('Wednesday'),
    '4': _('Thursday'),
    '5': _('Friday'),
    '6': _('Saturday'),
    '7': _('Sunday'),
    }

SHIPPINGMULTIPARCELV3 = [
    # esdValue3
    {
        'struct': 'esdValue3',
        'content': [],
        },
    # headerValue
    {
        'struct': 'headerValue',
        'required': True,
        'content': [
            {
                'dst': 'idEmit',
                'default': '',
                },
            {
                'dst': 'identWebPro',
                'default': '',
                },
            {
                'dst': 'accountNumber',
                'src': "self.credential.get('account_number')",
                'max_size': 8,
                'required': True,
                },
            {
                'dst': 'subAccount',
                'src': "self.credential.get('sub_account')",
                'max_size': 0,
                'required': True,
                },
            ],
        },
    # shipperValueV2 []
    {
        'struct': 'shipperValueV2',
        'required': True,
        'loop': "[1]",
        'content': [
            {
                'dst': 'shipperCivility',
                'default': 'M',
                'regexp': '[E|L|M]',
                'required': True,
                },
            {
                'dst': 'shipperName',
                'src': 'picking.company_id.partner_id.name',
                'default': '',
                'required': True,
                'max_size': 100,
                },
            {
                'dst': 'shipperName2',
                'default': '',
                'max_size': 100,
                },
            {'dst': 'shipperContactName', 'default': ''},
            {
                'dst': 'shipperAdress1',
                'src': 'picking.company_id.partner_id.street',
                'required': True,
                'max_size': 38
                },
            {
                'dst': 'shipperAdress2',
                'src': 'picking.company_id.partner_id.street2',
                'default': '',
                'max_size': 38,
                },
            {
                'dst': 'shipperZipCode',
                'src': 'picking.company_id.partner_id.zip',
                'required': True,
                'max_size': 9,
                },
            {
                'dst': 'shipperCity',
                'src': 'picking.company_id.partner_id.city',
                'required': True,
                'max_size': 50,
                },
            {
                'dst': 'shipperCountry',
                'src': 'picking.company_id.partner_id.country_id.code',
                'default': 'FR',
                'required': True,
                'max_size': 2,
                },
            {
                'dst': 'shipperCountryName',
                'src': 'picking.company_id.partner_id.country_id.name or None',
                'default': '',
                },
            {
                'dst': 'shipperPhone',
                'src': 'picking.company_id.partner_id.phone',
                'default': '',
                'max_size': 17,
                },
            {
                'dst': 'shipperMobilePhone',
                'src': 'picking.company_id.partner_id.mobile',
                'default': '',
                'max_size': 17,
                },
            {
                'dst': 'shipperEmail',
                'src': 'picking.company_id.partner_id.email',
                'default': '',
                'max_size': 80,
                },
            {'dst': 'shipperPreAlert', 'default': '0'},
            ],
        },
    # customerValue
    {
        'struct': 'customerValue',
        'required': True,
        'content': [
            {
                'dst': 'customerCivility',
                'default': 'M',
                'regexp': '[E|L|M]',
                'required': True,
                },
            {
                'dst': 'customerName',
                'src': 'picking.company_id.partner_id.name',
                'required': True,
                'max_size': 100,
                },
            {
                'dst': 'customerName2',
                'default': '',
                'max_size': 100,
                },
            {'dst': 'customerContactName', 'default': ''},
            {
                'dst': 'customerAdress1',
                'src': 'picking.company_id.partner_id.street',
                'default': '',
                'required': True,
                'max_size': 38
                },
            {
                'dst': 'customerAdress2',
                'src': 'picking.company_id.partner_id.street2',
                'default': '',
                'max_size': 38,
                },
            {
                'dst': 'customerZipCode',
                'src': 'picking.company_id.partner_id.zip',
                'required': True,
                'max_size': 9,
                },
            {
                'dst': 'customerCity',
                'src': 'picking.company_id.partner_id.city',
                'required': True,
                'max_size': 50,
                },
            {
                'dst': 'customerCountry',
                'src': 'picking.company_id.partner_id.country_id.code',
                'default': 'FR',
                'required': True,
                'max_size': 2,
                },
            {
                'dst': 'customerCountryName',
                'src': 'picking.company_id.partner_id.country_id.name or None',
                'default': '',
                },
            {
                'dst': 'customerPhone',
                'src': 'picking.company_id.partner_id.phone or None',
                'default': '',
                'max_size': 17,
                },
            {
                'dst': 'customerMobilePhone',
                'src': 'picking.company_id.partner_id.mobile or None',
                'default': '',
                'max_size': 17,
                },
            {
                'dst': 'customerEmail',
                'src': 'picking.company_id.partner_id.email',
                'default': '',
                'max_size': 80,
                },
            {'dst': 'customerPreAlert', 'default': '0'},
            {'dst': 'printAsSender', 'default': 'N'},
            ],
        },
    # recipientValueV2 []
    {
        'struct': 'recipientValueV2',
        'required': True,
        'loop': "[1]",
        'content': [
            # {
            #     'dst': 'recipientCivility',
            #     'default': 'M',
            #     'regexp': '[E|L|M]',
            #     'required': True,
            #     },
            {
                'dst': 'recipientName',
                'src': ('picking.cpst_get_names(picking.partner_id, '
                    'picking.original_partner_id).get("name1")'),
                'max_size': 100,
                'required': True,
                },
            {
                'dst': 'recipientName2',
                'src': ('picking.cpst_get_names(picking.partner_id, '
                    'picking.original_partner_id).get("name2")'),
                'max_size': 100,
                },
            {
                'dst': 'recipientAdress1',
                'src': 'picking.partner_id.street',
                'required': True,
                'max_size': 38
                },
            {
                'dst': 'recipientAdress2',
                'src': 'picking.partner_id.street2 or None',
                'default': '',
                'max_size': 38,
                },
            {
                'dst': 'recipientZipCode',
                'src': 'picking.partner_id.zip',
                'required': True,
                'max_size': 9,
                },
            {
                'dst': 'recipientCity',
                'src': 'picking.partner_id.city',
                'required': True,
                'max_size': 50,
                },
            {
                'dst': 'recipientCountry',
                'src': 'picking.partner_id.country_id.code or None',
                'default': 'FR',
                'required': True,
                'max_size': 2,
                },
            {
                'dst': 'recipientCountryName',
                'src': 'picking.partner_id.country_id.name or None',
                'default': '',
                },
            {
                'dst': 'recipientPhone',
                'src': ('picking.partner_id.phone '
                        'or (picking.partner_id.parent_id '
                        'and picking.partner_id.parent_id.phone)'
                        'or None'),
                'default': '',
                'max_size': 17,
                },
            {
                'dst': 'recipientMobilePhone',
                'src': ('picking.partner_id.mobile '
                        'or (picking.partner_id.parent_id '
                        'and picking.partner_id.parent_id.mobile) '
                        'or None'),
                'default': '',
                'max_size': 17,
                },
            {
                'dst': 'recipientEmail',
                'src': ('picking.partner_id.email '
                        'or (picking.partner_id.parent_id '
                        'and picking.partner_id.parent_id.email) '
                        'or None'),
                'default': '',
                'max_size': 80,
                },
            {'dst': 'recipientPreAlert', 'default': '0'},
            # FIXME
            # {'dst': 'identityCardNumber', 'default': '',},
            # {'dst': 'province', 'default': '',},
            # {'dst': 'language', 'default': '',},
            ],
        },
    # refValueV2 [x]
    {
        'struct': 'refValueV2',
        'required': True,
        'loop': "picking.move_line_ids.mapped('result_package_id')",
        'content': [
            {'dst': 'customerSkybillNumber', 'default': ''},
            {'dst': 'PCardTransactionNumber', 'default': ''},
            {
                'dst': 'recipientRef',
                'src': ('picking.partner_id.code_relaypoint '
                        'if picking.carrier_id.product_code == "86" '
                        'else "%s - %s" % (picking.name, picking.origin)'),
                'required': True,
                'max_size': 35,
                },
            {
                'dst': 'shipperRef',
                'src': '"%s - %s" % (picking.name, picking.origin)',
                'required': True,
                'max_size': 35,
                },
            {
                'dst': 'idRelais',
                'src': ('picking.partner_id.code_relaypoint '
                        'if picking.carrier_id.product_code == "86" '
                        'else ""'),
                'required': True,
                'max_size': 35,
                },
            ],
        },
    # skybillWithDimensionsValueV5 [x]
    {
        'struct': 'skybillWithDimensionsValueV5',
        'required': True,
        'loop': "picking.move_line_ids.mapped('result_package_id')",
        'content': [
            {
                'dst': 'bulkNumber',
                'src': "len(picking.move_line_ids.mapped("
                       "'result_package_id'))",
                'default': '1',
                },
            {
                'dst': 'skybillRank',
                'src': "options['number']",
                'default': '1',
                },
            {'dst': 'masterSkybillNumber', 'default': ''},
            {
                'dst': 'codCurrency',
                'src': 'picking.company_id.currency_id.name',
                'default': 'EUR',
                'required': True,
                },
            {'dst': 'codValue', 'default': ''},
            {
                'dst': 'customsCurrency',
                'src': 'picking.company_id.currency_id.name',
                'default': 'EUR',
                'required': True,
                },
            {'dst': 'customsValue', 'default': '0'},
            {
                'dst': 'insuredCurrency',
                'src': 'picking.company_id.currency_id.name',
                'default': 'EUR',
                'required': True,
                },
            {
                'dst': 'insuredValue',
                'default': '0.0',
                'required': True,
                },
            {'dst': 'portCurrency', 'default': ''},
            {
                'dst': 'portValue',
                'default': '0.0',
                'required': True,
                },
            {
                'dst': 'evtCode',
                'default': 'DC',
                'required': True,
                },
            {
                'dst': 'objectType',
                'default': 'MAR',
                'required': True,
                },
            {
                'dst': 'productCode',
                'src': 'picking.carrier_id.product_code',
                'required': True,
                },
            {
                'dst': 'service',
                'default': '0',
                'required': True,
                },
            {
                'dst': 'shipHour',
                'src': "datetime.now().strftime('%H')",
                # 'default': '18',
                'required': True,
                },
            {
                'dst': 'shipDate',
                'src': "datetime.now().strftime('%d/%m/%Y')",
                # 'default': '2018-11-14T15:29:36+02:00',
                'required': True,
                },
            {
                'dst': 'weight',
                'src': "options['loop'].shipping_weight",
                'required': True,
                },
            {
                'dst': 'weightUnit',
                'default': 'KGM',
                # 'compute': '_get_weight',
                },
            {'dst': 'height', 'default': '0'},
            {'dst': 'length', 'default': '0'},
            {'dst': 'width', 'default': '0'},
            {'dst': 'content1', 'default': ''},
            {'dst': 'content2', 'default': ''},
            {'dst': 'content3', 'default': ''},
            {'dst': 'content4', 'default': ''},
            {'dst': 'content5', 'default': ''},
            {'dst': 'latitude', 'default': ''},
            {'dst': 'longitude', 'default': ''},
            {'dst': 'qualite', 'default': ''},
            {'dst': 'source', 'default': ''},
            {'dst': 'as', 'default': ''},
            {'dst': 'toTheOrderOf', 'default': ''},
            ],
        },
    # skybillParamsValueV2
    {
        'struct': 'skybillParamsValueV2',
        'required': True,
        'content': [
            {
                'dst': 'duplicata',
                'default': 'N',
                'required': True,
                },
            {
                'dst': 'mode',
                'src': 'picking.carrier_id.cpst_label_format',
                'default': 'PDF',
                'required': True,
                },
            {
                'dst': 'withReservation',
                'default': '0',
                'required': True,
                },
            ],
        },
    # simple data
    {
        'content': [
            {
                'dst': 'password',
                'src': "self.credential.get('password')",
                'max_size': 6,
                'required': True,
                },
            {
                'dst': 'modeRetour',
                'default': '2',
                'required': True,
                },
            {
                'dst': 'numberOfParcel',
                'src': ("len(picking.move_line_ids.mapped("
                        "'result_package_id'))"),
                'required': True,
                },
            {
                'dst': 'version',
                'default': '2.0',
                'required': True,
                },
            {
                'dst': 'multiparcel',
                'src': ("'Y' if len(picking.move_line_ids.mapped("
                        "'result_package_id')) > 1 else 'N'"),
                'required': True,
                },
            ],
        },
    ]

RECHERCHEPOINTCHRONOPOST = [
    {
        'content': [
            {
                'dst': 'accountNumber',
                'src': "self.credential.get('account_number')",
                'max_size': 8,
                'required': True,
                },
            {
                'dst': 'password',
                'src': "self.credential.get('password')",
                'max_size': 6,
                'required': True,
                },
            {
                'dst': 'address',
                'src': ("picking.partner_id.street "
                        "or picking.partner_id.street2 "
                        "or False"),
                'required': True,
                },
            {
                'dst': 'zipCode',
                'src': 'picking.partner_id.zip',
                'required': True,
                },
            {
                'dst': 'city',
                'src': 'picking.partner_id.city',
                'required': True,
                },
            {
                'dst': 'countryCode',
                'src': ('picking.partner_id.country_id '
                        'and picking.partner_id.country_id.code or "FR"'),
                'default': 'FR',
                'required': True,
                },
            {
                'dst': 'type',
                'default': 'T',
                'regexp': '[A|B|P|T]',
                'required': True,
                },
            {
                'dst': 'productCode',
                'src': 'picking.carrier_id.product_code',
                'required': True,
                },
            {
                'dst': 'service',
                'default': 'T',
                'regexp': '[L|D|I|T]',
                'required': True,
                },
            {
                'dst': 'weight',
                'src': "picking.shipping_weight * 1000",
                'required': True,
                },
            {
                'dst': 'shippingDate',
                'src': "datetime.now().strftime('%d/%m/%Y')",
                # 'src': "picking.fields.Date.today().strftime(DF)",
                'required': True,
                },
            {
                'dst': 'maxPointChronopost',
                'src': "picking.carrier_id.cpst_max_point",
                'required': True,
                },
            {
                'dst': 'maxDistanceSearch',
                'src': "picking.carrier_id.cpst_distance_search",
                'required': True,
                },
            {
                'dst': 'holidayTolerant',
                'default': '1',
                'required': True,
                },
            ],
        },
    ]


class ChronopostRequest():
    """ """
    def __init__(self, prod_environment, debug_logger):
        self.debug_logger = debug_logger
        self.client = None
        self.prod_environment = prod_environment

    def _set_credential(self, carrier):
        if not self.prod_environment:
            self.credential = {
                'account_number': carrier.cpst_test_account_number,
                'sub_account': carrier.cpst_test_sub_account,
                'password': carrier.cpst_test_passwd,
                }
        else:
            self.credential = {
                'account_number': carrier.cpst_prod_account_number,
                'sub_account': carrier.cpst_prod_sub_account,
                'password': carrier.cpst_prod_passwd,
                }

    def _model_keys(self, model, required=False):
        keys = []
        for item in model:
            key = item.get('struct')
            if not key and not required:
                for content in item.get('content'):
                    keys.append(content.get('dst'))
            else:
                if not required:
                    keys.append(key)
                else:
                    if item.get('required'):
                        keys.append(key)
        return keys

    def _chronopost_request(self, service):
        self.client = Client(service)

    def _check_conditions(self, value, content):
        """
        @param value: Value to check
        @param content: Dict of content constraints to check
        @return: Value respecting constraints.
        """
        max_size = content.get('max_size')
        if max_size:
            value = value and value[:max_size]
        if content.get('required'):
            if value is None:
                raise UserError(_(
                    "A value for the field '%s' is required!"
                    "(value: %s)!") % (content.get('dst'), value))
        regexp = content.get('regexp')
        if regexp:
            if not re.match(regexp, value):
                raise UserError(_(
                    "The value of the field '%s' doesn't respect the expected "
                    "conditions (conditions: %s, value: %s)!") % (
                        content.get('dst'), regexp, value))
        return value

    def _check_required(self, model, value):
        # Get all field must be present
        must_fields = [k for k, v in model.items() if v.get('required')]
        # Check if all fields are present
        cur_fields = [k for k, v in asdict(value).items() if v is None]
        print('must:', must_fields, 'have:', cur_fields)
        not_present = set(must_fields) - set(cur_fields)
        if not_present:
            raise UserError(
                _('Some field are missing: %s') % ', '.join(list(not_present)))

    def _build_value(self, content, picking, options=None):
        """ """
        value = None
        source = content.get('src')
        if source:
            value = eval(source)
        if value is None:
            source = content.get('default')
            if content.get('evaluate_default'):
                value = eval(source, globals())
            else:
                value = source
        value = self._check_conditions(value, content)
        return value

    def _build_content(self, content, picking, options=None):
        res = {}
        struct = options.get('struct')
        for item in content:
            if struct:
                setattr(
                    struct, item.get('dst'),
                    self._build_value(item, picking, options))
            res.update(
                {item.get('dst'): self._build_value(item, picking, options)})
        return struct or res

    def _build_values(self, model, picking, options=None):
        values = {}
        options = options or {}
        for val in model:
            result = None
            opt = options.copy()
            struct = val.get('struct')
            if struct:
                opt.update({'struct': self.client.factory.create(struct)})
            loop = val.get('loop')
            content = val.get('content')
            if loop:
                loop = eval(loop, locals())
                result = []
                for l in loop:
                    new_opt = copy.deepcopy(opt)
                    new_opt.update({'loop': l, 'number': len(result) + 1})
                    result.append(self._build_content(content, picking,
                        new_opt))
            else:
                if content:
                    result = self._build_content(content, picking, opt)
            if not struct:
                values.update(result)
            else:
                values.update({struct: result})
        return values

    def shipping_request(self, picking, carrier):
        """ Removal request to the carrier.

            Model of method :
                shippingMultiParcelV3(
                    esdValue3 esdValue,
                    headerValue headerValue,
                    shipperValueV2[] shipperValue,
                    customerValue customerValue,
                    recipientValueV2[] recipientValue,
                    refValueV2[] refValue,
                    skybillWithDimensionsValueV5[] skybillValue,
                    skybillParamsValueV2 skybillParamsValue,
                    xs:string password,
                    xs:string modeRetour,
                    xs:int numberOfParcel,
                    xs:string version,
                    xs:string multiParcel,
                    scheduledValue[] scheduledValue,
                    recipientLocalValueV2[] recipientLocalValue,
                    customsValue[] customsValue)
        """
        result = {
            'price': picking.get_delivery_price(),
            'currency': picking.company_id.currency_id.name,
            }

        if not all([
                po.result_package_id is not False
                for po in picking.move_line_ids]):
            raise UserError(_("Some products have not been put in packages!"))

        # Init. some infos ...
        self._set_credential(carrier)
        self.client = Client(carrier.cpst_shipping_url)
        # Getting data and build the parameters ...
        model = SHIPPINGMULTIPARCELV3
        keys = self._model_keys(model)
        data = self._build_values(model, picking.sudo())

        # Test required items ...
        required_keys = self._model_keys(model, required=True)
        if required_keys:
            not_present = [key for key in required_keys if not data[key]]
            if not_present:
                raise UserError(
                    _("Values are not present to obtain a label: "
                      "%s" % not_present))
        values = [data[key] for key in keys]
        try:
            # Beware the query must respect the field order
            self.response = self.client.service.shippingMultiParcelV3(*values)
        except WebFault as e:
            _logger.error('Error from Chronopost API: %s' % e)
            raise UserError(_('Error from Chronopost API: %s') % (e))
        except Exception as e:
            # if authentification error
            #     if isinstance(e[0], tuple) and e[0][0] == 401:
            #     raise e[0][0]
            raise e
        else:
            _logger.debug('Response code: %s' % self.response.errorCode)
            if self.response.errorCode:
                raise UserError(
                    _('Error when retrieve label: %s(%s)') % (
                        self.response.errorMessage, self.response.errorCode))
            else:
                if self.response.resultMultiParcelValue:
                    result.update({'tracking_number': ','.join([
                            x.skybillNumber
                            for x in self.response.resultMultiParcelValue
                            ])})
        return result

    def get_label(self):
        res = []
        for parcel in self.response.resultMultiParcelValue:
            res.append(
                (parcel.codeDepot, binascii.a2b_base64(parcel.pdfEtiquette)))
        return res

    def cancel_request(self, picking, carrier):
        result = []
        # Init. some infos ...
        self._set_credential(carrier)
        self.client = Client(carrier.cpst_tracking_url)
        language = carrier.env.context.get('lang')
        if language != 'fr_FR':
            language = 'en_GB'
        for number in picking.carrier_tracking_ref.split(','):
            # If we aren't in prod, unable to cancel shipping.
            if not self.prod_environment:
                result.append(number)
                continue
            # we are in production ... continue.
            values = [
                self.credential.get('account_number'),
                self.credential.get('password'),
                language, number.strip()]
            _logger.debug("cancel_request: %s" % values)
            try:
                _logger.debug("cancel_request: %s" % values)
                # Beware the query must respect the field order
                self.response = self.client.service.cancelSkybill(*values)
            except WebFault as e:
                _logger.error('Error from Chronopost API: %s' % e)
                raise UserError(_('Error from Chronopost API: %s') % (e))
            except Exception as e:
                # if authentification error
                #     if isinstance(e[0], tuple) and e[0][0] == 401:
                #     raise e[0][0]
                raise e
            else:
                _logger.debug('Response code: %s' % self.response.errorCode)
                if self.response.errorCode:
                    raise UserError(
                        _("Error when cancelling sending parcel '%s': "
                          "%s(%s).") % (number, self.response.errorMessage,
                                        self.response.errorCode))
                else:
                    if self.response.cancelSkybillResponse:
                        result.append(number)
        return result

    def relaypoint_request(self, picking, carrier):
        result = []
        # Init. some infos ...
        self._set_credential(carrier)
        self.client = Client(carrier.cpst_relaypoint_url)
        model = RECHERCHEPOINTCHRONOPOST
        # self.client = Client(carrier.cpst_shipping_url)
        # model = SHIPPINGMULTIPARCELV3
        keys = self._model_keys(model)
        data = self._build_values(model, picking)
        values = [data[key] for key in keys]
        _logger.debug("relaypoint_request: %s" % values)
        try:
            # Beware the query must respect the field order
            self.response = self.client.service.recherchePointChronopost(
                *values)
        except WebFault as e:
            _logger.error('Error from Chronopost API: %s' % e)
            raise UserError(_('Error from Chronopost API: %s') % (e))
        except Exception as e:
            # if authentification error
            #     if isinstance(e[0], tuple) and e[0][0] == 401:
            #         raise e[0][0]
            raise e
        else:
            _logger.debug('Response code: %s' % self.response.errorCode)
            if self.response.errorCode:
                raise UserError(
                    _('Error when retrieve relay points: %s(%s)') % (
                        self.response.errorMessage, self.response.errorCode))
            else:
                for point in self.response.listePointRelais:
                    if not point.actif:
                        continue
                    address = {
                        'name': str(point.nom),
                        'street': point.adresse1,
                        'street2': ', '.join(
                            filter(None, [
                                point.adresse2, point.adresse2])),
                        'zip': point.codePostal,
                        'city': point.localite,
                        'country_id': picking.env['res.country'].search([
                                ('code', '=', point.codePays),
                                ]).id,
                        'code_relaypoint': point.identifiant,
                        }
                    hours = [
                        (DAYS[str(x.jour)], x.horairesAsString)
                        for x in point.listeHoraireOuverture
                        ]
                    result.append({
                        'address': address,
                        'hours': hours
                        })
        return result
