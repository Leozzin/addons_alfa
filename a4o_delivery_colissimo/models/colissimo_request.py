# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo.exceptions import UserError
from odoo import _
from suds.client import Client, WebFault
from odoo.addons.a4o_delivery_colissimo.data_tools import (Struct, Char,
    Integer, Float, List)
import zeep
import logging

_logger = logging.getLogger(__name__)
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)


PRODUCT_CODES = {
    'france': {
        'signature': ['DOS'],
        'wo_signature': ['DOM'],
        'relaypoint': ['BPR', 'A2P'],
        },
    'europe': {
        'signature': ['DOS'],
        'wo_signature': ['DOM'],
        'relaypoint': ['CMT', 'PCS', 'BDP'],
        },
    'oversea': {
        'signature': ['CDS'],
        'wo_signature': ['COM'],
        'eco': ['ECO'],
        },
    'international': ['COLI'],
    }

LABEL_FORMAT = [
    ('ZPL_10x15_203dpi', 'ZPL 10x15 203dpi'),
    ('ZPL_10x15_300dpi', 'ZPL 10x15 300dpi'),
    ('DPL_10x15_203dpi', 'DPL 10x15 203dpi'),
    ('DPL_10x15_300dpi', 'DPL 10x15 300dpi'),
    ('PDF_10x15_300dpi', 'PDF 10x15 300dpi'),
    ('PDF_A4_300dpi', 'PDF A4 300dpi'),
    ]

WEIGHT_REC20 = {
    't': 'TNE',
    'kg': 'KGM',
    'g': 'GRM',
    }

TYPEPOINT = {
    'A': _('Colissimo Agency'),
    'B': _('Post office'),
    'P': _('Relay point'),
    }

DAYS = [
    'Lundi',
    'Mardi',
    'Mercredi',
    'Jeudi',
    'Vendredi',
    'Samedi',
    'Dimanche',
    ]

BordereauByParcelNumbers = {
    "contractNumber": Char(name=_('Contract number'), required=True,
        max_size=6, eval="record.coli_account_number"),
    "password": Char(name=_('password'), required=True,
        eval="record.coli_passwd"),
    "generateBordereauParcelNumberList": {
        "parcelsNumbers": [],
        },
    }

RecherchePoint = {
    "accountNumber": Char(name=_('Account number'), required=True,
        max_size=6, eval="record.carrier_id.coli_account_number"),
    "password": Char(name=_('Password'), required=True,
        eval="record.carrier_id.coli_passwd"),
    # "apikey": Char(name=_('API Key'), eval=''),
    # "codTiersPourPartenaire": Char(name=_('Code tiers du partenaire'),
    #    eval=''),
    "address": Char(name=_('Address'), eval="record.partner_id.street",
        max_size=200),
    "zipCode": Char(name=_('Zip code'), required=True,
        eval="record.partner_id.zip", max_size=5),
    "city": Char(name=_('City'), required=True, max_size=35,
        eval="record.partner_id.city"),
    "countryCode": Char(name=_('Country Code'), required=True,
        eval=("record.partner_id.country_id "
            "and record.partner_id.country_id.code"),
        default='FR', max_size=2),
    "weight": Integer(name=_('Weight in grams'), required=True,
        eval="int(record.weight * 1000) or None"),
    "lang": Char(name=_('Lang'), required=True,
        eval=("record.partner_id.country_id "
            "and record.partner_id.country_id.code"),
        default='FR', max_size=2),
    "shippingDate": Char(name=_('Shipping Date'), required=True,
        eval="datetime.now().strftime('%d/%m/%Y')"),
    # "filterRelay": Char(name=_('Filter Relay'), eval=''),
    # "requestId": Char(name=_('Request ID'), eval=''),
    "optionInter": Integer(name=_('Option Inter.'),
        eval=("1 if record.partner_id.country_id "
            "and record.partner_id.country_id.code else 0")),
    }

