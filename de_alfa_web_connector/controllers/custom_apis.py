import odoo.http as http
from odoo.http import request
from odoo import _, SUPERUSER_ID


class SaleOrdersCustomController(http.Controller):

    @http.route('/sale-order/create', type='json', auth='public', methods=["POST"])
    def sale_order_create(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        sale_order = env['sale.order'].create_update_sales([data])
        return {
            'status': 200,
            "message": "Sale Order Created/Updated!"
        }
    
    @http.route('/sale-order/delete', type='json', auth='public', methods=["POST"])
    def sale_order_delete(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        order_id = data['Order']['order_id']
        sale_order = env['sale.order'].sudo().search([('old_id', '=', order_id)], limit=1)
        picking = env['stock.picking'].sudo().search([('sale_id', '=', sale_order.id)])
        
        picking.sudo().action_cancel()
        sale_order.sudo().action_cancel()
        picking.sudo().unlink()
        sale_order.sudo().unlink()
        return {
            'status': 200,
            "message": "Sale Order Deleted!"
        }

class SupplierCustomController(http.Controller):

    @http.route('/supplier/update', type='json', auth='public', methods=["POST"])
    def changeSupplierFromCrm(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        pickings = env['stock.picking'].sudo().search([('origin', '=', data['order_id'])])
        for picking in pickings:
            moves = picking.move_ids_without_package
            for move in moves:
                if data['product_id'] == move.product_id.old_id:
                    # supplier = env['res_partner'].sudo().search([('old_api_id', '=', data['new_supplier_id'])])
                    move.sudo().write({"supplier_old_id": data['new_supplier_id']})
                    break
        return {
            'status': 200,
            "message": "Supplier Updated!"
        }
    
    @http.route('/supplier/update/all', type='json', auth='public', methods=["POST"])
    def changeAllSupplierFromCrm(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        pickings = env['stock.picking'].sudo().search([('origin', '=', data['order_id'])] ) 
        
        DROP_TYPE = env['stock.picking.type'].search([('name', '=', 'Dropshipping')], limit=1)
        DELIVERY_TYPE = env['stock.picking.type'].search([('name', '=', 'Delivery Orders')], limit=1)
        for picking_obj in pickings:
            ref = picking_obj.sale_reference
            sale_obj = env['sale.order'].sudo().search([('old_id', '=', picking_obj.origin)], limit=1)
            supplier_id = int(data['supplier_id']) 
            supplier = data['supplier_id']
            for move_obj in picking_obj.move_ids_without_package:
                product_obj = move_obj.product_id

                if product_obj.type=='product':
                    if supplier in ['1', '0', False]:
                        if picking_obj.picking_type_id.id == DROP_TYPE.id:
                            search_delivery = env['stock.picking'].sudo().search([('origin', '=', picking_obj.origin), ('picking_type_id', '=', DELIVERY_TYPE.id)], limit=1)
                            if not search_delivery:
                                # Create Delivery Order:
                                new_delivery = env['stock.picking'].sudo().create({
                                    "partner_id": picking_obj.partner_id.id,
                                    "picking_type_id": DELIVERY_TYPE.id,
                                    "origin": picking_obj.origin,
                                    "location_id":DELIVERY_TYPE.default_location_src_id.id,
                                    "location_dest_id": DELIVERY_TYPE.default_location_dest_id.id,
                                    "custom_sale_id": picking_obj.sale_id.id,
                                    "scheduled_date": picking_obj.scheduled_date,
                                    "sale_reference": ref
                                })
                                move_obj.sudo().write({"picking_id": new_delivery.id})
                                new_picking = new_delivery
                            else:
                                move_obj.sudo().write({"picking_id": search_delivery.id})
                    else:
                        if picking_obj.picking_type_id.id == DELIVERY_TYPE.id:
                            search_drop = env['stock.picking'].sudo().search([('origin', '=', picking_obj.origin), ('picking_type_id', '=', DROP_TYPE.id)], limit=1)
                            if not search_drop:
                                new_drop = env['stock.picking'].sudo().create({
                                    "partner_id": picking_obj.partner_id.id,
                                    "picking_type_id": DROP_TYPE.id,
                                    "origin": picking_obj.origin,
                                    "location_id":DROP_TYPE.default_location_src_id.id,
                                    "location_dest_id": DROP_TYPE.default_location_dest_id.id,
                                    "custom_sale_id": picking_obj.sale_id.id,
                                    "scheduled_date": picking_obj.scheduled_date,
                                    "sale_reference": ref
                                })
                                move_obj.sudo().write({"picking_id": new_drop.id})
                                new_picking = new_drop
                            else:
                                move_obj.sudo().write({"picking_id": search_drop.id})
                move_obj.supplier_old_id = supplier
                move_obj.custom_supplier_id = supplier_id
                if sale_obj:
                    for line in sale_obj.order_line:
                        if line.product_id.id == product_obj.id:
                            line.custom_supplier_idd = int(supplier)
                            line.custom_supplier_id = supplier_id
                            break
                    if sale_obj.custom_type in ['1', '25'] or sale_obj.state=='sale':
                        sale_obj.create_purchase_quotation()
        for picking_obj in pickings:
            if not picking_obj.move_ids_without_package:
                picking_obj.sudo().unlink()
        return {
            'status': 200,
            "message": "Supplier Updated!"
        }

class ResPartnerCustomController(http.Controller):

    @http.route('/partner/create', type='json', auth='public', methods=["POST"])
    def partner_create(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        sale_order = env['res.partner'].create_update_customers([data])
        return {
            'status': 200,
            "message": "Partner Created/Updated!"
        }