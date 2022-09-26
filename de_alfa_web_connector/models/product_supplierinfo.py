from datetime import datetime
from odoo import models, fields, api, _
import requests
import json
from requests.auth import HTTPBasicAuth
        


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    
    def create_stock_quant(self):
        StockQuant = self.env['stock.quant']
        
        quant_id = StockQuant.search([('product_id','=',self.product_id.id),('location_id.usage','=','internal')], limit=1)
        
        if not quant_id:
            quant_id = StockQuant.create({
                'product_id': self.product_id.id,
                'location_id': 8,
                'quantity': self.min_qty,
                })
        else:
            quant_id.update({
                'product_id': self.product_id.id,
                'location_id': 8,
                'quantity': quant_id.quantity + self.min_qty,
                })
            
        print('-----quantity----',quant_id.quantity)
    
    
    
    def send_stock_to_website(self):
        data_list = []
        
        sql = """
            select distinct product_id from stock_quant 
            where location_id in (select id from stock_location where usage='internal')
        """
        self.env.cr.execute(sql)
        product_ids = self.env.cr.fetchall()
        
        new_lst = []
        for ls in product_ids:
            new_lst.append(ls[0])
        
        product_ids = self.env['product.product'].browse(new_lst)
        
        
        
        sql = """
            select b.id from product_template a,
            product_product b
            where a.id = b.product_tmpl_id and type = 'service'
            and old_id is not null
        """
        self.env.cr.execute(sql)
        service_product_ids = self.env.cr.fetchall()
        print(service_product_ids)
        
        new_lst2 = []
        for ls in service_product_ids:
            new_lst2.append(ls[0])
        
        service_products = self.env['product.product'].browse(new_lst2)
        product_ids = product_ids + service_products
        
        for product_id in product_ids:
            dict = {}
            arrivage=[]
            
            
            if product_id.old_id and product_id.active==True:
                print('available qty-----',product_id.qty_available)
                print('not validated yet------',product_id.qty_not_validated_yet)
                if product_id.type == 'service':
                    dict['product_id'] = product_id.old_id
                    dict['onhand_qty'] = 100
                    dict['price'] = product_id.standard_price
                    dict['incoming_qty'] = 0
                    dict['incoming_date'] = '-'
                    dict['arrivage'] = arrivage
                elif product_id.sale_ok == False:
                    dict['product_id'] = product_id.old_id
                    dict['onhand_qty'] = 0
                    dict['price'] = product_id.standard_price
                    dict['incoming_qty'] = 0
                    dict['incoming_date'] = '-'
                    moves = self.env['stock.move'].search(
                        [('product_id', '=', product_id.id), ('state', '=', 'assigned'), ('picking_type_id', '=', 1)])
                    for m in moves:
                        if m.product_uom_qty !=0:
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
                    if moves:
                        dict['incoming_date'] = (min(p.date for p in moves)).strftime('%Y-%m-%d')
                    dict['arrivage'] = arrivage
                else:
                    moves=self.env['stock.move'].search([('product_id','=',product_id.id),('state','=','assigned'),('picking_type_id','=',1)])
                    dict['incoming_date'] = '-'
                    for m in moves:
                        if m.product_uom_qty !=0:
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
                                    ['1',m.purchase_line_id.price_unit, m.product_uom_qty,m.date.strftime('%Y-%m-%d')
                                    , m.incertain])


                    if moves:
                        dict['incoming_date'] = (min(p.date for p in moves)).strftime('%Y-%m-%d')
                    

                    dict['product_id'] = product_id.old_id
                    dict['onhand_qty'] = product_id.qty_available - product_id.qty_not_validated_yet
                    dict['price'] = product_id.standard_price
                    dict['incoming_qty'] = product_id.incoming_qty
                    dict['arrivage']=arrivage
                data_list.append(dict)


        for data in data_list:

            url = 'http://141.94.171.159/crm/Companies/majStock?iscron=cron'
            
            #post_data = {'price':data.get('price'), 'product_id': data.get('product_id'), 'stock': data.get('onhand_qty')}
            post_data = {'price':data.get('price'), 'product_id': data.get('product_id'), 'stock': data.get('onhand_qty'),'arrivage': data.get('arrivage')}
            response = requests.post(url, json=post_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))
                    
                    
                    
    def import_product_vendors_link_cron_modified(self):
        username = 'alfaprint'
        password = '590-Alfaprint'
        
        sql = """ select max(modified_datetime) from product_supplierinfo """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()
        
        if result[0]:
            formatted_datetime = str(result[0].date())+"_"+str(result[0].strftime("%H"))+"@"+str(result[0].strftime("%M"))+"@"+str(result[0].strftime("%S"))
            print(formatted_datetime)
            
            url = "http://141.94.171.159/crm/Companies/getProductsProvidersToOdoo/"+str(formatted_datetime)+"/iscron=cron"
            print('----------url-----------')
            data=json.loads(requests.get(url, auth=(username, password)).content)
            print(data)
            self.create_update_product_vendors_link(data)
            


    def import_product_vendors_link_cron(self):
        url = "http://141.94.171.159/crm/Companies/getProductsProvidersToOdoo/null/iscron=cron"
        username = 'alfaprint'
        password = '590-Alfaprint'

        data = json.loads(requests.get(url, auth=(username, password)).content)
        print(data)
        self.create_update_product_vendors_link(data)
        
        
    
    def create_update_product_vendors_link(self, data):
        ResPartner = self.env['res.partner']
        ProductProduct = self.env['product.product']
 
        for rec in data:
            print(rec)
            supplier_vals = {}
            
            partner_id = ResPartner.search([('old_api_id','=',rec.get('provider_id'))], order='id desc', limit=1)
            
            if partner_id:
                supplier_vals['old_id'] = rec.get('id')
                supplier_vals['provider_id'] = rec.get('provider_id')
                supplier_vals['name'] = partner_id.id
                supplier_vals['code'] = rec.get('code')
                supplier_vals['product_code'] = rec.get('code')
                
                if rec.get('created') != None:
                    supplier_vals['created_datetime'] = datetime.strptime(rec.get('created'), '%Y-%m-%d %H:%M:%S')
                if rec.get('modified') != None:
                    supplier_vals['modified_datetime'] = datetime.strptime(rec.get('modified'), '%Y-%m-%d %H:%M:%S')
                if rec.get('promo') != False:
                    supplier_vals['promo'] = rec.get('promo')
                if rec.get('stock') != None:
                    supplier_vals['min_qty'] = float(rec.get('stock'))
                if rec.get('price') != None:
                    supplier_vals['price'] = float(rec.get('price'))
                if rec.get('normal_price') != None:
                    supplier_vals['normal_price'] = float(rec.get('normal_price'))
                if rec.get('selling_price') != None:
                    supplier_vals['selling_price'] = float(rec.get('selling_price'))
                if rec.get('stock_promo') != None:
                    supplier_vals['stock_promo'] = rec.get('stock_promo')
                if rec.get('cotation') != None:
                    supplier_vals['cotation'] = rec.get('cotation')
                if rec.get('capacity_pg') != None:
                    supplier_vals['capacity_pg'] = rec.get('capacity_pg')
                if rec.get('capacity_ml') != None:
                    supplier_vals['capacity_ml'] = rec.get('capacity_ml')
                if rec.get('capacity_gr') != None:
                    supplier_vals['capacity_gr'] = rec.get('capacity_gr')
                if rec.get('bechlem') != None:
                    supplier_vals['bechlem'] = rec.get('bechlem')
                
                
                product_id = ProductProduct.search([('old_id','=',int(rec.get('product_id')))], order='id desc', limit=1)
                if product_id:
                    supplier_vals['product_tmpl_id'] = product_id.product_tmpl_id.id
                    supplier_vals['product_id'] = product_id.id
                
            
                record_exists = self.search([('old_id','=',rec.get('id'))], order='id desc', limit=1)
                if not record_exists:
                    print('-----create-------')
                    sup = self.create(supplier_vals)
                    
                else:
                    print('-----update-------')
                    record_exists.update(supplier_vals)
                    sup = record_exists
                print(sup)
#                 sup.create_stock_quant()   
#                 print(sup)
                        
                    
    
    old_id = fields.Char(string='Old ID')  
    created_datetime = fields.Datetime(string='Created')
    modified_datetime = fields.Datetime(string='Modified')
    provider_id = fields.Char(string='Provider ID')
    custom_product_id = fields.Integer(string='Custom Product ID')
    code = fields.Char(string='Code')
    promo = fields.Char(string='Promo')
    normal_price = fields.Float(string='Normal Price')
    selling_price = fields.Float(string='Selling Price')
    stock_promo = fields.Char(string='Stock Promo')
    cotation = fields.Char(string='Cotation')
    capacity_pg = fields.Char(string='Capacity pg')
    capacity_ml = fields.Char(string='Capacity ml')
    capacity_gr = fields.Char(string='Capacity gr')
    bechlem = fields.Char(string='Bechlem')
    
#  'price': '12.00', 
#  'stock': '100', 