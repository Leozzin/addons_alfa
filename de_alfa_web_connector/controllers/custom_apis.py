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