Article = {
    "description": Char(name=_('Description'), source='product_id.name',
        required=True, max_size=64),
    "quantity": Integer(name=_('Quantity'), source='qty_done', convert=True),
    "weight": Float(name=_('Weight'),
        eval="(record.product_id.weight * 2.20462) "
            "if record.product_id.weight_uom_name == 'lb(s)' "
            "else record.product_id.weight"),
    "value": Float(name=_('Unit price'),
        eval=("record.move_id.sale_line_id "
            "and record.move_id.sale_line_id.price_unit "
            "or record.product_id.lst_price or 1.0")),
    "hsCode": Char(name=_('HS Code'),
                   eval='record.product_id.get_hs_code()'),
    "originCountry": Char(name=_('Origin Country'),
        eval="record.product_id.get_origin_country() or False",
        late_default='originCountry')
    # "currency": [TODO]
    }

Articles = List(name='article', eval=None, content=Article)

CustomsDeclarations = {
    "customsDeclarations": {
        "includeCustomsDeclarations": True,
        "invoiceNumber": Char(name="Invoice Number",
            eval="' ,'.join("
                "[x.name "
                    "for x in record.colissimo_get_invoices()])"),
        "contents": {
            "category": {
                "value": Integer(name='Customs category',
                    eval="int(record.carrier_id.coli_customs_category)")
                },
            },
        },
    }

Package = {
    "weight": Float(name=_('Weight of parcel'), source="shipping_weight",
        required=True),
    }

GenerateLabel = {
    "contractNumber": Char(name=_('Contract number'), required=True,
        max_size=6, eval="record.carrier_id.coli_account_number"),
    "password": Char(name=_('password'), required=True,
        eval="record.carrier_id.coli_passwd"),
    "outputFormat": {
        "outputPrintingType": Char(name='outputPrintingType', required=True,
            eval="record.carrier_id.coli_label_format"),
        },
    "letter": {
        "service": {
            "productCode": Char(name='productCode', required=True,
                eval=("record.colissimo_get_product_code()")),
            "depositDate": Char(name='depositDate', required=True,
                eval="datetime.now().strftime('%Y-%m-%d')"),
            "commercialName": Char(name='commercialName',
                eval=("record.company_id.partner_id.name "
                    "if record.relaypoint_delivery else ''")),
            "totalAmount": Integer(name=_('Total amount'),
                eval=("record.get_delivery_price() "
                    "and (record.get_delivery_price() * 100) "
                    "or 1"), convert=True),
            # By default no return, but we can implement the 'getProductInter'
            # function to retrieve the return codes authorized on the country
            # of destination. Not yet developed at present.
            "returnTypeChoice": Integer(name=_('Return Type'),
                eval='int(3)'),
            },
        "parcel": {
            "pickupLocationId": Char(name='pickupLocationId',
                eval="record.partner_id.code_relaypoint or ''"),
            "ftd": Char(name=_("Free of Taxe and Duty"),
                eval=("'true' if record.carrier_id.get_ftd(record.partner_id) "
                    "else 'false'")),
            },
        "sender": {
            "address": {
                "companyName": Char(name="companyName", required=True,
                    eval="record.company_id.partner_id.name", max_size=35),
                "line2": Char(name="sender:line2", required=True,
                    eval="record.company_id.partner_id.street", max_size=35),
                "line3": Char(name="line2", max_size=35,
                    eval="record.company_id.partner_id.street2"),
                "countryCode": Char(name="countryCode", required=True,
                    eval="record.company_id.partner_id.country_id.code",
                    default='FR', max_size=2),
                "city": Char(name="city", required=True, max_size=35,
                    eval="record.company_id.partner_id.city"),
                "zipCode": Char(name="zipCode", required=True, max_size=5,
                    eval="record.company_id.partner_id.zip"),
                "email": Char(name="email",
                    eval="record.company_id.partner_id.email"),
                "mobileNumber": Char(name="mobileNumber",
                    eval="record.company_id.partner_id.mobile"),
                },
            },
        "addressee": {
            "address": {
                "companyName": Char(name="company name", max_size=35,
                    truncate=True,
                    eval=("record.colissimo_get_names(record.partner_id, "
                          "record.original_partner_id).get('company')")),
                "lastName": Char(name="lastName", max_size=35,
                    eval=("record.colissimo_get_names(record.partner_id, "
                          "record.original_partner_id).get('lastname')")),
                "firstName": Char(name="firstName", max_size=29,
                    eval=("record.colissimo_get_names(record.partner_id, "
                          "record.original_partner_id).get('firstname')")),
                "line2": Char(name="addressee:line2", required=True,
                    eval="record.partner_id.street", max_size=35),
                "line3": Char(name="line2", max_size=35,
                    eval="record.partner_id.street2"),
                "countryCode": Char(name="countryCode", required=True,
                    eval="record.partner_id.country_id.code",
                    default='FR', max_size=2),
                "city": Char(name="city", required=True, max_size=35,
                    eval="record.partner_id.city"),
                "zipCode": Char(name=_("recipient zip code"), required=True,
                    eval="record.partner_id.zip", max_size=5),
                "email": Char(name="email",
                    eval=("record.partner_id.parent_id.email "
                        "if record.relaypoint_delivery "
                        "else record.partner_id.email or ("
                            "record.partner_id.parent_id "
                            "and record.partner_id.parent_id.email)")),
                "mobileNumber": Char(name="mobileNumber",
                    eval=("record.partner_id.parent_id.mobile "
                        "if record.relaypoint_delivery "
                        "else record.partner_id.mobile or ("
                            "record.partner_id.parent_id "
                            "and record.partner_id.parent_id.mobile)")),
                "phoneNumber": Char(name="phoneNumber",
                    eval=("record.partner_id.parent_id.phone "
                        "if record.relaypoint_delivery "
                        "else record.partner_id.phone or ("
                            "record.partner_id.parent_id "
                            "and record.partner_id.parent_id.phone)")),
                },
            },
        },
    }


