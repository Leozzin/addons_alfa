# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from odoo import _
from odoo.exceptions import UserError
import requests
import hashlib
import json


from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


_logger = logging.getLogger(__name__)


class ChronoRequest(object):
    def __init__(self, carrier, record):
        self.carrier = carrier
        self.record = record
        self.appVersion = 3.0
        # self.servicecode = self.carrier.service_code
        self.uid = self.carrier.chrono_alfa_ws_uid
        self.url = "https://ws.chrono-api.fr/services/"



    def _prepare_address(self, partner):

        if partner.name:
            split=partner.name.split(" ")
        if len (split) >=2:
            first=split[0][0:90]
            last=split[1][0:90]
        else:
            first=partner.name[0:90]
            last=partner.name[0:90]
        if partner.phone:
            phone=partner.phone.replace(' ','').replace('+33','0').replace('.','')
            if phone[0:2]=='33':
                phone='0'+phone[2:]
        else:
            raise UserError(
                _("""Ajouter un phone number.""")
            )
        print (first)
        print (last)
        return {
            "country":partner.country_id.code,
            "countryName":partner.country_id.name,
            "parcelType":"COMPANY",
            "address": partner.street,
            "city": partner.city,
            "zipCode": partner.zip,
            "firstName": first,
            "lastName": last,
            "phoneNumber": phone,
            "email": partner.email,
        }





    def _get_data_total_shipping(self):
        weight = self.record.shipping_weight
        volume = p_length = height = width = 0
        liste=[]
        if self.record.package_ids:
            liste = []
            for p in self.record.package_ids:
                if p.shipping_weight!=0:
                    liste.append({"sequenceNumber":self.record.package_ids.ids.index(p.id)+1,"weight":p.shipping_weight})
                else:
                    liste.append({"sequenceNumber": self.record.package_ids.ids.index(p.id)+1, "weight": 0.1})


            for quant in self.record.package_ids.mapped("quant_ids"):
                volume += quant.product_id.volume * quant.quantity
        else:
            liste = []
            lines = self.record.move_line_ids_without_package
            for line in lines.filtered(lambda x: x.qty_done > 0):
                volume += line.product_id.volume * line.qty_done
                p_length += line.product_id.product_length * line.qty_done
                height += line.product_id.product_height * line.qty_done
                width += line.product_id.product_width * line.qty_done
            if self.record.shipping_weight!=0:
                liste.append({"sequenceNumber": "1", "weight": self.record.shipping_weight})
            else:
                liste.append({"sequenceNumber": "1", "weight": 0.1})

        return liste

    def _prepare_create_shipping(self):
        delivery = self._prepare_address(self.record.partner_id)
        data_total = self._get_data_total_shipping()
        print (data_total)
        data = {

            'parcels': [{'id':self.record.id,
                        'data':delivery,
                        # 'products':data_total,


            }],



        }

        return data



    def _send_shipping(self):

        data=self._prepare_create_shipping()
        url_send = self.url + 'task/' + self.uid + '/create'
        session_apt=self.url + '/user/auth'
        sha_signature = \
            hashlib.sha256('Alfa@2021'.encode()).hexdigest()
        connect=requests.post(session_apt, json={'email':'a.feddal@alfaprint.fr','password':sha_signature}, verify=False)
        print(connect)
        for s in connect:
            print (s)

        url_parcel=self.url + 'parcel_config_presets/1/create'
        dataparcel={"VALUE_TO_DECLARE_TO_CUSTOMS":"5",
                    "LENGTH": "5",
                    "WIDTH": "5",
                    "HEIGHT": "5",
                    "WEIGHT": "5",
                    "PRODUCT_DESCRIPTION": "5",
                    "CONTAINER": "5",
                    "SEND_TYPE_INTERNATIONAL": "5",
                    "SEND_TYPE_NATIONAL": "5",
                    "INFORM_SENDER_BY": "5",
                    "SEND_MAIL_RECIPIENT": "5",
                    "INSURANCE_VALUE": "5",


        }
        print (requests.post(url_parcel, json=dataparcel,verify=False))
        for r in requests.post(url_parcel, json=dataparcel,verify=False):
            print (r)
        response = requests.post(url_send, json=data,verify=False)
        print (response)
        for r in response:
            print (r)
        url_get=self.url + 'task/' + self.uid + 'tasks/parcels/not_notified/list'
        get=requests.get(url_get, json=data,verify=False)
        print(get)
        for r in get:
            print(r)









    # TrackSevice
    # def _prepare_state_update(self):
    #     data = {
    #         "SearchCriteria": {"ConsignmentNumber": self.record.carrier_tracking_ref},
    #         "LevelOfDetail": {"Summary": ""},
    #     }
    #     xml_info = dicttoxml.dicttoxml(
    #         data, attr_type=False, custom_root="TrackRequest"
    #     ).decode("utf-8")
    #     return "xml_in=%s" % xml_info

    def tracking_state_update(self):

        url_state = self.url + 'postage/chronopost/' + self.uid + '/parcel/tracking/infos/FR/'+self.record.carrier_tracking_ref

        update_state=requests.get(url_state,verify=False)

        event=update_state.json()[-1]['event'][update_state.json()[-1]['event'].rfind('CHRONOPOST')+11:]


        return {
                    "status_code": event,
                    "delivery_state": "shipping_recorded_in_carrier",
                    "tracking_state_history": event,
                }


    # TntLabel
    # def _prepare_label_address(self, partner):
    #     return {
    #         "name": partner.name,
    #         "addressLine1": partner.street,
    #         "town": partner.city,
    #         "exactMatch": "Y",
    #         "province": partner.state_id.name,
    #         "postcode": partner.zip,
    #         "country": partner.country_id.code,
    #     }

    # def _prepare_label(self):
    #     data_total = self._get_data_total_shipping()
    #     data = {
    #         "consignment": {
    #             "consignmentIdentity": {
    #                 "consignmentNumber": re.sub(
    #                     "[^0-9]", "", self.record.carrier_tracking_ref
    #                 ),
    #                 "customerReference": self.record.name,
    #             },
    #             "collectionDateTime": fields.Datetime.today(),
    #             "sender": self._prepare_label_address(
    #                 self.record.company_id.partner_id
    #             ),
    #             "delivery": self._prepare_label_address(self.record.partner_id),
    #             "product": {
    #                 "lineOfBusiness": self.record.carrier_id.tnt_line_of_business,
    #                 "groupId": 0,
    #                 "subGroupId": 0,
    #                 "id": self.product_service,
    #                 "type": self.product_type,
    #                 "option": self.product_code,
    #             },
    #             "account": self._prepare_account(self.record.company_id.partner_id),
    #             "totalNumberOfPieces": self.record.number_of_packages,
    #             "pieceLine": {
    #                 "identifier": 1,
    #                 "goodsDescription": self.record.name,
    #                 "pieceMeasurements": {
    #                     "length": data_total["length"],
    #                     "width": data_total["width"],
    #                     "height": data_total["height"],
    #                     "weight": data_total["weight"],
    #                 },
    #                 "pieces": {
    #                     "sequenceNumbers": self.record.number_of_packages,
    #                     "pieceReference": "",
    #                 },
    #             },
    #         }
    #     }
    #     return dicttoxml.dicttoxml(
    #         data, attr_type=False, custom_root="labelRequest"
    #     ).decode("utf-8")
    #
    # def _get_label_info(self):
    #     if not self.record.carrier_tracking_ref:
    #         return
    #     response = self._send_api_request(
    #         url="%s/expresslabel/documentation/getlabel" % self.url,
    #         data=self._prepare_label(),
    #         content_type="application/x-www-form-urlencoded",
    #     )
    #     res = json.loads(json.dumps(xmltodict.parse(response)))
    #     if "labelResponse" in res:
    #         res = res["labelResponse"]
    #     if "brokenRules" in res:
    #         errors = res["brokenRules"]
    #         if type(errors) is not list:
    #             errors = [errors]
    #         raise UserError(
    #             _("Sending to TNT\n%s")
    #             % (
    #                 "\n".join(
    #                     "%(errorCode)s %(errorDescription)s" % error for error in errors
    #                 )
    #             )
    #         )
    #     print ("hello res label")
    #     print (res)
    #     res = res["consignment"]
    #     p_data = res["pieceLabelData"]
    #     c_data = res["consignmentLabelData"]
    #     twoDBarcode_text_split = p_data["twoDBarcode"]["#text"].split("|")
    #     c_data_fcd = c_data["freeCirculationDisplay"]
    #     c_data_dd = c_data["destinationDepot"]
    #     vals = {
    #         "tnt_consignment_mumber": c_data["consignmentNumber"],
    #         "tnt_consignment_date": twoDBarcode_text_split[-2],
    #         "tnt_consignment_free_circulation": c_data_fcd["#text"],
    #         "tnt_consignment_sort_split": c_data["sortSplitText"],
    #         "tnt_consignment_destination_depot": c_data_dd["depotCode"],
    #         "tnt_consignment_destination_depot_day": c_data_dd["dueDayOfMonth"],
    #         "tnt_consignment_cluster_code": c_data["clusterCode"],
    #         "tnt_consignment_origin_depot": c_data["originDepot"]["depotCode"],
    #         "tnt_consignment_product": c_data["product"]["#text"],
    #         "tnt_consignment_option": twoDBarcode_text_split[19],
    #         "tnt_consignment_market": c_data["marketDisplay"]["#text"],
    #         "tnt_consignment_transport": c_data["transportDisplay"]["#text"],
    #         "tnt_piece_barcode": p_data["barcode"]["#text"],
    #     }
    #     if "transitDepots" in c_data and c_data["transitDepots"]:
    #         transitDepot = c_data["transitDepots"]["transitDepot"]
    #         vals["tnt_consignment_transit_depot"] = transitDepot["depotCode"]
    #     if "xrayDisplay" in c_data and "#text" in c_data["xrayDisplay"]:
    #         vals["tnt_consignment_xray"] = c_data["xrayDisplay"]["#text"]
    #     self.record.write(vals)
