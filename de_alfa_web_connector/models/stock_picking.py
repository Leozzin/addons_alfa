# -*- coding: utf-8 -*-
from email.policy import default
import os
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import requests
import json
from ftplib import FTP
import csv
from csv import reader



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ticket_id = fields.Many2one('helpdesk.ticket', 'SAV', readonly=True)
    # amazon_fba = fields.Char(string='Amazon FBA')
    amazon_fba = fields.Selection([('null', ''), ('Expédié par Amazon', 'Expédié par Amazon')], string='Amazon FBA', default='null')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('not_approved', 'Not Approved'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")
    def action_download_attachment(self):
        ftp=FTP('ftp.cluster017.ovh.net', 'alfaprinfm-gls', 'Etiquette59')
        dest=r'/opt/odoo/addons_alfa/de_alfa_ftp_gls/static/description/files/tracking'
        ftp.cwd('/testtracking')
        #liste = ftp.nlst('tracking/*.csv')
        liste = ftp.nlst('*.csv')
        for l in liste:
            os.chdir(dest)
            file_des=l
            with open(file_des,'wb') as file:
                ftp.retrbinary('RETR %s' %l,file.write)
            with open(file_des, 'r') as read_obj:
                csv_reader = reader(read_obj,delimiter=';')
                # Iterate over each row in the csv using reader object
                for row in csv_reader:
                    # row variable is a list that represents a row in csv
                    if len (row) >= 4:
                        #if (row[13] and row[16] and row[13]!='' and row[16]!=''):
                            search=self.env['stock.picking'].search([('origin','=',str(row[14]))])
                            if search:
                                search[0].carrier_tracking_ref=row[17]

    

    def get_report(self, download_url):
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')

            print ("hyyy")
            print (str(base_url) + str(download_url))

            return {
                'name': 'Go to website',
                'type': 'ir.actions.act_url',

                'url': str(base_url) + str(download_url),
                 'target': 'self',
            }
    def create_pack(self):
        for record in self:
            liste=record.move_line_ids_without_package.filtered(lambda m: m.tracking_ws)
            tracking=[]
            for i in liste:
                if i.tracking_ws not in tracking:
                    tracking.append(i.tracking_ws)
            custom = False
            if record.move_line_ids_without_package:
                custom = record.move_line_ids_without_package[0].custom_carrier
            for t in tracking:
                move_line_ids=record.move_line_ids_without_package.filtered(lambda m: m.tracking_ws==t)
                pack=record._put_in_pack(move_line_ids)
                pack.carrier_tracking_ref=t
                if custom=='TNT':
                    pack.carrier_tracking_url = "%s/%s=%s" % (
                                     "https://www.tnt.fr",
                                      "public/suivi_colis/recherche/visubontransport.do?bonTransport",
                                    t,
                                         )
                elif custom=='CHRONO':
                    print("helolo CRON")
                    print(record.origin)
                    pack.carrier_tracking_url = "%s/%s=%s" % (
                            "https://www.chronopost.fr/",
                                "tracking-no-cms/suivi-page?listeNumerosLT",
                                t,
                                         )
            if len(tracking)==1:
                record.carrier_tracking_ref=tracking[0]


            if  all(l.custom_carrier==custom for l in record.move_ids_without_package) and custom:
                search=self.env['delivery.carrier'].search(['|',('active','=',True),('active','=',False),('name','=',custom + ' ALFA')])
                if search:
                    record.carrier_id=search[0].id
                else:
                    d=self.env['delivery.carrier'].create({'name':custom + ' ALFA' ,
                                                           'product_id':19282})
                    record.carrier_id=d.id
    def createpdfsingle(self):
        for i in self:
            url=os.path.join(r'/opt/odoo/addons_alfa/de_alfa_ws_tnt/static/description/files/tnt',str(i.origin))
            if os.path.exists(url):


                for r in os.listdir(url):
                     if not self.env["ir.attachment"].search([('name','=',r),('res_model','=',i._name),('res_id','=',i.id)]):
                         self.env["ir.attachment"].create(
                                    {

                                        "name": r,
                                        "type": "url",
                                        "url":'/de_alfa_ws_tnt\static/description/files/tnt/'+str(i.origin)+'/'+r,
                                        # "url": "/theme_default\static/description/icon.png",
                                        "res_model": i._name,
                                        "res_id": i.id,
                                    }
                                )
    def correct_sale(self):
        compteur=0
        for record in self.env['stock.picking'].search([('carrier_id','=',False),('is_update','=',False)],limit=5000):
            compteur=compteur+1
            print(compteur)
            liste=record.move_line_ids_without_package.filtered(lambda m: m.tracking_ws)
            tracking=[]
            for i in liste:
                if i.tracking_ws not in tracking:
                    tracking.append(i.tracking_ws)
            custom = False
            if record.move_line_ids_without_package:
                custom = record.move_line_ids_without_package[0].custom_carrier
            for t in tracking:
                move_line_ids=record.move_line_ids_without_package.filtered(lambda m: m.tracking_ws==t)
                pack=record._put_in_pack(move_line_ids)
                pack.carrier_tracking_ref=t
                if custom == 'TNT':
                    pack.carrier_tracking_url = "%s/%s=%s" % (
                        "https://www.tnt.fr",
                        "public/suivi_colis/recherche/visubontransport.do?bonTransport",
                        t,
                    )
                elif custom == 'CHRONO':
                    print("helolo CRON")
                    print(record.origin)
                    pack.carrier_tracking_url = "%s/%s=%s" % (
                        "https://www.chronopost.fr/",
                        "tracking-no-cms/suivi-page?listeNumerosLT",
                        t,
                    )
            if len(tracking)==1:
                record.carrier_tracking_ref=tracking[0]


            if  all(l.custom_carrier==custom for l in record.move_line_ids_without_package) and custom:
                search=self.env['delivery.carrier'].search(['|',('active','=',True),('active','=',False),('name','=',custom + ' ALFA')])
                if search:
                    record.carrier_id=search[0].id
                else:
                    d=self.env['delivery.carrier'].create({'name':custom + ' ALFA' ,
                                                           'product_id':19282})
                    record.carrier_id=d.id

            record.is_update=True

    def createpdf(self):
        compteur=1
        for i in self.env['stock.picking'].search([]):
            compteur=compteur+1
            print (compteur)
            if i.origin==78111:
                print ("hello exist")
            url=os.path.join(r'/opt/odoo/addons_alfa/de_alfa_ws_tnt/files/tnt',str(i.origin))

            if os.path.exists(url):


                for r in os.listdir(url):
                     print(r)
                     self.env["ir.attachment"].create(
                                {

                                    "name": r,
                                    "type": "url",
                                    "url":'/de_alfa_ws_tnt\static/description/files/tnt/'+str(i.origin)+'/'+r,
                                    # "url": "/theme_default\static/description/icon.png",
                                    "res_model": i._name,
                                    "res_id": i.id,
                                }
                            )

    def button_validate(self):
        record=super(StockPicking, self).button_validate()
        for picking in self:
            if picking.sale_id:
                old_id = self.env['sale.order'].browse(picking.sale_id.id).old_id
                picking.send_order_status_to_website(old_id, 1)
        return record
        
    def action_cancel(self):
        record=super(StockPicking, self).action_cancel()
        for picking in self:
            if picking.sale_id:
                old_id = self.env['sale.order'].browse(picking.sale_id.id).old_id
                picking.send_order_status_to_website(old_id, 4)
        return record



    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_lines.write({'date': picking.scheduled_date})
    @api.depends('origin','picking_type_id')
    def compute_name(self):
        for record in self:
            if record.origin and record.picking_type_id:
                record.name='WH/'+record.picking_type_id.sequence_code+'/'+record.origin
            else:
                record.name = 'WHI/'+record.picking_type_id.sequence_code+'/'+str(record.id)

    # @api.depends('purchase_id', 'sale_id')
    # def compute_origin(self):
    #     for record in self:
    #         if record.purchase_id:
    #             if record.purchase_id.sale_order_id:
    #                 record.origin=record.purchase_id.sale_order_id.old_id
    #         else:
    #             if record.sale_id:
    #                 record.origin= record.sale_id.old_id

    name=fields.Char(compute=compute_name)
   
             
    # origin=fields.Char(compute=compute_origin,store=True)
    # def write(self,vals):
    #     for record in self:
    #         rec = super(StockPicking, self).write(vals)
    #         status_code = None
    #         print ("hello test")
    #         print (vals.get('state'))
    #         print (vals.get('sale_id'))
    #         picking_type_id = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
    #         if vals.get('state'):
    #             state=vals.get('state')
    #             if state=='done':
    #                 status_code = 1
    #             elif state=='assigned':
    #                 status_code=3
    #             elif state=='cancel':
    #                 status_code=4
    #             if vals.get('sale_id') and status_code != None :
    #                 old_id=self.env['sale.order'].browse(vals.get('sale_id')).old_id
    #                 # record.send_order_status_to_website(old_id, status_code)






    

    
    
    
    def send_order_status_to_website(self, order_id, status):
        username = 'alfaprint'
        password = '590-Alfaprint'
        
        url = "http://141.94.171.159/crm/Companies/updateStatusLivFromOdoo/"+str(order_id)+"/"+str(status)+"/iscron=cron"
        print('----------url-----------')
        data=json.loads(requests.get(url, auth=(username, password)).content)
        print(data)
    
    
        
    def check_transfers_for_stock_zero(self):
        picking_type_id = self.env['stock.picking.type'].search([('name','=','Fournisseur_ID_NULL')], limit=1)
        
        sql = """
            select product_id,sum(product_uom_qty) as qty from sale_order s1, sale_order_line s2  
            where  s1.id = s2.order_id and delivery_status in(0,3)  
            and custom_type in('1','25')
            and (custom_supplier_id=1 or custom_supplier_id is null)
            --and product_id = 167380 --167381
            group by product_id
        """
        self.env.cr.execute(sql)
        stock_sales = self.env.cr.dictfetchall()
        print(stock_sales)
        
        
        sql = """
            select product_id,sum(quantity) as qty from stock_quant
            where location_id in (
            select id from stock_location where usage='internal') 
            --and product_id = 167380 --167381
            group by product_id
        """
        self.env.cr.execute(sql)
        stock_quants = self.env.cr.dictfetchall()
        print(stock_quants)
        
        data_list = []
        
        for stock_sale in stock_sales:
            found = False
            
            for stock_quant in stock_quants:
                if stock_sale.get('product_id') == stock_quant.get('product_id'):
                    found = True
                    
                    remaining_stock = stock_quant.get('qty') - stock_sale.get('qty')
                    
                    if remaining_stock <= 0:
                        data_list.append(stock_sale.get('product_id'))
            
            if found == False:
                data_list.append(stock_sale.get('product_id'))
                    
        print(data_list)
        
        
        
        if data_list != []:
            
            sql = """
                select distinct s1.id  from sale_order s1, sale_order_line s2  
                where  s1.id = s2.order_id and delivery_status in(0,3)  
                and custom_type in('1','25')
                and product_id in """ +str(tuple(data_list))+""" 
                and s1.id not in 
                (select custom_sale_id from stock_picking where custom_sale_id is not null
                and picking_type_id="""+str(picking_type_id.id)+""")
            """
            
            self.env.cr.execute(sql)
            order_ids = self.env.cr.fetchall()
            print(order_ids)
            
            
            if order_ids != []:
                for order_id in order_ids:
                    order_obj = self.env['sale.order'].browse(order_id)
                    
                    print(order_obj)
                    self.create_stock_picking(order_obj, picking_type_id)

    
    
    def create_stock_picking(self, order_id, picking_type_id):
        print('create stock picking---------------')
#         picking_type_id = self.env['stock.picking.type'].search([('name','=','Fournisseur_ID_NULL')], limit=1)
        stock_move_vals=[]
        
        for line in order_id.order_line:
            stock_move_vals.append((0,0,{
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'partner_id': order_id.partner_id.id,
                'origin': order_id.old_id,
                }))
                   
            
        stock_picking_vals = {
            'partner_id': order_id.partner_id.id,
            'picking_type_id': picking_type_id.id,
            'origin': order_id.old_id,
            'move_ids_without_package': stock_move_vals,
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'custom_sale_id': order_id.id,
            }
                        
        picking_id = self.env['stock.picking'].create(stock_picking_vals)
        picking_id.action_confirm()
        
    
    def move_operation(self):
        for rec in self:
            print('--------------------------------')
            supplier_ids = operations = []
            
            for line in rec.move_ids_without_package:
                supplier_ids.append(line.supplier_old_id)
            
            if len(set(supplier_ids)) > 1:
                if '1' in supplier_ids:
                    operations = ['OUT', 'DRS']
                else:    
                    operations = ['DRS']
                    
            if len(set(supplier_ids)) == 1:
                if '1' in supplier_ids:
                    operations = ['OUT']
                else:    
                    operations = ['DRS']
                
            print(operations)
                
            if operations != []:
                rec.copy_opeation(operations)
        self.unlink()    
            
            
    def copy_opeation(self, operations):
        for operation in operations:
            picking_type_id = self.env['stock.picking.type'].search([('sequence_code','=',operation)], limit=1)
            print(picking_type_id)
            stock_move_vals=[]
            
            for line in self.move_ids_without_package:
                stock_move_vals.append((0,0,{
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'partner_id': self.custom_sale_id.partner_id.id,
                    'origin': self.custom_sale_id.old_id,
                    }))
                       
            print(picking_type_id.default_location_src_id)
            print(picking_type_id.default_location_dest_id)    
            stock_picking_vals = {
                'partner_id': self.custom_sale_id.partner_id.id,
                'picking_type_id': picking_type_id.id,
                'origin': self.custom_sale_id.old_id,
                'move_ids_without_package': stock_move_vals,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
                'custom_sale_id': self.custom_sale_id.id,
                }
                            
            picking_id = self.create(stock_picking_vals)
            picking_id.synch_info()
            picking_id.action_cancel()
            print('delete current rec')
            
    
    
    
    def synch_info(self):
        for rec in self:
            rec.synch_info_single()
            
            
    def synch_info_single(self):
        if self.custom_sale_id:
            if self.custom_sale_id.date_offset_format:    
                datee = self.custom_sale_id.date_offset_format
            else:
                datee = self.custom_sale_id.custom_order_date
                
            self.update({'scheduled_date': datee})
            
            if self.move_ids_without_package:
                for move_line in self.move_ids_without_package:
                    for sale_line in self.custom_sale_id.order_line:
                        if move_line.product_id == sale_line.product_id:
                            move_line.update({
                                'custom_supplier_id': sale_line.custom_supplier_id,
                                'supplier_old_id': sale_line.custom_supplier_idd
                                              })

    
    def action_check_availability(self):
        for rec in self:
            if rec.state in ('confirmed','waiting','assigned'):
                rec.action_assign()

    
    
    
    def cancel_multiple_x(self):
        for rec in self:
            if rec.state != 'done':
                rec.action_cancel()
            
                
    def reset_draft_mark_todo_multiple_x(self):
        for rec in self:
            if rec.state != 'done':
                rec.action_back_to_draft()
                rec.action_confirm()
                
    
    def delete_stock_move_line_unreserve(self):  
        for rec in self:
            print('111111111111111')
            print(rec.move_line_ids_without_package)
            if rec.move_line_ids_without_package:
                sql = """delete from stock_move_line where picking_id ="""+str(rec.id)
                self.env.cr.execute(sql)
                print('2222222222222')
            rec.do_unreserve() 


    is_update=fields.Boolean("Est mis a jour")
    # sale_reference = fields.Char(related='sale_id.reference', readonly=False, store=True, string='sale reference')
    sale_reference=fields.Char(readonly=False,string='Sale Reference')
    first_product_id = fields.Many2one('product.product', related='move_ids_without_package.product_id', store=True)



class StockMove(models.Model):
    _inherit = 'stock.move'            
            
    detail_order_id=fields.Integer('Detail order id')
    custom_supplier_id = fields.Many2one('res.partner', string='Supplier') 
    supplier_old_id = fields.Char(string='Supplier ID') 
    incertain=fields.Selection([('0','Incertain'),('1','Certain')],default='1')

    
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line' 
    #on a commenté raise error : A fixer le cron sale ---> dont delete stock move (pas fait maintenant)
    def unlink(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for ml in self:
            #if ml.state in ('done', 'cancel'):
                #raise UserError(_('You can not delete product moves if the picking is done. You can only correct the done quantities.'))
            # Unlinking a move line should unreserve.
            if ml.product_id.type == 'product' and not ml._should_bypass_reservation(ml.location_id) and not float_is_zero(ml.product_qty, precision_digits=precision):
                self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
        moves = self.mapped('move_id')
        res = super(models.Model, self).unlink()
        if moves:
            # Add with_prefetch() to set the _prefecht_ids = _ids
            # because _prefecht_ids generator look lazily on the cache of move_id
            # which is clear by the unlink of move line
            moves.with_prefetch()._recompute_state()
        return res   