class ColissimoRequest():
    """ """  
    def __init__(self, prod_environment, debug_logger):
        self.debug_logger = debug_logger
        self.client = None
        self.prod_environment = prod_environment
        self.response = {}

    def delivery_slip_request(self, carrier, tracking_numbers):
        ''' Send request to get delivery slip from tracking_numbers'''

        try:
            cslip = Struct(BordereauByParcelNumbers, carrier)
        except ValueError as e:
            raise UserError(e)
        except Exception:
            raise
        request = cslip.get()

        if tracking_numbers:
            request["generateBordereauParcelNumberList"]["parcelsNumbers"] = \
                tracking_numbers

        self.client = zeep.Client(wsdl=carrier.coli_shipping_url)

        try:
            r = self.client.service.generateBordereauByParcelsNumbers(
                **request)
        except zeep.exceptions.Fault as e:
            _logger.error('Fault from Colissimo API: %s' % e)
            raise UserError(_('Fault from Colissimo API: %s') % (e))
        except zeep.exceptions.Error as e:
            _logger.error('Error from Colissimo API: %s' % e)
            raise UserError(_('Error from Colissimo API: %s') % (e))
        else:
            for msg in r.messages:
                if msg['type'] == 'ERROR':
                    raise UserError(
                        _("Error when retrieve label(s): %s (%s)") % (
                            msg['messageContent'], msg['id']))
            self.response.update({
                    'pdf': r['bordereau']['bordereauDataHandler'],
                    'date': r['bordereau']['bordereauHeader'] \
                        ['publishingDate'],
                    'name': r['bordereau']['bordereauHeader'] \
                        ['bordereauNumber'],
                    'details': r['bordereau']['bordereauHeader'],
                    })
            return self.response

    def shipping_request(self, record, carrier):
        packages = record.move_line_ids.mapped('result_package_id')
        if not packages:
            raise UserError(_("Some products have not been put in packages!"))

        result = {
            'price': 0.0,
            'currency': record.company_id.currency_id.name,
            }

        try:
            clabel = Struct(GenerateLabel, record)
        except ValueError as e:
            raise UserError(e)
        except Exception:
            raise
        request = clabel.get()

        # Update the price with the sale price of delivery.
        result['price'] = request['letter']['service']['totalAmount']

        customs_declaration = record.carrier_id.needs_cn23(record.partner_id)
        if customs_declaration:
            try:
                ccustoms = Struct(CustomsDeclarations, record)
            except ValueError as e:
                raise UserError(e)
            except Exception:
                raise
            request['letter'].update(ccustoms.get())

        defaults = {'originCountry': (record.carrier_id
                and record.carrier_id.coli_country_origin_id
                and record.carrier_id.coli_country_origin_id.code
                or '')}

        self.client = zeep.Client(wsdl=carrier.coli_shipping_url)
        # we need to loop on the number of packages because we have to make
        # one label per package.
        for package in packages:
            move_lines = record.move_line_ids.filtered(
                lambda r: r.result_package_id == package)

            try:
                cpackage = Struct(Package, package)
            except ValueError as e:
                raise UserError(e)
            except Exception:
                raise
            request['letter']['parcel'].update(cpackage.get())

            if customs_declaration:
                try:
                    carticle = Struct(Articles, move_lines, defaults=defaults)
                except ValueError as e:
                    raise UserError(e)
                except Exception:
                    raise
                request['letter']['customsDeclarations']['contents'] \
                    ['article'] = carticle.get()

            _logger.debug("shipping_request: %s" % request)
            try:
                r = self.client.service.generateLabel(request)
            except zeep.exceptions.Fault as e:
                _logger.error('Fault from Colissimo API: %s' % e)
                raise UserError(_('Fault from Colissimo API: %s') % (e))
            except zeep.exceptions.Error as e:
                _logger.error('Error from Colissimo API: %s' % e)
                raise UserError(_('Error from Colissimo API: %s') % (e))
            else:
                for msg in r.messages:
                    if msg['type'] == 'ERROR':
                        raise UserError(
                            _("Error when retrieve label(s): %s (%s)") % (
                                msg['messageContent'], msg['id']))
                self.response.setdefault('parcelNumber', []).append(
                    r.labelResponse['parcelNumber'])
                self.response.setdefault('label', []).append(
                    r.labelResponse['label'])
                if r.labelResponse['cn23']:
                    self.response.setdefault('cn23', []).append(
                        r.labelResponse['cn23'])
        return result

    def get_response(self):
        return self.response

    def cancel_request(self, record, carrier):
        raise UserError(
            _("Colissimo does not offer cancellation of requests. "
              "Do not put the package acts as cancellation."))

    def relaypoint_request(self, record, carrier):
        result = []

        try:
            crecherche = Struct(RecherchePoint, record)
        except ValueError as e:
            raise UserError(e)
        except Exception:
            raise
        request = crecherche.get()

        _logger.debug("relaypoint_request: %s" % request)
        self.client = Client(carrier.coli_relaypoint_url)
        try:
            r = self.client.service.findRDVPointRetraitAcheminement(**request)
        except WebFault as e:
            _logger.error('Fault from Colissimo API: %s' % e)
            raise UserError(_('Fault from Colissimo API: %s') % (e))
        except Exception as e:
            _logger.error('Error from Colissimo API: %s' % e)
            raise UserError(_('Error from Colissimo API: %s') % (e))
        else:
            if r.errorCode != 0:
                raise UserError(
                    _('Error when retrieve relay points: %s (%s)') % (
                        r.errorMessage, r.errorCode))
            if r.qualiteReponse == 0:
                raise UserError(
                    _('The quality of the response is poor ! There is no '
                        'relay point around the address indicated.'))
            for point in r.listePointRetraitAcheminement:
                address = {
                    'name': str(point.nom),
                    'street': point.adresse1,
                    'street2': ', '.join(
                        filter(None, [point.adresse2, point.adresse3])),
                    'zip': point.codePostal,
                    'city': point.localite,
                    'country_id': record.env['res.country'].search([
                            ('code', '=', point.codePays),
                            ]).id,
                    'code_relaypoint': point.identifiant,
                    'point_type': point.typeDePoint,
                    }
                hours = [
                    (d, getattr(point, 'horairesOuverture%s' % (_(d),)))
                    for d in DAYS
                    ]
                result.append({
                    'address': address,
                    'hours': hours
                    })
            return result
