from odoo import api, fields,models, _
import requests
from requests.auth import HTTPBasicAuth
import json

class SUPPLIER_CHANGE(models.TransientModel):
    _name="supplier.change"
    _description = 'Import Account Data'
    def compute_supplier(self):
        active = self._context.get('active_id')

        sale_object = self.env['stock.move'].browse(active)
        return sale_object.supplier_old_id
    def compute_product(self):
        active = self._context.get('active_id')

        sale_object = self.env['stock.move'].browse(active)
        return sale_object.product_id
    def compute_supplier_id(self):
        active = self._context.get('active_id')

        sale_object = self.env['stock.move'].browse(active)
        if sale_object.supplier_old_id != False:
            search=self.env['res.partner'].search([('old_api_id','=',sale_object.supplier_old_id)])
            if search:
                return search[0].id
            else:
                return False
        else:
            return False
    product_id=fields.Many2one('product.product',default=compute_product,string="Produit")
    ancien_supplier=fields.Char('ID Ancien fournisseur',default=compute_supplier)
    new_supplier = fields.Char(related='new_supplier_id.old_api_id')
    new_supplier_id=fields.Many2one('res.partner','Nouveau fournisseur')
    ancien_supplier_id = fields.Many2one('res.partner','Ancien fournisseur',default=compute_supplier_id)

    def change_supplier(self):
        DROP_TYPE = self.env['stock.picking.type'].search([('name', '=', 'Dropshipping')], limit=1)
        DELIVERY_TYPE = self.env['stock.picking.type'].search([('name', '=', 'Delivery Orders')], limit=1)

        active = self._context.get('active_id')
        move_obj = self.env['stock.move'].browse(active)
        picking_obj = move_obj.picking_id
        product_obj = move_obj.product_id
        supplier_id = self.new_supplier_id
        supplier = self.new_supplier
        ref = picking_obj.sale_reference
        new_picking = False
        sale_obj = self.env['sale.order'].sudo().search([('old_id', '=', picking_obj.origin)], limit=1)
        picking_obj.do_unreserve()
        if product_obj.type=='product':
            if supplier in ['1', '0', False]:
                if picking_obj.picking_type_id.id == DROP_TYPE.id:
                    search_delivery = self.env['stock.picking'].sudo().search([('origin', '=', picking_obj.origin), ('picking_type_id', '=', DELIVERY_TYPE.id)], limit=1)
                    if not search_delivery:
                        # Create Delivery Order:
                        new_delivery = self.env['stock.picking'].sudo().create({
                            "partner_id": picking_obj.partner_id.id,
                            "picking_type_id": DELIVERY_TYPE.id,
                            "origin": picking_obj.origin,
                            "location_id":DELIVERY_TYPE.default_location_src_id.id,
                            "location_dest_id": DELIVERY_TYPE.default_location_dest_id.id,
                            "custom_sale_id": picking_obj.sale_id.id,
                            "scheduled_date": picking_obj.scheduled_date,
                            "sale_reference": ref
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
                        new_picking = search_delivery
            else:
                if picking_obj.picking_type_id.id == DELIVERY_TYPE.id:
                    search_drop = self.env['stock.picking'].sudo().search([('origin', '=', picking_obj.origin), ('picking_type_id', '=', DROP_TYPE.id)], limit=1)
                    if not search_drop:
                        new_drop = self.env['stock.picking'].sudo().create({
                            "partner_id": picking_obj.partner_id.id,
                            "picking_type_id": DROP_TYPE.id,
                            "origin": picking_obj.origin,
                            "location_id":DROP_TYPE.default_location_src_id.id,
                            "location_dest_id": DROP_TYPE.default_location_dest_id.id,
                            "custom_sale_id": picking_obj.sale_id.id,
                            "scheduled_date": picking_obj.scheduled_date,
                            "sale_reference": ref
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
                        new_picking = search_drop
        move_obj.supplier_old_id = supplier
        move_obj.custom_supplier_id = supplier_id
        try:
            picking_obj.action_confirm()
            picking_obj.action_assign()
        except:
            pass
        if new_picking:
            new_picking.action_confirm()
            new_picking.action_assign()

        if self.new_supplier == '1':
            url = 'http://141.94.171.159/crm/Companies/majStock2?iscron=cron'
            post_data = {"product_id": product_obj.old_id}
            response = requests.post(url, json=post_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))
        # raise Exception(response.content)
        
        # raise Exception("origin:",origin,"| detail_order_id:",str(detail_order_id),"| new_supplier:",self.new_supplier)
        url=  'http://141.94.171.159/crm/Propdetails/changeprov'

        url='http://141.94.171.159/crm/Propdetails/changeprov/%s/%s/%s/odoo' % (picking_obj.origin,str(move_obj.detail_order_id),self.new_supplier,)
        # raise Exception((origin,str(detail_order_id),self.new_supplier,))
        requests.post(url, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))

        if sale_obj:
            for line in sale_obj.order_line:
                if line.product_id.id == product_obj.id and line.custom_supplier_idd == int(self.ancien_supplier):
                    line.custom_supplier_idd = int(supplier)
                    line.custom_supplier_id = supplier_id
                    break
            if sale_obj.custom_type in ['1', '25'] or sale_obj.state=='sale':
                sale_obj.create_purchase_quotation()
        if not picking_obj.move_ids_without_package:
            picking_obj.sudo().unlink()
            if new_picking:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Create Receipt',
                    'res_model': 'stock.picking',
                    'res_id': new_picking.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                }
        else:
            if picking_obj.state not in ['done', 'cancel']:
                picking_obj.do_unreserve()
                picking_obj.action_confirm()
                picking_obj.action_assign()

    def change_supplier2(self):
        active=self._context.get('active_id')
        DROP = self.env['stock.picking.type'].search([('name', '=', 'Dropshipping')])
        DELIVERY = self.env['stock.picking.type'].search([('name', '=', 'Delivery Orders')])
        sale_object=self.env['stock.move'].browse(active)
        product=self.env['stock.move'].browse(active).product_id
        detail_order_id=self.env['stock.move'].browse(active).detail_order_id
        origin = self.env['stock.move'].browse(active).origin
        supplier_id=self.new_supplier_id
        print("Hellooooo testttt")
        print(len(sale_object.picking_id.move_ids_without_package.filtered(lambda r: r.supplier_old_id in ['0', '1',False] and r.product_id.type == 'product' and r.id != sale_object.id)))
        picking_ob=sale_object.picking_id
        
        if sale_object.picking_id.picking_type_id.name == 'Dropshipping'  and self.new_supplier not in ['0', '1', False] :
            sale_object.supplier_old_id = self.new_supplier
            sale_object.custom_supplier_id = supplier_id
        elif sale_object.picking_id.picking_type_id.name == 'Delivery Orders'  and self.new_supplier in ['0', '1', False] :
            sale_object.supplier_old_id = self.new_supplier
            sale_object.custom_supplier_id = supplier_id

        # create new DO and keep dropshiping
        elif sale_object.picking_id.picking_type_id.name=='Dropshipping' and sale_object.product_id.type=='product' and self.new_supplier in ['0','1',False] and len(sale_object.picking_id.move_ids_without_package.filtered(lambda r: r.supplier_old_id not in ['0','1',False] and r.product_id.type=='product' and r.id!= sale_object.id ))>0:
            sale_object.supplier_old_id=self.new_supplier
            sale_object.custom_supplier_id=supplier_id

            if self.env['stock.picking'].search([('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DELIVERY[0].id)]):
                stock = self.env['stock.picking'].search([('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DELIVERY[0].id)])

            else:
                stock_picking_vals = {
                    'partner_id': sale_object.picking_id.partner_id.id,
                    'picking_type_id': DELIVERY[0].id,
                    'origin': sale_object.picking_id.origin,
                    'location_id': DELIVERY[0].default_location_src_id.id,
                    'location_dest_id': DELIVERY[0].default_location_dest_id.id,
                    'custom_sale_id': sale_object.picking_id.sale_id.id,
                    # 'state': state,
                }
                stock = self.env['stock.picking'].create(stock_picking_vals)
            self._cr.execute("""UPDATE stock_move
                                                            SET picking_id=%s
                                                            WHERE id=%s """,
                             (stock.id, sale_object.id))
            self._cr.execute("""UPDATE stock_move_line
                                                          SET picking_id=%s
                                                          WHERE move_id=%s """,
                             (stock.id, sale_object.id))

        elif sale_object.picking_id.picking_type_id.name=='Delivery Orders' and sale_object.product_id.type=='product' and self.new_supplier not in ['0','1',False] and len(sale_object.picking_id.move_ids_without_package.filtered(lambda r: r.supplier_old_id in ['0','1',False] and r.product_id.type=='product' and r.id!= sale_object.id))>0:
            sale_object.supplier_old_id=self.new_supplier
            sale_object.custom_supplier_id = supplier_id
            print ("hi test 555")


            if self.env['stock.picking'].search([('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DROP[0].id)]):
                stock = self.env['stock.picking'].search([('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DROP[0].id)])
            else:
                stock_picking_vals = {
                    'partner_id': sale_object.picking_id.partner_id.id,
                    'picking_type_id': DROP[0].id,
                    'origin': sale_object.picking_id.origin,
                    'location_id': DROP[0].default_location_src_id.id,
                    'location_dest_id': DROP[0].default_location_dest_id.id,
                    'custom_sale_id': sale_object.picking_id.sale_id.id,
                    # 'state': state,
                }
                stock = self.env['stock.picking'].create(stock_picking_vals)
            print("hi test stock")
            print(stock)
            self._cr.execute("""UPDATE stock_move
                                                            SET picking_id=%s
                                                            WHERE id=%s """,
                             (stock.id, sale_object.id))
            self._cr.execute("""UPDATE stock_move_line
                                                          SET picking_id=%s
                                                          WHERE move_id=%s """,
                             (stock.id, sale_object.id))
        # keep dropshiping and change type
        elif sale_object.picking_id.picking_type_id.name=='Dropshipping' and sale_object.product_id.type=='product' and self.new_supplier in ['0','1',False] and len(sale_object.picking_id.move_ids_without_package.filtered(lambda r: r.supplier_old_id not in ['0','1',False] and r.product_id.type=='product' and r.id!= sale_object.id)) == 0:
            sale_object.supplier_old_id=self.new_supplier
            sale_object.custom_supplier_id = supplier_id

            if self.env['stock.picking'].search([('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DELIVERY[0].id)]):
                stock = self.env['stock.picking'].search([('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DELIVERY[0].id)])
                self._cr.execute("""UPDATE stock_move
                                                                            SET picking_id=%s
                                                                            WHERE id=%s """,
                                 (stock.id, sale_object.id))
                self._cr.execute("""UPDATE stock_move_line
                                                                          SET picking_id=%s
                                                                          WHERE move_id=%s """,
                                 (stock.id, sale_object.id))

                picking_ob.unlink()

            else:

                self._cr.execute("""UPDATE stock_picking
                                                                SET picking_type_id=%s
                                                                WHERE id=%s """,
                                 (DELIVERY[0].id, picking_ob.id))
        elif sale_object.picking_id.picking_type_id.name=='Delivery Orders' and sale_object.product_id.type=='product' and self.new_supplier not in ['0','1',False] and len(sale_object.picking_id.move_ids_without_package.filtered(lambda r: r.supplier_old_id in ['0','1',False] and r.product_id.type=='product' and r.id!= sale_object.id))==0:
            sale_object.supplier_old_id = self.new_supplier
            sale_object.custom_supplier_id = supplier_id
            print ("hello test vide")
            if self.env['stock.picking'].search(
                    [('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DROP[0].id)]):
                stock = self.env['stock.picking'].search(
                    [('origin', '=', sale_object.picking_id.origin), ('picking_type_id', '=', DROP[0].id)])
                print (stock)
                picking_obs = sale_object.picking_id
                sale_objt=sale_object.id
                self._cr.execute("""UPDATE stock_move
                                                                                            SET picking_id=%s
                                                                                            WHERE id=%s """,
                                 (stock.id, sale_objt))
                self._cr.execute("""UPDATE stock_move_line
                                                                                          SET picking_id=%s
                                                                                          WHERE move_id=%s """,
                                 (stock.id, sale_objt))

                print ('Hello sale object')
                print(picking_obs)
                picking_obs.unlink()

            else:

                self._cr.execute("""UPDATE stock_picking
                                                                                SET picking_type_id=%s
                                                                                WHERE id=%s """,
                                 (DROP[0].id, picking_ob.id))

        sale_order=self.env['sale.order'].search([('old_id','=',origin)],limit=1)
        """
        if self.new_supplier == '1':
            url = 'http://141.94.171.159/crm/Companies/majStock2?iscron=cron'
            post_data = {"product_id": product.old_id}
            response = requests.post(url, json=post_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))
        """
        # raise Exception(response.content)
        
        # raise Exception("origin:",origin,"| detail_order_id:",str(detail_order_id),"| new_supplier:",self.new_supplier)
        url=  'http://141.94.171.159/crm/Propdetails/changeprov'
        print ("Hellotest")
        print (str(detail_order_id))
        url='http://141.94.171.159/crm/Propdetails/changeprov/%s/%s/%s/odoo' % (origin,str(detail_order_id),self.new_supplier,)
        # raise Exception((origin,str(detail_order_id),self.new_supplier,))
        requests.post(url, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))


        if sale_order:
            for i in sale_order.order_line:
                if i.product_id==product:
                    i.custom_supplier_idd=int(self.new_supplier)
                    i.custom_supplier_id = supplier_id
            if sale_order.custom_type in ['1', '25'] or sale_order.state=='sale':
                sale_order.create_purchase_quotation()

        # raise Exception("test")
