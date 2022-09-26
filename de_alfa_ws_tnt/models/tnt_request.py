# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import zeep
import base64
from zeep.wsse.username import UsernameToken
from datetime import datetime
from odoo import _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class TntRequest(object):
    def __init__(self, carrier, record):
        self.carrier = carrier
        self.record = record
        self.appVersion = 3.0
        self.servicecode = self.carrier.service_code
        self.username = self.carrier.tnt_alfa_ws_username
        self.password = self.carrier.tnt_alfa_ws_password
        self.account = self.carrier.tnt_alfa_ws_account
        self.url = "http://www.tnt.fr/service/?wsdl"
        auth_encoding = "%s:%s" % (self.username, self.password)
        self.authorization = UsernameToken(self.username,  self.password)

    # def _send_api_request(
    #     self, url, data=None, auth=True, content_type="application/xml"
    # ):
    #
    #     print ("Hello send ")
    #     print (url)
    #     print (data)
    #     print (auth)
    #     if data is None:
    #         data = {}
    #     try:
    #         print ("hellotry")
    #         headers = {"Content-Type": content_type}
    #         print ("Auuuutttttorisation")
    #         print (self.authorization)
    #         print ("Basic {}".format(self.authorization))
    #         if auth:
    #             headers["Authorization"] = "Basic {}".format(self.authorization)
    #         res = requests.post(url=url, data=data, headers=headers, timeout=60)
    #         print ("hello res")
    #         print (res)
    #         res.raise_for_status()
    #         tnt_last_request = ("URL: {}\nData: {}").format(self.url, data)
    #         print ("hello data")
    #         print (data)
    #         self.carrier.log_xml(tnt_last_request, "tnt_last_request")
    #         self.carrier.log_xml(res.text or "", "tnt_last_response")
    #         res = res.text
    #     except requests.exceptions.Timeout:
    #         raise UserError(_("Timeout: the server did not reply within 60s"))
    #     except (ValueError, requests.exceptions.ConnectionError):
    #         raise UserError(_("Server not reachable, please try again later"))
    #     except requests.exceptions.HTTPError as e:
    #         if res.status_code != 200:
    #             raise UserError('Request to TNT.\nCode: %s\nContent: %s' % (res.status_code, res.content))
    #         else:
    #             res.json()
    #             raise UserError(
    #                 _("{}\n{}".format(e, res.json().get("Message", "") if res.text else ""))
    #             )
    #     return res
    #
    # def _partner_to_shipping_data(self, partner):
    #     return {
    #         "country": partner.country_id.code,
    #         "town": partner.city,
    #         "postcode": partner.zip,
    #     }
    #
    # def _prepare_product(self):
    #     return {
    #         "id": self.product_code,
    #         "type": self.product_type,
    #         "options": {"option": {"optionCode": self.product_code}},
    #     }
    #
    # def _prepare_account(self, partner):
    #     return {
    #         "accountNumber": self.account,
    #         "accountCountry": partner.country_id.code,
    #     }

    # def _prepare_rate_shipment(self):
    #     totalWeight = 0
    #     totalVolume = 0
    #     for line in self.record.order_line.filtered(
    #         lambda x: x.product_id
    #         and (x.product_id.weight > 0 or x.product_id.volume > 0)
    #     ):
    #         totalWeight += line.product_id.weight * line.product_uom_qty
    #         totalVolume += line.product_id.volume * line.product_uom_qty
    #     data = {
    #         "appId": "PC",
    #         "appVersion": self.appVersion,
    #         "priceCheck": {
    #             "rateId": self.record.name,
    #             "sender": self._partner_to_shipping_data(
    #                 self.record.company_id.partner_id
    #             ),
    #             "delivery": self._partner_to_shipping_data(
    #                 self.record.partner_shipping_id
    #             ),
    #             "collectionDateTime": self.record.expected_date,
    #             "product": self._prepare_product(),
    #             "account": self._prepare_account(self.record.company_id.partner_id),
    #             "currency": self.record.currency_id.name,
    #             "priceBreakDown": True,
    #             "consignmentDetails": {
    #                 "totalWeight": totalWeight,
    #                 "totalVolume": totalVolume,
    #                 "totalNumberOfPieces": 1,
    #             },
    #         },
    #     }
    #     return dicttoxml.dicttoxml(
    #         data, attr_type=False, custom_root="priceRequest"
    #     ).decode("utf-8")

    # def rate_shipment(self):
    #     response = self._send_api_request(
    #         url="%s/expressconnect/pricing/getprice" % self.url,
    #         data=self._prepare_rate_shipment(),
    #     )
    #     response = json.loads(json.dumps(xmltodict.parse(response)))["document"]
    #     if "errors" in response and "priceResponse" not in response:
    #         errors = response["errors"]["brokenRule"]
    #         if type(errors) is not list:
    #             errors = [errors]
    #         raise UserError(
    #             _("Sending to TNT\n%s")
    #             % ("\n".join("%(code)s %(description)s" % error for error in errors))
    #         )
    #     res = {
    #         "success": False,
    #         "price": 0,
    #     }
    #     if "priceResponse" in response:
    #         service = response["priceResponse"]["ratedServices"]["ratedService"]
    #         res["success"] = True
    #         res["price"] = service["totalPrice"]
    #         res["currency"] = response["priceResponse"]["ratedServices"]["currency"]
    #     return res


    def _prepare_address(self, partner):
        # return {
        #     "name": 'ALFAPRINT',
        #     # "address1": partner.street,
        #     "address1": '4120 route de Tournai-FRANCE',
        #     "city": 'Douai',
        #     # "PROVINCE": partner.state_id.name,
        #     "zipCode": '59500',
        #     "contactFirstName": 'ALFAPRINT',
        #     "contactLastName": 'ALFAPRINT',
        #     "phoneNumber": '0982547830',
        #     "emailAddress": 'gaetan@alfaprint.fr',
        # }
        if partner.name:
            split=partner.name.split(" ")
        if len (split) >=2:
            first=split[0][0:11]
            last=split[1][0:18]
        else:
            first=partner.name[0:11]
            last=partner.name[0:18]
        if partner.phone:
            phone=partner.phone.replace(' ','').replace('+33','0').replace('.','')
            if phone[0:2]=='33':
                phone='0'+phone[2:]
        else:
            raise UserError(
                _("""Ajouter un phone number.""")
            )
        return {
            "name": partner.name[0:30],
            "address1": partner.delivery_addres,
            "city": partner.delivery_city,
            "zipCode": partner.delivery_code_zip,
            "contactFirstName": first,
            "contactLastName": last,
            "phoneNumber": phone,
            "emailAddress": partner.email,
        }



    def _prepare_sender(self):
        data = self._prepare_address(self.record.company_id.partner_id)

        return data

    def _get_data_total_shipping(self):
        weight = self.record.shipping_weight
        volume = p_length = height = width = 0
        liste=[]
        if self.record.package_ids:
            liste = []
            for p in self.record.package_ids:
                shipping_weight=sum((i.quantity * i.product_id.weight) for i in p.quant_ids)
                if p.shipping_weight==0:
                    p.shipping_weight=shipping_weight

                if shipping_weight!=0:
                    liste.append({"sequenceNumber":self.record.package_ids.ids.index(p.id)+1,"weight":shipping_weight})
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
        print ("HELLO liste")
        print (liste)
        return liste

    def _prepare_create_shipping(self):
        delivery = self._prepare_address(self.record.partner_id)
        data_total = self._get_data_total_shipping()
        print (data_total)
        data = {
            # 'pickUpRequest': '',
            'shippingDate':datetime.now(),
            'accountNumber': self.account,
            'sender': self._prepare_sender(),
            'labelFormat': "STDA4",
            'receiver': delivery,
            'serviceCode': self.servicecode,
            'saturdayDelivery': "0",
            'quantity': len(data_total),
            "parcelsRequest": {"parcelRequest":data_total},
            # "parcelsRequest": {"parcelRequest": [{"sequenceNumber": "1", "weight": "1.1"}]},


        }

        return data



    def _send_shipping(self):
            if not self.record.package_ids:
                print ("hello not packages")
                for i in self.record.move_line_ids_without_package:
                    if i.product_id.categ_id.name=='ALFA TANK':
                        self.record._put_in_pack(i)

            self.record._put_in_pack(self.record.move_line_ids_without_package.filtered(lambda r: not r.result_package_id))

            client = zeep.Client(wsdl=self.url, wsse=self.authorization)
            data=self._prepare_create_shipping()
            try:
                response = client.service.expeditionCreation(parameters=data)
                print("test_multipackkk")
                print(data)
                print(response)
                if response.parcelResponses:
                    print(len(response.parcelResponses))
                    if len(response.parcelResponses)==1:
                        parcelnumber = response.parcelResponses[0].parcelNumber
                        sequenceNumber = response.parcelResponses[0].sequenceNumber

                        self.record.carrier_tracking_ref = parcelnumber
                        self.record.carrier_tracking_url = response.parcelResponses[0].trackingURL
                        for p in self.record.package_ids:

                                p.carrier_tracking_ref = parcelnumber
                                p.carrier_tracking_url = response.parcelResponses[0].trackingURL

                        # if self.record.package_ids:

                    else:
                        for request in response.parcelResponses:
                            for p in self.record.package_ids:
                                if str(self.record.package_ids.ids.index(p.id)+1)==request.sequenceNumber:
                                    p.carrier_tracking_ref = request.parcelNumber
                                    p.carrier_tracking_url = request.trackingURL
                self.record.pdf_label = base64.b64encode(response.PDFLabels)
                self.carrier._tnt_alfa_action_label(self.record, response.PDFLabels)
            except zeep.exceptions.Fault as fault:
                msg=fault.message
                # parsed_fault_detail = client.wsdl.types.deserialize(fault.message[0])
                if 'zipCode' in fault.message:
                    msg="Le champ code postale est incorrect"
                raise UserError(msg)







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
        client = zeep.Client(wsdl=self.url, wsse=self.authorization)
        if len (self.record.carrier_tracking_ref)==16:
            try:
                response = client.service.trackingByConsignment(self.record.carrier_tracking_ref)
                if response:
                    SummaryCode = response.statusCode
                    mapped_states = {
                        "INT": "in_transit",
                        "DEL": "customer_delivered",
                        "EXC": "incidence",
                        "000": "customer_delivered",
                        "NLU": "shipping_recorded_in_carrier",
                    }
                    for p in self.record.package_ids:
                        if len (p.carrier_tracking_ref)==16:
                            try:
                                response = client.service.trackingByConsignment(p.carrier_tracking_ref)
                                if response:
                                    SummaryCodepack = response.statusCode
                                    mapped_states_pack = {
                                        "INT": "in_transit",
                                        "DEL": "customer_delivered",
                                        "EXC": "incidence",
                                        "000": "customer_delivered",
                                        "NLU": "shipping_recorded_in_carrier",
                                    }
                                    print ()
                                    p.delivery_state=mapped_states_pack.get(SummaryCodepack, "incidence")
                                    p.status_code=SummaryCodepack
                            except Exception:
                                pass
                    
                    return {
                        "status_code":SummaryCode,
                        "delivery_state": mapped_states.get(SummaryCode, "incidence"),
                        "tracking_state_history": SummaryCode,
                    }
                else:
                    return {
                        "status_code": "NLU" ,
                        "delivery_state": "shipping_recorded_in_carrier",
                        "tracking_state_history": ''}
            except Exception:
                return {
                    "status_code": "NLU" ,
                    "delivery_state": "shipping_recorded_in_carrier",
                    "tracking_state_history": ''}
                
        elif self.record.package_ids and (any (p.carrier_tracking_ref for p in self.record.package_ids)):
            for p in self.record.package_ids:
                    if len (p.carrier_tracking_ref)==16:
                        try:
                            response = client.service.trackingByConsignment(p.carrier_tracking_ref)
                            if response:
                                SummaryCodepack = response.statusCode
                                mapped_states_pack = {
                                    "INT": "in_transit",
                                    "DEL": "customer_delivered",
                                    "EXC": "incidence",
                                    "000": "customer_delivered",
                                    "NLU": "shipping_recorded_in_carrier",
                                }
                                print ()
                                p.delivery_state=mapped_states_pack.get(SummaryCodepack, "incidence")
                                p.status_code=SummaryCodepack
                        except Exception:
                                pass
            if (any (p.status_code for p in self.record.package_ids)):
                return {
                            "status_code":"Muli pack",
                            "delivery_state": "shipping_recorded_in_carrier",
                            "tracking_state_history": '',
                        }  
            else:
                return {
                            "status_code":"Reference invalide",
                            "delivery_state": "shipping_recorded_in_carrier",
                            "tracking_state_history": '',
                        }  
                
        else:
            return {
                        "status_code":"Not send",
                        "delivery_state": False,
                        "tracking_state_history": '',
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
