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
            supplier = str(data['supplier_id'])
            new_picking = False
            picking_obj.do_unreserve()
            for move_obj in picking_obj.move_ids_without_package:
                product_obj = move_obj.product_id
                if product_obj.old_id == data['product_id']:
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
                                        "sale_reference": ref,
                                        "state": "draft"
                                    })
                                    move_obj.sudo().write({
                                        "picking_id": new_delivery.id,
                                        "state": "draft",
                                        "location_id": new_delivery.location_id.id
                                    })
                                    new_picking = new_delivery
                                else:
                                    search_delivery.do_unreserve()
                                    move_obj.sudo().write({
                                        "picking_id": search_delivery.id,
                                        "location_id": search_delivery.location_id.id,
                                        "state": "draft"
                                    })
                                    try:
                                        search_delivery.action_confirm()
                                        search_delivery.action_assign()
                                    except:
                                        pass
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
                                        "sale_reference": ref,
                                        "state": "draft"
                                    })
                                    move_obj.sudo().write({
                                        "picking_id": new_drop.id,
                                        "state": "draft",
                                        "location_id": new_drop.location_id.id
                                    })
                                    new_picking = new_drop
                                else:
                                    search_drop.do_unreserve()
                                    move_obj.sudo().write({
                                        "picking_id": search_drop.id,
                                        "location_id": search_drop.location_id.id,
                                        "state": "draft"
                                    })
                                    try:
                                        search_drop.action_confirm()
                                        search_drop.action_assign()
                                    except:
                                        pass
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
            try:
                picking_obj.action_confirm()
                picking_obj.action_assign()
            except:
                pass
            if new_picking:
                new_picking.action_confirm()
                new_picking.action_assign()
        for picking_obj in pickings:
            if not picking_obj.move_ids_without_package:
                picking_obj.sudo().unlink()
            else:
                if picking_obj.state not in ['done', 'cancel']:
                    picking_obj.do_unreserve()
                    picking_obj.action_confirm()
                    picking_obj.action_assign()
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