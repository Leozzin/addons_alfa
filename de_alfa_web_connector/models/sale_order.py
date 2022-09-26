import os
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging
from requests.auth import HTTPBasicAuth
from ftplib import FTP



class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'
    
    def download_ftp_tnt(self,A,Doc):
        ftp = FTP('ftp.cluster017.ovh.net', 'alfaprinfm-tnt', 'Alfa2021')
        try:
            LocalDestinationPath =os.path.join(r'/opt/odoo/addons_alfa/de_alfa_ws_tnt/static/description/files/tnt',Doc)
            if not os.path.exists(LocalDestinationPath):
                os.mkdir(LocalDestinationPath)
            os.chdir(LocalDestinationPath)
            with open( A, 'wb' ) as file :
                ftp.retrbinary('RETR %s' % A, file.write)
       
        except:
            print ("Error")
    
    def download_ftp(self):
        folder=""
        ftp = FTP('ftp.cluster017.ovh.net', 'alfaprinfm-tnt', 'Alfa2021')
        try:
            LocalDestinationPath =os.path.join(r'/opt/odoo/addons_alfa/de_alfa_ws_tnt/files/tnt','test')
            if not os.path.exists(LocalDestinationPath):
                os.mkdir(LocalDestinationPath)
            os.chdir(LocalDestinationPath)
            with open( '911903700003624h.pdf', 'wb' ) as file :
                ftp.retrbinary('RETR %s' % '9119037000036240.pdf', file.write)
       
            
        except:
            print ("Error")
    
    def compute_category(self):
        for i in self.env['product.category'].search([]):
            i._compute_complete_name()

    def correction_service(self):
        self._cr.execute("""select id,name,delivery_status,state from sale_order where id in 

                         (select order_id from sale_order_line where name not like '%%Extension%%' and name not like '%%extension%%' and name not like '%%Livraison%%' and name not like '%%Installation%%'  and name not like '%%delivery%%' and product_id in (select id from product_product where product_tmpl_id in (select id from product_template where type ='service')))""",
                         )
        for row in self._cr.dictfetchall():
            if row['id']:
                sale=self.env['sale.order'].browse(row['id'])
                print ("sallllle")
                print (sale.name)
                sale.picking_ids.unlink()
                for i in sale.order_line:
                    if i.product_id.type=='service' and ('Extension' not in i.name) and ('extension' not in i.name) and ('Livraison' not in i.name) and ('delivery' not in i.name):
                        i.product_id.type="product"
                        i.product_id.product_tmpl_id.type = "product"

                if sale.custom_type in ['1','25']:

                    sale.create_sale_operations()



    def correction_product(self):
        compt=0
        for p in self.env['stock.quant'].search([('location_id','=',8)]):
            compt=compt+1
            print(compt)
            qty=sum(i.product_uom_qty  for i in self.env['stock.move.line'].search([('product_id','=',p.product_id.id),('state','=','assigned'),('location_id','=',8)]))
            p.reserved_quantity=qty
    def correction_picking(self):
        compt=1
        for record in self.env['sale.order'].search([('custom_type', 'in', ['1', '25']),('delivery_status', 'in', [0,1,3])]):
            compt=compt+1
            print (compt)
            if record.delivery_status==1:
                for picking_id in record.picking_ids:
                    picking_id.action_confirm()
                    for i in picking_id.move_ids_without_package:
                        i.quantity_done = i.product_uom_qty
                        if i.product_uom_qty <= 0:
                            i.product_uom_qty = 1
                            i.quantity_done = 1

                    picking_id.button_validate()
            else:

                for picking_id in record.picking_ids:

                    picking_id.state='draft'
                    for i in picking_id.move_ids_without_package:
                        i.state='draft'

                    picking_id.action_confirm()
                    picking_id.action_assign()






    def correction_quantity(self):
        for record in self.env['stock.quant'].search([]):
            record._compute_inventory_quantity()

    def correction_purchase(self):
        comp = 0
        for record in self.env['sale.order'].search(
                [('is_update', '=', False), ('custom_type', 'in', ['1', '25'])],
                limit=10000):
            comp = comp + 1
            print("compteur")
            print(comp)

            for i in record.order_line:
                if not i.custom_supplier_id and i.custom_supplier_idd:
                    search = self.env['res.partner'].search([('old_api_id', '=', str(i.custom_supplier_idd))])
                    if search:
                        i.custom_supplier_id = search[0].id
            if not record.picking_ids:
                record.create_sale_operations()
                record.is_update = True
            if not record.purchase_order_ids:
                record.create_purchase_quotation()
                record.is_update = True



    def correction_delivery(self):
        comp = 0
        for record in self.env['sale.order'].search(['|', ('custom_type', 'in', ['1', '25']), ('state', '=', 'sale')],
                                                    limit=1000):
            comp = comp + 1
            print("compteurtest")
            print(comp)

            record.create_sale_operations()

    def correction_detail(self):
        sql = """select propal_id,product_id,propdetail_id  from detail_order
                """
        self.env.cr.execute(sql)
        product_ids = self.env.cr.fetchall()
        compt = 1
        for ls in product_ids:
            compt = compt + 1
            print(compt)
            self._cr.execute("""UPDATE sale_order_line
                                                    SET detail_order_id=%s
                                                    WHERE custom_order_id=%s and custom_product_id=%s   """,
                             (ls[2], str(ls[0]), str(ls[1])))

    def correction_stock(self):
        compt = 0
        compt_line = 0
        for i in self.env['stock.move'].search([]):
            compt = compt + 1
            print(compt)
            i.picking_type_id = i.picking_id.picking_type_id
            i.location_id = i.picking_id.location_id
            i.location_dest_id = i.picking_id.location_dest_id
            if i.picking_id.state == 'done':
                # i.quantity_done=i.product_uom_qty
                i.state = i.picking_id.state
        # for i in self.env['stock.move.line'].search([]):
        #     compt_line = compt_line + 1
        #     print(compt_line)
        #     # i.picking_type_id=i.picking_id.picking_type_id
        #     if i.picking_id.location_id:
        #         i.location_id = i.picking_id.location_id
        #     if i.picking_id.location_dest_id:
        #         i.location_dest_id = i.picking_id.location_dest_id
        #     if i.picking_id.state=='done':
        #         i.qty_done=i.product_uom_qty
        #         i.state=i.picking_id.state

    def script_update_stock(self):
        for i in self.env['stock.picking'].search([]):
            i.compute_name()

    def script_update(self):
        DROP = self.env['stock.picking.type'].search([('name', '=', 'Dropshipping')])
        DELIVERY = self.env['stock.picking.type'].search([('name', '=', 'Delivery Orders')])
        for i in self.env['stock.picking'].search([]):
            if i.picking_type_id.name in ['Annulée', 'Livrée', 'Traitée']:
                if i.picking_type_id.name == 'Annulée':
                    state = 'cancel'
                elif i.picking_type_id.name == 'Livrée':
                    state = 'done'
                elif i.picking_type_id.name == 'Traitée':
                    state = 'assigned'

                if all(l.supplier_old_id in ['0', '1', False] for l in i.move_ids_without_package):
                    self._cr.execute("""UPDATE stock_picking
                                        SET picking_type_id=%s,state=%s
                                        WHERE id=%s """,
                                     (DELIVERY[0].id, state, i.id))

                elif all(l.supplier_old_id not in ['0', '1', False] for l in i.move_ids_without_package):
                    self._cr.execute("""UPDATE stock_picking
                                        SET picking_type_id=%s,state=%s
                                        WHERE id=%s """,
                                     (DROP[0].id, state, i.id))
            elif i.picking_type_id.name in ['Fournisseur_ID_NULL', 'Dropshipping', 'Delivery Orders']:

                if all(l.supplier_old_id in ['0', '1', False] for l in i.move_ids_without_package):
                    self._cr.execute("""UPDATE stock_picking
                                                                    SET picking_type_id=%s
                                                                    WHERE id=%s """,
                                     (DELIVERY[0].id, i.id))

                elif all(l.supplier_old_id not in ['0', '1', False] for l in i.move_ids_without_package):
                    self._cr.execute("""UPDATE stock_picking
                                                                                        SET picking_type_id=%s
                                                                                        WHERE id=%s """,
                                     (DROP[0].id, i.id))

    def script_update_mixte(self):
        DROP = self.env['stock.picking.type'].search([('name', '=', 'Dropshipping')])
        DELIVERY = self.env['stock.picking.type'].search([('name', '=', 'Delivery Orders')])
        for i in self.env['stock.picking'].search([]):
            stock_move_vals_service = []
            if i.picking_type_id.name in ['Annulée', 'Livrée', 'Traitée']:
                if i.picking_type_id.name == 'Annulée':
                    state = 'cancel'
                elif i.picking_type_id.name == 'Livrée':
                    state = 'done'
                elif i.picking_type_id.name == 'Traitée':
                    state = 'assigned'
                if any(l.supplier_old_id in ['0', '1', False] and l.product_id.type == 'product' for l in
                       i.move_ids_without_package):
                    stock_picking_vals = {
                        'partner_id': i.partner_id.id,
                        'picking_type_id': DELIVERY[0].id,
                        'origin': i.origin,
                        'location_id': DELIVERY[0].default_location_src_id.id,
                        'location_dest_id': DELIVERY[0].default_location_dest_id.id,
                        'custom_sale_id': i.sale_id,
                        # 'state': state,
                    }
                    if self.env['stock.picking'].search(
                            [('origin', '=', i.origin), ('picking_type_id', '=', DELIVERY[0].id)]):
                        stock = self.env['stock.picking'].search(
                            [('origin', '=', i.origin), ('picking_type_id', '=', DELIVERY[0].id)], limit=1)
                    else:
                        stock = self.env['stock.picking'].create(stock_picking_vals)

                        self._cr.execute("""UPDATE stock_picking
                                                                        SET state=%s
                                                                        WHERE id=%s """,
                                         (state, stock.id))

                    for ligne in i.move_ids_without_package:
                        if ligne.supplier_old_id in ['0', '1', False] and ligne.product_id.type == 'product':
                            self._cr.execute("""UPDATE stock_move
                                                SET picking_id=%s
                                                WHERE id=%s """,
                                             (stock.id, ligne.id))
                            self._cr.execute("""UPDATE stock_move_line
                                              SET picking_id=%s
                                              WHERE move_id=%s """,
                                             (stock.id, ligne.id))
                        elif ligne.product_id.type == 'service':
                            ligne.copy().update({'picking_id': stock.id})
                self._cr.execute("""UPDATE stock_picking
                                                        SET picking_type_id=%s,state=%s
                                                        WHERE id=%s """,
                                 (DROP[0].id, state, i.id))

            if i.picking_type_id.name in ['Dropshipping']:
                if any(l.supplier_old_id in ['0', '1', False] and l.product_id.type == 'product' for l in
                       i.move_ids_without_package):
                    stock_picking_vals = {
                        'partner_id': i.partner_id.id,
                        'picking_type_id': DELIVERY[0].id,
                        'origin': i.origin,
                        'location_id': DELIVERY[0].default_location_src_id.id,
                        'location_dest_id': DELIVERY[0].default_location_dest_id.id,
                        'custom_sale_id': i.sale_id,
                        # 'state': state,
                    }
                    if self.env['stock.picking'].search(
                            [('origin', '=', i.origin), ('picking_type_id', '=', DELIVERY[0].id)]):
                        stock = self.env['stock.picking'].search(
                            [('origin', '=', i.origin), ('picking_type_id', '=', DELIVERY[0].id)])
                    else:
                        stock = self.env['stock.picking'].create(stock_picking_vals)

                        self._cr.execute("""UPDATE stock_picking
                                                                        SET state=%s
                                                                        WHERE id=%s """,
                                         (i.state, stock.id))
                    for ligne in i.move_ids_without_package:
                        if ligne.supplier_old_id in ['0', '1', False] and ligne.product_id.type == 'product':
                            self._cr.execute("""UPDATE stock_move
                                                SET picking_id=%s
                                                WHERE id=%s """,
                                             (stock.id, ligne.id))
                            self._cr.execute("""UPDATE stock_move_line
                                                                            SET picking_id=%s
                                                                            WHERE move_id=%s """,
                                             (stock.id, ligne.id))
                        elif ligne.product_id.type == 'service':
                            ligne.copy().update({'picking_id': stock.id})

    def create_purchase_order_from_sale_modified(self):
        sql = """ select max(custom_modified) from purchase_order """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()

        if result[0]:
            sql = """select id from sale_order where (custom_type in ('1','25') or state='sale') 
                and custom_modified > '""" + str(result[0]) + """'
                """
            self.env.cr.execute(sql)
            orders = self.env.cr.fetchall()
            
            order_ids = self.search([('id', 'in', orders)])
            print(order_ids)

            for order_id in order_ids:
                order_id.create_purchase_quotation()

    def create_purchase_order_from_sale(self):
        """commented code, was used for (moving all sales into purchase for first time)"""
        #         sql = """select id from sale_order where (custom_type in ('1','25') or state='sale')
        #                 and is_converted_to_purchase = False limit 1000"""
        #         self.env.cr.execute(sql)
        #         orders = self.env.cr.fetchall()
        #
        #         order_ids = self.search([('id','in',orders)])
        #         print(order_ids)
        #
        #         for order_id in order_ids:
        #             order_id.create_purchase_quotation()

        self.create_purchase_order_from_sale_modified()

    def create_purchase_quotation(self):
        PurchaseOrder = self.env['purchase.order']

        if self.old_id:
            purchase_exists = PurchaseOrder.search([('origin','=',self.old_id)])

            if purchase_exists:
                purchase_exists.button_unlock()
                purchase_exists.button_cancel()
                purchase_exists.unlink()

            sql = """
                select distinct custom_supplier_id from sale_order_line 
                where custom_supplier_id is not null  and custom_supplier_idd not in (1,0)  and order_id = """ + str(
                self.id)
            self.env.cr.execute(sql)
            vendors = self.env.cr.fetchall()

            if vendors != []:
                # sales_ids = []

                for vendor_id in vendors:
                    provider_ref_list = []
                    purchase_line_vals = []
                    vendor_id = vendor_id[0]

                    print('---------vendor------', vendor_id)
                    for line in self.order_line:
                        if line.custom_supplier_id.id == vendor_id:
                            purchase_line_vals.append((0, 0, {
                                'detail_order_id': line.detail_order_id,
                                'name': line.name,
                                'product_id': line.product_id.id,
                                'product_qty': line.product_uom_qty,
                                'product_uom': line.product_uom.id,
                                'price_unit': line.custom_supplier_price and line.custom_supplier_price,
                                'provider_ref': line.provider_ref,
                            }))

                    if self.date_offset_format:
                        order_date = self.date_offset_format
                    else:
                        order_date = self.custom_order_date

                    purchase_vals = {
                        'partner_id': vendor_id,
                        'order_line': purchase_line_vals,
                        'sale_order_id': self.id,
                        'origin': self.old_id,
                        'user_id': self.user_id.id,
                        'date_order': order_date,
                        'date_planned': None,
                        'custom_modified': self.custom_modified,
                    }

                    purchase = self.env['purchase.order'].create(purchase_vals)
                    print("create purchase")
                    print(purchase.id)
                    # sales_ids.append(purchase.id)

                    if self.delivery_status not in (0, 3):
                        purchase.state = 'done'
                        # purchase.button_confirm()

                self.is_converted_to_purchase = True
                # self.update({
                #     'is_converted_to_purchase': True,
                #     # 'purchase_order_ids': sales_ids,
                #     })
    
    def import_sale_avoirs_cron_modified(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

        sql = """ select max(custom_modified) from sale_order where custom_type not in ('0','1','25') """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()

        if result[0]:
            formatted_datetime = str(result[0].date()) + "_" + str(result[0].strftime("%H")) + "@" + str(
                result[0].strftime("%M")) + "@" + str(result[0].strftime("%S"))
            print(formatted_datetime)
            formatted_datetime = "2022-09-07_00@00@00"
            # raise UserError(formatted_datetime)
            # url = "http://141.94.171.159/crm/Companies/getAvoirsToOdoo/" + str(formatted_datetime) + "/iscron=cron"
            url = "http://141.94.171.159/crm/Companies/getAvoirsToOdoo/" + str(formatted_datetime) + "/iscron=cron"
            # url="http://141.94.171.159/crm/Companies/getAvoirsToOdoo/part19/iscron=cron"
            # url = "http://141.94.171.159:8080/crm/companies/getAvoirsToOdoo"

            data = json.loads(requests.get(url, auth=(username, password)).content)
            print('---sale data---')
            print(data)

            self.create_update_sales(data)
            self.create_tasks(data)
            # try:
            #     self.create_update_sales(data)
            # except:
            #     raise Exception('error in create update sales')
            # try:
            #     self.create_tasks(data)
            # except:
            #     raise Exception('error in create update tickets')

    def create_tasks(self, data):
        list_tasks = []
        for task in data:
            try:
                helpdesk_task = self.env['helpdesk.ticket'].sudo().search([('number', '=', task['Order']["order_id"])], limit=1)
                picking = self.env['stock.picking'].sudo().search([('origin', '=', task['Order']["order_ref"])], limit=1)
                company = self.env['res.partner'].sudo().search([('old_api_id', '=', task['Order']["company_id"])], limit=1)
                picking_id = None
                if picking:
                    picking_id = picking.id
                if int(task['Order']['type']) != 25:
                    if not helpdesk_task:
                        print(">>> UPDATE AVOIRS <<<")
                        list_operations = []
                        for details in picking.move_ids_without_package:
                            move_line = self.env['stock.move.line'].sudo().search([('move_id', '=', details.id)], limit=1)
                            data = {
                                # "name": details['name'],
                                "qty": details.product_qty,
                                "product_id": details.product_id.id,
                                "uom_id": details.product_uom.id,
                                "lot_id": move_line.lot_id.name
                            }
                            list_operations.append(data)
                        order_details = self.env['helpdesk.ticket.operations'].sudo().create(list_operations)
                        team_id = self.env['helpdesk.ticket.category'].sudo().search([('id', '=', int(task['Order']['type']))])
                        if not team_id.default_team_id.id:
                            print("Order:", task['Order']["order_id"], "| Team:", team_id.default_team_id.id, "| Type:", task['Order']['type'])
                        # stage_id = 6
                        # if int(task['Order']["statutsav"]) == 6:
                        #     stage_id = 3
                        # elif int(task['Order']["statutsav"]) in [1, 2, 3, 4, 5]:
                        #     stage_id = int(task['Order']["statutsav"])
                        stage_id = int(task['Order']["statutsav"]) + 1
                        stage = self.env['helpdesk.ticket.stage'].sudo().search([('id', '=', stage_id)])
                        if not stage:
                            stage_id = None
                        user_id = None
                        if task['Order']["user_id"] is not None:
                            # user_id = (int(task['Order']["user_id"]),)
                            user_id = self.env['res.users'].sudo().search([('partner_id', '=', int(task['Order']["user_id"]))], limit=1).id
                            if user_id == False:
                                user_id = None
                        note = ""
                        if task['Order']['note'] is not None:
                            note = task['Order']['note']
                        company_id = None
                        if company:
                            company_id = (company.id,)
                        users_ids = None
                        if task['Order']['sav_ir_user_id'] is not None:
                            # users_ids = [int(uir_id) for uir_id in task['Order']['sav_ir_user_id'].split(';') if len(uir_id) > 0]
                            users_ids = []
                            for uir_id in task['Order']['sav_ir_user_id'].split(';'):
                                if len(uir_id) > 0:
                                    user_partner = self.env['res.users'].sudo().search([('partner_id', '=', int(uir_id))], limit=1)
                                    users_ids.append(user_partner.id)
                        order_id = int(task['Order']["order_id"])
                        task_data = {
                            "name": task['Order']['ref'],
                            "team_id": team_id.default_team_id.id,
                            "user_id": None,
                            "number": int(task['Order']["order_id"]),
                            # "order_id": task['Order']["order_id"],
                            # "order_ref": task['Order']['order_ref'],
                            "order_date": task['Order']['order_date'],
                            "partner_id": company_id,
                            "category_id": int(task['Order']['type']),
                            "picking_id": picking_id,
                            "note": note,
                            "stage_id": stage_id,
                            "operations": order_details,
                            "users_ids": users_ids,
                            "url_crm": f'http://141.94.171.159/crm/propals/view/{order_id}',
                            "invoice": f'http://141.94.171.159/crm/Propals/viewpdf/{order_id}'
                        }
                        # raise Exception(task_data)
                        list_tasks.append(task_data)
                        try:
                            helpdesk_tasks = self.env['helpdesk.ticket'].sudo().create(task_data)
                        except:
                            raise Exception(task['Order']["order_id"])
                    else:
                        print(">>> UPDATE AVOIRS <<<")
                        team_id = self.env['helpdesk.ticket.category'].sudo().search(
                            [('id', '=', int(task['Order']['type']))])
                        user_id = None
                        if task['Order']["user_id"] is not None:
                            # user_id = (int(task['Order']["user_id"]),)
                            user_id = self.env['res.users'].sudo().search([('partner_id', '=', int(task['Order']["user_id"]))], limit=1).id
                            if user_id == False:
                                user_id = None
                        company_id = None
                        if company:
                            company_id = (company.id,)
                        note = ""
                        if task['Order']['note'] is not None:
                            note = task['Order']['note']
                        stage_id = int(task['Order']["statutsav"]) + 1
                        stage = self.env['helpdesk.ticket.stage'].sudo().search([('id', '=', stage_id)])
                        if not stage:
                            stage_id = None
                        users_ids = None
                        if task['Order']['sav_ir_user_id'] is not None:
                            # users_ids = [int(uir_id) for uir_id in task['Order']['sav_ir_user_id'].split(';') if len(uir_id) > 0]
                            users_ids = []
                            for uir_id in task['Order']['sav_ir_user_id'].split(';'):
                                if len(uir_id) > 0:
                                    user_partner = self.env['res.users'].sudo().search([('partner_id', '=', int(uir_id))], limit=1)
                                    users_ids.append(user_partner.id)
                        helpdesk_task.sudo().write(
                            vals={
                                "name": task['Order']['ref'],
                                "team_id": (team_id.default_team_id.id,),
                                "user_id": None,
                                "number": int(task['Order']["order_id"]),
                                "order_date": task['Order']['order_date'],
                                "partner_id": company_id,
                                "category_id": (int(task['Order']['type']),),
                                "picking_id": (picking_id,),
                                "note": note,
                                "stage_id": stage_id,
                                "users_ids": users_ids
                            },
                            isCron=True
                        )
            except:
                raise Exception('id: '+task['Order']["order_id"])
        # try:
        #     helpdesk_tasks = self.env['helpdesk.ticket'].sudo().create(list_tasks)
        # except:
        #     raise UserError('Error in Cron Create Avoirs')

    def import_sale_orders_cron_modified(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

        sql = """ select max(custom_modified) from sale_order where custom_type in ('0','1','25') """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()

        if result[0]:
            formatted_datetime = str(result[0].date()) + "_" + str(result[0].strftime("%H")) + "@" + str(
                result[0].strftime("%M")) + "@" + str(result[0].strftime("%S"))
            #             formatted_datetime = "2022-02-23_10@44@48"
            url = "http://141.94.171.159/crm/Companies/getPropalsToOdoo/" + str(
                formatted_datetime) + "/iscron=cron"
            data = json.loads(requests.get(url, auth=(username, password)).content)

            #             data_new = []
            #             for dt in data:
            #                 if dt['Order']['order_id'] == '98381':
            #                     data_new.append(dt)
            #             data = data_new
            self.create_update_sales(data)

    def import_sale_orders_cron(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

        #         url="http://141.94.171.159/crm/Companies/getPropalsToOdoo/null/iscron=cron"
        # url = "http://141.94.171.159/crm/Companies/getPropalsToOdoo/part19/iscron=cron"
        url = "http://141.94.171.159/crm/Companies/getPropalsToOdoo/part19/iscron=cron"

        data = json.loads(requests.get(url, auth=(username, password)).content)

        self.create_update_sales(data)

    def order_1(self):
        compteur=0
        for sale in self.env['sale.order'].search([('custom_type', 'in', ['1', '25']),('delivery_status', 'in', [1])]):
            print (sale.name)
            compteur = compteur + 1
            print(compteur)

            for p in sale.picking_ids:
                if p.state=='cancel':
                    print ("-------------hi test cancel")
                    print (sale.name)
                    p.action_back_to_draft()
                if p.state != 'done':
                            p.action_confirm()
                            for i in p.move_ids_without_package:
                                i.quantity_done = i.product_uom_qty
                                if i.product_uom_qty <= 0:
                                    i.product_uom_qty = 1
                                    i.quantity_done = 1

                            p.button_validate()
    def order_2(self):
        compteur=0
        for sale in self.env['sale.order'].search([('custom_type', 'in', ['1', '25']),('delivery_status', 'in', [2])]):
            print (sale.name)
            compteur=compteur+1
            print(compteur)

            for p in sale.picking_ids:
                if p.state=='cancel':
                    print ("-------------hi test cancel")
                    print (sale.name)
                    p.action_back_to_draft()
                if p.state != 'done':
                            p.action_confirm()
                            for i in p.move_ids_without_package:
                                i.quantity_done = i.product_uom_qty
                                if i.product_uom_qty <= 0:
                                    i.product_uom_qty = 1
                                    i.quantity_done = 1

                            p.button_validate()

    def order_0_3(self):
        compteur = 0
        for sale in self.env['sale.order'].search(
                [('custom_type', 'in', ['1', '25']), ('delivery_status', '=', 3)]):
            print(sale.name)
            compteur = compteur + 1
            print(compteur)

            for p in sale.picking_ids:
                if p.state == 'cancel':
                    print("-------------hi test cancel")
                    print(sale.name)
                    p.action_back_to_draft()
                if p.state == 'done':
                    print("-------------hi test done")
                    print(sale.name)
                if p.state not in ['confirmed','assigned']:
                    p.action_confirm()
                    p.action_assign()
                else:
                    p.action_assign()

    def order_4(self):
        compteur = 0
        for sale in self.env['sale.order'].search(
                [('custom_type', 'in', ['1', '25']), ('delivery_status', 'in', [4])]):
            print(sale.name)
            compteur = compteur + 1
            print(compteur)

            for p in sale.picking_ids:

                if p.state == 'done':
                    print("-------------hi test done")
                    print(sale.name)
                    # p.action_cancel()
                if p.state not in ['cancel','done']:
                    p.action_cancel()












    def update_volume(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

        url = "http://141.94.171.159/crm/companies/getVolumeToOdoo"
        data = json.loads(requests.get(url, auth=(username, password)).content)
        compteur = 0
        for rec in data:
            print ("hello resc")
            compteur=compteur+1
            print(compteur)

            product_id=self.env['product.product'].search([('old_id','=',rec['product_id'])],limit=1)
            if product_id:
                print ("hello product")
                print (product_id.name)

                if rec['dimX']:
                    unity = self.env['uom.uom'].search([('name', '=', rec['dimX'].replace(',','.')[len(rec['dimX'])-2:])], limit = 1)
                    product_id.product_length=float(rec['dimX'].replace(',','.')[:len(rec['dimX'])-2])
                if rec['dimY']:
                    product_id.product_height =float(rec['dimY'].replace(',','.')[:len(rec['dimY'])-2])
                if rec['dimY']:
                    product_id.product_width =float(rec['dimZ'].replace(',','.')[:len(rec['dimZ'])-2])
                if unity:
                    product_id.dimensional_uom_id=unity.id
                if rec['capacity_ml']:
                    product_id.capacity_ml = rec['capacity_ml']
                if rec['capacity_gr']:
                    product_id.weight_uom_id=self.env['uom.uom'].search([('name', '=','g')],limit=1)
                    product_id.weight = float(rec['capacity_gr'].replace(',','.'))
                length_m = self.env['product.template'].convert_to_meters(product_id.product_length, product_id.dimensional_uom_id)
                height_m =self.env['product.template'].convert_to_meters(product_id.product_height, product_id.dimensional_uom_id)
                width_m = self.env['product.template'].convert_to_meters(product_id.product_width, product_id.dimensional_uom_id)
                volume = length_m * height_m * width_m
                product_id.volume=volume








    def update_status(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

        url = "http://141.94.171.159/crm/Companies/getStatusToOdoo/iscron=cron"

        data = json.loads(requests.get(url, auth=(username, password)).content)
        compteur=0
        for rec in data:
            print ("hello resc")
            compteur=compteur+1
            print(compteur)
            print (rec['Order']['order_id'])
            sale=self.env['sale.order'].search([('old_id','=',rec['Order']['order_id'])],limit=1)
            if sale:
                print("hello test sale")
                print (sale)
                datetime_object = datetime.strptime(rec['Order']['date_order'], '%Y-%m-%d')
                sale.date_order= datetime_object.date()
                print (sale.delivery_status)
                print (rec['Order']['statut'])
                if sale.delivery_status != int(rec['Order']['statut']):
                    print ("helllo difffff")
                    sale.delivery_status=int(rec['Order']['statut'])
                    delivery=int(rec['Order']['statut'])
                    # if delivery not in (0, 3):
                    #     for p in sale.purchase_order_ids:
                    #         p.state = 'done'
                    # else:
                    #     for p in sale.purchase_order_ids:
                    #         p.state = 'draft'

                    # state = 'assigned'
                    # if delivery in [1, 2]:
                    #     state = 'done'
                    #
                    # elif delivery == 4:
                    #     state = 'cancel'
                    # elif delivery == 5:
                    #     state = 'confirmed'
                    # if state == 'assigned':
                    #
                    #         for p in sale.picking_ids:
                    #             if p.state != 'assigned':
                    #                 if p.state =='done':
                    #                     print ("hello test 555 done")
                    #                     print (p.state)
                    #                 p.action_confirm()
                    #                 p.action_assign()
                    # elif state == 'done':
                    #     for p in sale.picking_ids:
                    #         if p.state != 'done':
                    #             p.action_confirm()
                    #             for i in p.move_ids_without_package:
                    #                 i.quantity_done = i.product_uom_qty
                    #                 if i.product_uom_qty <= 0:
                    #                     i.product_uom_qty = 1
                    #                     i.quantity_done = 1
                    #
                    #             p.button_validate()
                    # elif state == 'cancel':
                    #     for p in sale.picking_ids:
                    #         if p.state not in ['cancel','done']:
                    #             p.action_cancel()
                    #         if p.state=''
                    #
                    # elif state == 'confirmed':
                    #     for p in sale.picking_ids:
                    #         if p.state != 'confirmed':
                    #             p.state = 'confirmed'



    def create_update_sales(self, data):
        product_obj = self.env['product.product']
        partner_obj = self.env['res.partner']
        user_obj = self.env['res.users']
        StockPicking = self.env['stock.picking']
        count = 0
        c = 0
        for rec in data:
            # try:
                c = rec['Order']['order_id']
                sale_order_val = {}
                print(rec.get('Order'))
                print(rec.get('Order_details'))
                print('===========================')
                company_id = 0

                if rec['Order']['company_id'] != None:
                    company_id = rec['Order']['company_id']
                print ("hiii order testttt")
                print (rec['Order']['order_id'])
                if rec['Order']['order_id']=='98761':
                    print ("Hello is order")
                if int(company_id)==1024247:
                    print ("Hello is company")


                customer_id = partner_obj.search([('old_api_id', '=', int(company_id)), ('customer_rank', '=', 1)],
                                                order='id desc', limit=1)
                print (customer_id)

                if not customer_id:
                    customer_id = partner_obj.search([('old_api_id', '=', 0), ('customer_rank', '=', 1)], order='id desc',
                                                    limit=1)

                user_id = user_obj.search([('partner_id', '=', rec['Order']['user_id'])], limit=1)
                print('customer_id-------', customer_id)

                if customer_id:
                    sale_order_val['partner_id'] = customer_id.id
                    sale_order_val['old_id'] = rec['Order']['order_id']
                    sale_order_val['reference'] = rec['Order']['ref']

                    if rec['Order']['order_date'] != None:
                        datetime_object = datetime.strptime(rec['Order']['order_date'], '%Y-%m-%d')
                        sale_order_val['custom_order_date'] = datetime_object.date()
                        sale_order_val['date_order'] = datetime_object.date()
                    else:
                        datetime_object = datetime.now()
                        sale_order_val['custom_order_date'] = datetime_object.date()
                        sale_order_val['date_order'] = datetime_object.date()

                    # sale_order_val['user_id'] = rec['Order']['user_id']
                    sale_order_val['user_id'] = user_id.id
                    sale_order_val['note'] = rec['Order']['note']
                    sale_order_val['margin'] = rec['Order']['margin']
                    sale_order_val['custom_type'] = rec['Order']['type']
                    sale_order_val['delivery_status'] = int(rec['Order']['delivery_status'])
                    if rec['Order'].get('amazon_fba') != None:
                        if int(rec['Order'].get('amazon_fba')) == 1:
                            sale_order_val['amazon_fba'] = "Expédié par Amazon"
                    if rec['Order'].get('flag_nc'):
                        sale_order_val['flag_nc'] = rec['Order']['flag_nc']
                    else:
                        sale_order_val['flag_nc'] = '-'

                    if rec['Order']['delivery_date'] != None:
                        sale_order_val['delivery_date'] = rec['Order']['delivery_date']
                    if rec['Order']['hors_tva'] != False:
                        sale_order_val['hors_tva'] = rec['Order']['hors_tva']
                    if rec['Order']['date_offset'] != None:
                        sale_order_val['date_offset'] = rec['Order']['date_offset']
                        sale_order_val['date_offset_format'] = rec['Order']['date_offset']

                    sale_order_val['custom_discount'] = 0
                    if rec['Order']['discount'] != None:
                        sale_order_val['custom_discount'] = float(rec['Order']['discount'])

                    sale_order_val['lost_margin_float'] = 0
                    if rec['Order']['lost_margin'] != None:
                        sale_order_val['lost_margin_float'] = float(rec['Order']['lost_margin'])
                    if rec['Order']['payment'] != None:
                        sale_order_val['custom_payment'] = rec['Order']['payment']
                    if rec['Order']['provider_ref'] != None:
                        sale_order_val['provider_ref'] = rec['Order']['provider_ref']
                    if rec['Order']['provenance'] != None:
                        sale_order_val['provenance'] = rec['Order']['provenance']
                    if rec['Order']['provenance_ref'] != None:
                        sale_order_val['provenance_ref'] = rec['Order']['provenance_ref']
                    if rec['Order']['commission'] != None:
                        sale_order_val['commission'] = rec['Order']['commission']
                    if rec['Order']['contrat'] != None:
                        sale_order_val['contrat'] = rec['Order']['contrat']
                    if rec['Order']['order_ref'] != None:
                        sale_order_val['order_ref'] = rec['Order']['order_ref']

                    if rec['Order']['modified'] != None:
                        datetime_object = datetime.strptime(rec['Order']['modified'], '%Y-%m-%d %H:%M:%S')
                        sale_order_val['custom_modified'] = datetime_object

                    lines_val = []
                    if 'Order_details' in rec:
                        for order_detail in rec['Order_details']:
                            ("hello order detail")
                            print(order_detail)
                            vals = {}
                            product_id = product_obj.search([('old_id', '=', order_detail['product_id'])], limit=1)

                            # print('++++++++++++++++++++++++++++++',product_id.default_code)
                            print ("hello product_id")
                            print (product_id)
                            if product_id:
                                print ("if product")
                                description = product_id.display_name
                                if order_detail['name'] != None:
                                    description = order_detail['name']
                                if order_detail.get('detail_order_id'):
                                    vals['detail_order_id'] = order_detail['detail_order_id']

                                    if 'Express' in description:
                                        product_id = product_obj.search([('default_code', '=', 'LE')], limit=1)
                                    elif 'Rapide' in description:
                                        product_id = product_obj.search([('default_code', '=', 'LR')], limit=1)
                                    elif 'livraison' in description:
                                        product_id = product_obj.search([('default_code', '=', 'LG')], limit=1)

                                vals['product_id'] = product_id.id
                                vals['name'] = description
                                vals['product_uom_qty'] = order_detail['qantity']
                                vals['price_unit'] = order_detail['price']
                                vals['product_code_custom'] = order_detail['code']
                                vals['tx_tva'] = order_detail['tx_tva']
                                vals['tht'] = order_detail['tht']
                                vals['ttva'] = order_detail['ttva']
                                vals['ttc'] = order_detail['ttc']
                                vals['custom_supplier_price'] = order_detail['supplier_price']
                                vals['management_cost'] = order_detail['management_cost']
                                vals['provider_ref'] = order_detail['provider_ref']
                                vals['custom_carrier'] = order_detail['carrier']
                                vals['tracking'] = order_detail['tracking']
                                vals['delivery_type'] = order_detail['delivery_type']
                                vals['delivery_cost'] = order_detail['delivery_cost']
                                vals['custom_order_id'] = order_detail['order_id']
                                vals['custom_product_id'] = order_detail['product_id']
                                vals['promo'] = order_detail['promo']
                                # if order_detail['carrier']=='TNT':
                                #     if order_detail['tracking'] != None:
                                #         self.download_ftp_tnt(order_detail['tracking']+'.pdf',rec['Order']['order_id'])

                                if order_detail['supplier_id'] != None:
                                    vals['custom_supplier_idd'] = int(order_detail['supplier_id'])

                                    supplier_id = self.env['res.partner'].search(
                                        [('old_api_id', '=', int(order_detail['supplier_id'])), ('supplier_rank', '=', 1)],
                                        limit=1)
                                    vals['custom_supplier_id'] = supplier_id.id

                                else:
                                    vals['custom_supplier_idd'] = 0

                                    supplier_id = self.env['res.partner'].search(
                                        [('old_api_id', '=', 0), ('supplier_rank', '=', 1)], limit=1)
                                    vals['custom_supplier_id'] = supplier_id.id

                                lines_val.append((0, 0, vals))

                    sale_order_val['order_line'] = lines_val

                    exist_sale_order = self.search([('old_id', '=', rec['Order']['order_id'])], limit=1)
                    if exist_sale_order:
                        print('----------update--------')

                        if int(exist_sale_order.custom_type) != 1:
                            print('----------QUOTATION--------')
                            if exist_sale_order.order_line:
                                exist_sale_order.order_line.unlink()

                            exist_sale_order.update(sale_order_val)
                            sale_id = exist_sale_order

                        if int(exist_sale_order.custom_type) == 1 and exist_sale_order.state == 'sale':
                            print('----------SALE ORDER--------')
                            not_tobe_deleted = StockPicking.search(
                                [('custom_sale_id', '=', exist_sale_order.id), ('state', '=', 'done')])
                            print(not_tobe_deleted)
                            if not_tobe_deleted:
                                exist_sale_order.update({'partner_id': customer_id})
                                if rec['Order']['order_date'] != None:
                                    datetime_object = datetime.strptime(rec['Order']['order_date'], '%Y-%m-%d')
                                    exist_sale_order.date_order = datetime_object.date()
                                    exist_sale_order.custom_order_date = datetime_object.date()
                                print('-----iffff-----')
                                continue
                            else:
                                print('--------else-------')
                                PurchaseOrder = self.env['purchase.order']
                                tobe_deleted = StockPicking.search(
                                    [('custom_sale_id', '=', exist_sale_order.id), ('state', '!=', 'cancel')])
                                print(tobe_deleted)
                                tobe_deleted.unlink()

                                purchase_orders = PurchaseOrder.search([('sale_order_id', '=', exist_sale_order.id)])

                                if purchase_orders:
                                    purchase_orders.button_cancel()
                                    purchase_orders.unlink()
                                exist_sale_order.action_cancel()
                                exist_sale_order.unlink()
                                sale_id = self.create(sale_order_val)

                    else:
                        print('----------create--------')
                        sale_id = self.create(sale_order_val)
                    
                    if user_id:
                        sale_id.update({'user_id': user_id.id})

                    if int(sale_id.custom_type) == 1:
                        sale_id.action_confirm()

                    margin_val = sale_id.margin
                    custom_discount_val = sale_id.custom_discount
                    lost_margin_float_val = sale_id.lost_margin_float

                    if margin_val == None:
                        margin_val = 0

                    if custom_discount_val == None:
                        custom_discount_val = 0

                    if lost_margin_float_val == None:
                        lost_margin_float_val = 0

                    marge = margin_val - custom_discount_val - lost_margin_float_val
                    sale_id.update({'marge': marge})
                    sale_id.update({'partner_id': customer_id})
                    if rec['Order']['order_date'] != None:
                        datetime_object = datetime.strptime(rec['Order']['order_date'], '%Y-%m-%d')
                        sale_order_val['custom_order_date'] = datetime_object.date()
                        sale_id.date_order = datetime_object.date()
                    if int(sale_id.custom_type) != 0 and int(sale_id.custom_type) != 1 and int(sale_id.custom_type) != 25:
                        sale_id.update({'amount_total': -sale_id.amount_total})
            # except:
            #     raise Exception(f'Len data:{len(data)} | error in: {c}')

    def action_confirm(self):
        rec = super(SaleOrderCustom, self).action_confirm()

        picking_rec = self.env['stock.picking'].search([('sale_id', '=', self.id)], order='id desc', limit=1)
        print(picking_rec)

        if picking_rec:
            picking_rec.unlink()

        self.create_sale_operations()
        #         self.create_purchase_quotation()

        return rec

    def create_sale_operations(self):
        print('sale_order---------', self.name)

        operation_lst = []
        delivery_status = self.delivery_status
        liste_DO = self.order_line.filtered(
            lambda r: r.custom_supplier_idd in [0, 1, False] and r.product_id.type == 'product')
        liste_DROP = self.order_line.filtered(
            lambda r: r.custom_supplier_idd not in [1, 0, False] and r.product_id.type == 'product')
        list_service = self.order_line.filtered(lambda r: r.product_id.type == 'service')
        state = 'assigned'
        if delivery_status in [1,2]:
            state = 'done'

        elif delivery_status == 4:
            state = 'cancel'
        elif delivery_status == 5:
            state = 'confirmed'
        elif delivery_status == 6:
            state = 'not_approved'
        if state == 'not_approved':
            if len(liste_DO.ids) <= 0:
                self.create_stock_picking(liste_DROP + list_service, state, 'Delivery Orders')
            else:
                self.create_stock_picking(liste_DO + list_service, state, 'Delivery Orders')
        else:
            if liste_DO:
                self.create_stock_picking(liste_DO + list_service, state, 'Delivery Orders')
            if liste_DROP:
                self.create_stock_picking(liste_DROP + list_service, state, 'Dropshipping')

    def create_stock_picking(self, liste, state, picking_type_name):
        picking_type_id = self.env['stock.picking.type'].search([('name', '=', picking_type_name)], limit=1)
        stock_move_vals = []
        if not picking_type_id.default_location_dest_id:
            raise UserError('Please selection destination location in operations : ' + str(picking_type_id.name))
        # delivery_type = None
        # sales = self.env['sale.order.line'].sudo().search([('order_id', '=', self.id)])
        # for s in sales:
        #     if s.delivery_type is not None:
        #         delivery_type = s.delivery_type
        # location_src = picking_type_id.default_location_src_id.id
        # if delivery_type == "Expédié par Amazon":
        #     location_src = 56
        amazon_fba = self.amazon_fba
        location_src = picking_type_id.default_location_src_id.id
        if amazon_fba == "Expédié par Amazon":
            location_src = 56
        for line in liste:
            stock_move_vals.append((0, 0, {
                'name': line.product_id.display_name,
                'detail_order_id': line.detail_order_id,
                'sale_line_id': line.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'partner_id': self.partner_id.id,
                'origin': self.old_id,
            }))
        
        stock_picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_id.id,
            'origin': self.old_id,
            'sale_id': self.id,
            'move_ids_without_package': stock_move_vals,
            'location_id': location_src,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'custom_sale_id': self.id,
            'sale_reference': self.reference,
            'amazon_fba': amazon_fba
        }
        if state == 'not_approved':
            stock_picking_vals['state'] = 'not_approved'
        picking_id = self.env['stock.picking'].create(stock_picking_vals)
                     
        picking_id.createpdfsingle()

        if state == 'assigned':
            picking_id.action_confirm()
            picking_id.action_assign()
            picking_id.create_pack()
        elif state == 'done':
            picking_id.action_confirm()
            
            for i in picking_id.move_ids_without_package:
                i.quantity_done = i.product_uom_qty
                if i.product_uom_qty <=0:
                    i.product_uom_qty=1
                    i.quantity_done = 1

            picking_id.button_validate()
            picking_id.create_pack()
        elif state == 'cancel':
            picking_id.action_cancel()
        elif state == 'confirmed':
            picking_id.state = 'confirmed'
        elif state == 'not_approved':
            picking_id.state = 'not_approved'

        # picking_id.action_confirm()
        picking_id.synch_info()

    def action_cancel_order_multiple(self):
        records = self.browse(self.ids)

        for record in records:
            record.action_cancel()

    def action_view_purchase_order(self):
        # view = self.env.ref('mrp.view_immediate_production')
        return {
            'name': _('Achat'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.purchase_order_ids.ids)]

        }

    amazon_fba = fields.Char('Amazon FBA')
    flag_nc = fields.Char('Segmentation')
    old_id = fields.Char('Order ID')
    margin = fields.Float('Margin')
    marge = fields.Float('Marge')
    custom_modified = fields.Datetime('Modified')
    custom_type = fields.Char('Type')
    hors_tva = fields.Char('Hors Tva')
    delivery_status = fields.Integer('Delievery Status')
    delivery_date = fields.Char('Delivery Date')
    date_offset = fields.Char('Date Offset')
    date_offset_format = fields.Date('Date Offset Format')
    custom_discount = fields.Float('Discount')
    lost_margin = fields.Char('Lost margin')
    lost_margin_float = fields.Float('Lost Margin')
    custom_payment = fields.Char('Payment')
    provider_ref = fields.Char('Provider Ref')
    provenance = fields.Char('Provenance')
    provenance_ref = fields.Char("Provenance Ref")
    commission = fields.Char('Commission')
    contrat = fields.Char('Contrat')
    order_ref = fields.Char('Order Ref')
    custom_order_date = fields.Date('Custom Order Date')
    purchase_order_ids = fields.One2many('purchase.order', 'sale_order_id', string='Purchase')
    is_converted_to_purchase = fields.Boolean('Converted To Purchase?')
    is_update = fields.Boolean()
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=False, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")



class SaleOrderCustomLine(models.Model):
    _inherit = 'sale.order.line'

    product_code_custom = fields.Char('Code')
    tx_tva = fields.Char('Tx Tva')
    tht = fields.Char('Tht')
    ttva = fields.Char('Ttva')
    ttc = fields.Char('Ttc')
    custom_supplier_price = fields.Char('Supplier Price')
    management_cost = fields.Char('Management Cost')
    provider_ref = fields.Char('Provider Ref')
    custom_carrier = fields.Char('Carrier')
    tracking = fields.Char('Tracking')
    delivery_type = fields.Char('Delivery Type')
    delivery_cost = fields.Char('Delivery Cost')
    custom_order_id = fields.Char('Order Id')
    custom_product_id = fields.Char('Product ID')
    custom_supplier_id = fields.Many2one('res.partner', string="Supplier")
    custom_supplier_idd = fields.Integer(string="Supplier ID")
    detail_order_id = fields.Integer('Detail order id')
    promo = fields.Char('Promo')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    custom_sale_id = fields.Many2one('sale.order', string="Custom Sale ID")


class PurchaseOrderCustom(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        rec = super(PurchaseOrderCustom, self).button_confirm()
        
        for ligne in self.order_line:
            if ligne.product_id.sale_ok==True and ligne.product_id.type=='product':
                arrivage=[]
                onhand_qty= ligne.product_id.qty_available - ligne.product_id.qty_not_validated_yet
                moves = self.env['stock.move'].search(
                        [('product_id', '=', ligne.product_id.id), ('state', '=', 'assigned'), ('picking_type_id', '=', 1)])
                for m in moves:
                        if m.purchase_line_id:
                            arrivage.append(
                                ['1',m.purchase_line_id.price_unit, m.product_uom_qty,m.date.strftime('%Y-%m-%d')
                                , m.incertain])
                        elif m.sale_line_id:
                            arrivage.append(
                                ['1',m.sale_line_id.custom_supplier_price, m.product_uom_qty,m.date.strftime('%Y-%m-%d')
                                , m.incertain])
                        else:
                            arrivage.append(
                                ['1',0.0, m.product_uom_qty,m.date.strftime('%Y-%m-%d')
                                , m.incertain])
                post_data = {'price': ligne.product_id.standard_price, 'product_id': ligne.product_id.old_id,
                             'stock': onhand_qty,'arrivage': arrivage}
                url = 'http://141.94.171.159/crm/Companies/majStock?iscron=cron'
                requests.post(url, json=post_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))


        if self.sale_order_id:
            picking_rec = self.env['stock.picking'].search([('purchase_id', '=', self.id)], order='id desc', limit=1)
            print(picking_rec)

            if picking_rec:
                picking_rec.unlink()

        return rec

    def get_unique_provider_ref(self, provider_ref_list):
        provider_ref = ''
        provider_ref_list = set(provider_ref_list)

        for ref in provider_ref_list:
            provider_ref = provider_ref + ref + ", "

        if provider_ref != '':
            provider_ref = provider_ref[:-2]

        return provider_ref

    def compute_provider_ref(self):
        for rec in self:
            provider_ref = None
            provider_ref_list = []

            if rec.order_line:
                for line in rec.order_line:
                    if line.provider_ref:
                        provider_ref_list.append(line.provider_ref)

                print(provider_ref_list)
                if provider_ref_list != []:
                    provider_ref = rec.get_unique_provider_ref(provider_ref_list)

            rec.provider_ref = provider_ref

    def compute_deliver_to(self):
        for rec in self:
            address = ''

            if rec.sale_order_id:
                partner = rec.sale_order_id.partner_id

                if partner.street:
                    address = address + partner.street + ', '
                if partner.street2:
                    address = address + partner.street2 + ', '
                if partner.city:
                    address = address + partner.city + ', '
                if partner.zip:
                    address = address + partner.zip + ', '

                if address != '':
                    address = address[:-2]

            rec.partner_delivery_address = address

    sale_order_id = fields.Many2one('sale.order', string='Sale Order Ref', copy=False)
    provider_ref = fields.Char('Provider Ref', compute='compute_provider_ref')
    partner_delivery_address = fields.Char(compute='compute_deliver_to')
    custom_modified = fields.Datetime(string='Custom Modified')


class PurchaseOrderLineCustom(models.Model):
    _inherit = 'purchase.order.line'

    provider_ref = fields.Char('Provider Ref')
    detail_order_id = fields.Integer('Detail order id')



