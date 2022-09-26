from odoo import http
from odoo import _, SUPERUSER_ID
from odoo.http import request
import json
import werkzeug
from datetime import datetime
import base64
import os

class ScanController(http.Controller):

    @http.route('/picking/validate/<string:barcode>', type='http', auth='none')
    def pickingvalidate(self, barcode):
        """ validate picking. """
        env = request.env(user=SUPERUSER_ID, su=True)
        pickings = env['stock.picking'].sudo().search([('id', '=', barcode)])
        if pickings:
            trouve = 0
            for p in pickings:
                trouve = 1
                if p.state not in ['done']:

                    p.action_confirm()
                    p.action_assign()
                    stock_move_backorder = None
                    backorder_list_move = []
                    for item in p.move_ids_without_package:
                        product = env['product.product'].sudo().search([('id', '=', item.product_id.id)])
                        print(product[0].old_id, '|', product[0].qty_not_validated_yet, '|', product[0].qty_available, '|', item.state)

                        if product[0].qty_available <= 0:
                            print("case 1", item.product_id.old_id)
                            backorder_list_move.append({
                                "product_id": item.product_id.id,
                                "product_uom": item.product_uom.id,
                                "quantity_done": 0,
                                "forecast_availability": 0,
                                "product_uom_qty": item.product_uom_qty,
                                "name": item.name,
                                "location_id": item.location_id.id,
                                "location_dest_id": item.location_dest_id.id
                            })
                            item.product_uom_qty = 0
                            item.forecast_availability = 0
                            item.quantity_done = 0
                        else:
                            stock_reel = product[0].qty_available - product[0].qty_not_validated_yet
                            if stock_reel <= 0 and item.state != "assigned":
                                print("case 2", item.product_id.old_id)
                                backorder_list_move.append({
                                    "product_id": item.product_id.id,
                                    "product_uom": item.product_uom.id,
                                    "quantity_done": 0,
                                    "forecast_availability": 0,
                                    "product_uom_qty": item.product_uom_qty,
                                    "name": item.name,
                                    "location_id": item.location_id.id,
                                    "location_dest_id": item.location_dest_id.id
                                })
                                item.product_uom_qty = 0
                                item.forecast_availability = 0
                                item.quantity_done = 0
                            else:
                                if stock_reel >= item.product_uom_qty or item.state == "assigned":
                                    print("case 3", item.product_id.old_id)
                                    # done with demand
                                    item.forecast_availability = item.product_uom_qty
                                    item.quantity_done = item.product_uom_qty
                                else:
                                    print("case 4", item.product_id.old_id)
                                    diff = item.product_uom_qty - stock_reel
                                    backorder_list_move.append({
                                        "product_id": item.product_id.id,
                                        "product_uom": item.product_uom.id,
                                        "quantity_done": 0,
                                        "forecast_availability": 0,
                                        "product_uom_qty": diff,
                                        "name": item.name,
                                        "location_id": item.location_id.id,
                                        "location_dest_id": item.location_dest_id.id
                                    })
                                    item.product_uom_qty = stock_reel
                                    item.forecast_availability = stock_reel
                                    item.quantity_done = stock_reel
                    if len(backorder_list_move) > 0:
                        stock_move_backorder = env['stock.move'].sudo().create(backorder_list_move)
                    backorder_check = "sans backorder"
                    if stock_move_backorder != None:
                        backorder = env["stock.picking"].sudo().create(
                            {"partner_id": (p.partner_id.id,), "picking_type_id": (p.picking_type_id.id,),
                             "location_dest_id": (p.location_dest_id.id,), "location_id": (p.location_id.id,),
                             "backorder_id": p.id, "origin": p.origin})
                        for item in stock_move_backorder:
                            item.picking_id = backorder
                        backorder.move_ids_without_package = stock_move_backorder
                        v = backorder.action_confirm()
                        backorder.action_toggle_is_locked()
                        backorder_check = "avec backorder"
                    p.button_validate()

                    data = {
                        'status': 200,
                        'message': 'Vous avez validé le transfert( ' + backorder_check + ' )',
                    }

                    return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

                else:
                    data = {
                        'status': 208,
                        'message': 'Le transfert est déja validé',
                    }

                    return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
            if trouve == 0:
                data = {
                    'status': 404,
                    'message': 'Le transfert n\'existe pas',
                }
                return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

        else:
            data = {
                'status': 404,
                'message': 'Le transfert n\'existe pas',
            }
            return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/picking/show/<string:barcode>', type='http', auth='none')
    def pickingshow(self, barcode):
        """ validate picking. """

        env = request.env(user=SUPERUSER_ID, su=True)
        list = barcode.split('-')
        pickings = env['stock.picking'].sudo().search([('origin', '=', list[2])])
        for p in pickings:
            if p.picking_type_id.sequence_code == list[1]:
                data = {
                    "id": p.id
                }

                return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/picking/get-products/<string:barcode>', type='http', auth='none')
    def getPickingProducts(self, barcode):
        env = request.env(user=SUPERUSER_ID, su=True)
        query = """select id from stock_move_line where picking_id=%s
        """
        env.cr.execute(query, (barcode,))
        result = env.cr.fetchall()
        ids = [x[0] for x in result]
        # move_lines = env['stock.move.line'].sudo().search([('picking_id', '=', barcode)])
        move_lines = env['stock.move.line'].sudo().browse(ids)
        # raise Exception(move_lines)
        list_return = []
        for move in move_lines:
            if move.product_id.product_tmpl_id.tracking == "serial":
                serial_number = ""
                if move.lot_id:
                    serial_number = move.lot_id.name
                list_return.append({
                    "picking_id": barcode,
                    "product_id": move.product_id.id,
                    "serial_number": serial_number,
                    "product_name": move.product_id.product_tmpl_id.name,
                    "move_id": move.id
                })
        return request.make_response(json.dumps(list_return), headers=[('Content-Type', 'application/json')])

    @http.route('/picking/post-products/<string:barcode>', type='json', auth='public', methods=["POST"])
    def postPickingProducts(self, barcode):
        data = request.jsonrequest['params']['data']
        env = request.env(user=SUPERUSER_ID, su=True)
        print(data)
        for item in data:
            move = env['stock.move.line'].sudo().browse(int(item['move_id']))
            lot = env['stock.production.lot'].sudo().search([('name', '=', item['serial_number']), ('product_id', '=', item['product_id'])])
            #try:
            if lot:
                move.write({"lot_id": lot.id})
            else:
                lot_id = env['stock.production.lot'].sudo().create({
                    "name": item['serial_number'],
                    "product_id": int(item["product_id"]),
                    "product_uom_id": move.product_id.product_tmpl_id.uom_id.id,
                    "company_id": 1})
                move.write({"lot_id": lot_id.id})
            """except:
                return {
                    'status': 404,
                    'message': 'Il y\'a une erreur!',
                }"""

        return {
            'status': 200,
            "message": "Les numéros de séries sont ajoutés!"
        }

    @http.route('/picking/show/<string:barcode>', type='http', auth='none')
    def pickingshow(self, barcode):
        """ validate picking. """
        print ('hi')
        env = request.env(user=SUPERUSER_ID, su=True)
        list = barcode.split('-')
        pickings = env['stock.picking'].sudo().search([('origin', '=', list[2])])
        for p in pickings:
            if p.picking_type_id.sequence_code == list[1]:
                data = {
                    "id": p.id
                }

                return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    @http.route('/picking/get-new-id/<string:barcode>', type='http', auth='none')
    def getNewPickingID(self, barcode):
        env = request.env(user=SUPERUSER_ID, su=True)
        new_barcode = barcode
        query = f"""select max(picking_new_id)
                    from stock_picking_mapping
                    where mapping_str like '%{new_barcode}%'"""

        env.cr.execute(query)
        data = env.cr.dictfetchall()
        if len(data) > 0:
            if data[0]['max'] is not None:
                new_barcode = data[0]['max']

        return request.make_response(json.dumps({"new_id": new_barcode}), headers=[('Content-Type', 'application/json')])

    @http.route('/picking/test', type='http', auth='none')
    def test_test(self):
        query = """select picking_old_id from stock_picking_mapping where picking_old_id=1111111111"""
        env = request.env(user=SUPERUSER_ID, su=True)
        env.cr.execute(query)
        data = env.cr.fetchall()
        return request.make_response(json.dumps({"data": data}), headers=[('Content-Type', 'application/json')])
    
    @http.route('/picking/carriere-tnt/<string:barcode>', type='http', auth='none')
    def sendCarrierTNT(self, barcode):
        env = request.env(user=SUPERUSER_ID, su=True)
        pickings = env['stock.picking'].sudo().search([('id', '=', barcode)])
        if pickings:
            for p in pickings:
                try:
                    p.write({"carrier_id": 2})
                    p.carrier_id.send_shipping(pickings)
                    p.tracking_send()
                    env['stock.picking'].action_all_picking(p)
                    return request.make_response(
                        json.dumps({"status": 200, "message": "Shippement Order Printed. Check Printer!"}),
                        headers=[('Content-Type', 'application/json')])
                except:
                    return request.make_response(
                        json.dumps({"status": 400, "message": "Error While Creaing Shippement Order!"}),
                        headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(
                json.dumps({"status": 404, "message": "Picking Not Found!"}),
                headers=[('Content-Type', 'application/json')])

    @http.route('/picking/carriere-gls/<string:barcode>', type='http', auth='none')
    def sendCarrierGLS(self, barcode):
        env = request.env(user=SUPERUSER_ID, su=True)
        carrier = env['stock.carrier.transfer'].browse([40])
        # p.write({"carrier_id": carrier.carrier_id.id})
        pickings = env['stock.picking'].sudo().search([('id', '=', barcode)])
        if pickings:
            for p in pickings:
                try:
                    p.write({"carrier_id": 40})
                    p.carrier_id.send_shipping(pickings)
                    p.tracking_send()
                    env['stock.picking'].action_all_picking(p)
                    return request.make_response(
                        json.dumps({"status": 200, "message": "Shippement Order Sended To GLS!"}),
                        headers=[('Content-Type', 'application/json')])
                except:
                    return request.make_response(
                        json.dumps({"status": 400, "message": "Error While Creaing Shippement Order!"}),
                        headers=[('Content-Type', 'application/json')])
        else:
            return request.make_response(
                json.dumps({"status": 404, "message": "Picking Not Found!"}),
                headers=[('Content-Type', 'application/json')])

    @http.route('/picking/upload-image/<string:barcode>', type='http', auth='public', methods=["POST"], csrf=False)
    def uploadImage(self, barcode,**kw):
        env = request.env(user=SUPERUSER_ID, su=True)
        imageFile = kw['image']
        extension = str(werkzeug.utils.secure_filename(imageFile.filename)).split('.')[1]
        fileName = datetime.now().strftime("upload__%Y-%m-%d__%H-%M.") + extension
        imageFile.save("/opt/odoo/addons_alfa/de_alfa_webservice_scan/static/" + fileName)
        picking = env['stock.picking'].sudo().browse(int(barcode))
        with open("/opt/odoo/addons_alfa/de_alfa_webservice_scan/static/" + fileName, "rb") as f:
            file = env['ir.attachment'].create({
                'name': fileName,
                'type': 'binary',
                # 'datas': base64.encodebytes(imageFile.read()),
                'datas': base64.encodebytes(f.read()),
                'res_model': "stock.picking",
                'res_id': picking.id,
                'index_content': "image",
            })

        os.remove("/opt/odoo/addons_alfa/de_alfa_webservice_scan/static/" + fileName)

        return request.make_response(
            json.dumps({"status": 200, "message": "Image Uploaded"}),
            headers=[('Content-Type', 'application/json')])