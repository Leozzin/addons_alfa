
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import json
import logging
import traceback
from requests.auth import HTTPBasicAuth
        
                
            
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    
    
    def write(self,vals):
        rec = super(ProductProduct, self).write(vals)
        
        print('----------write-----------')
        if 'can_be_sold_online' in vals:
            print(vals.get('can_be_sold_online'))
            if vals.get('can_be_sold_online') == True:
                self.send_status_sold_online(self.old_id, 1)
                
                sql = """ update product_template set can_be_sold_online = true """
                self.env.cr.execute(sql)

                
            if vals.get('can_be_sold_online') == False:
                self.send_status_sold_online(self.old_id, 0)
                
                sql = """ update product_template set can_be_sold_online = false """
                self.env.cr.execute(sql)
            
                
        if 'sale_ok' in vals:
            print(vals.get('sale_ok'))
            if vals.get('sale_ok') == True:
                self.send_status_sold_telesales(self.old_id, 1)
            if vals.get('sale_ok') == False:
                self.send_status_sold_telesales(self.old_id, 0)

        self.editProduct()

        return rec
    
    
    def editProduct(self):
        product_id = self.old_id
        stock = self.qty_available
        price = self.standard_price
        # raise Exception([product_id, stock, price])
        url = 'http://141.94.171.159/crm/Companies/majStockEdit'
        post_data = {"product_id": product_id, "stock": stock, "price": price}
        response = requests.post(url, json=post_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))


    def send_status_sold_online(self, product_id, status):
        username = 'alfaprint'
        password = '590-Alfaprint'
        
        try:
            url = "http://141.94.171.159/crm/companies/canBeSoldOnline/"+str(product_id)+"/"+str(status)+"/iscron=cron"
            print('----------url-----------')
            data=json.loads(requests.get(url, auth=(username, password)).content)
            print(data)
        
        except Exception as e:
                values = dict(
                    exception=e,
                    traceback=traceback.format_exc(),
                )
    
    
    def send_status_sold_telesales(self, product_id, status):
        username = 'alfaprint'
        password = '590-Alfaprint'
        
        try:
            url = "http://141.94.171.159/crm/companies/canBeSoldTelesales/"+str(product_id)+"/"+str(status)+"/iscron=cron"
            print('----------url-----------')
            data=json.loads(requests.get(url, auth=(username, password)).content)
            print(data)
            
        except Exception as e:
                values = dict(
                    exception=e,
                    traceback=traceback.format_exc(),
                )
    
    
    
    
    def import_products_cron_modified(self):
        username = 'alfaprint'
        password = '590-Alfaprint'
        
        sql = """ select max(custom_modified) from sale_order """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()
        print ("Hi import")
        if result[0]:
            formatted_datetime = str(result[0].date())+"_"+str(result[0].strftime("%H"))+"@"+str(result[0].strftime("%M"))+"@"+str(result[0].strftime("%S"))

            url = "http://141.94.171.159/crm/Companies/getProductsToOdoo/"+str(formatted_datetime)+"/iscron=cron"
            data=json.loads(requests.get(url, auth=(username, password)).content)
            print ("Hello data product url")
            print(data) 
            self.create_update_products(data) 
                      
    
    def import_products_cron(self):
        url = "http://141.94.171.159/crm/Companies/getProductsToOdoo/null/iscron=cron"
        username = 'alfaprint'
        password = '590-Alfaprint'

        data = json.loads(requests.get(url, auth=(username, password)).content)
        print(data)
        self.create_update_products(data)
        
    
    def create_update_products(self, data):
        ResPartner = self.env['res.partner']

        for rec in data:
            print ("Hello data product")
            print(rec)
            product_vals = {}
            
            if 'Product' in rec:
                product = rec.get('Product')
                
                product_vals['old_id'] = product_vals['default_code'] = product.get('id')
                
                if product.get('name') != None:
                    product_vals['name'] = product.get('name')
                else:
                    product_vals['name'] = 'product_empty'
                
                product_type = 'product'  
                if ('Extension' in product_vals['name']) or ('extension' in product_vals['name']) or ('Prise en main' in product_vals['name']) or (u"Volume d'impression" in product_vals['name']) or ('Prise en main' in product_vals['name']) or ("Transport sur Palette" in product_vals['name']):
                    product_type = 'service'
                print ("hello type")
                print (product.get('name'))
                print (product_vals['name'])
                print (product_type)
                product_vals['type'] = product_type
                
                if product.get('created') != None:
                    product_vals['created_datetime'] = datetime.strptime(product.get('created'), '%Y-%m-%d %H:%M:%S')
                if product.get('modified') != None:
                    product_vals['modified_datetime'] = datetime.strptime(product.get('modified'), '%Y-%m-%d %H:%M:%S')
                if product.get('sku') != None:
                    product_vals['sku'] = product.get('sku')
                if product.get('ean') != None:
                    product_vals['ean'] = product.get('ean')
                if product.get('upc') != None:
                    product_vals['upc'] = product.get('upc')
                if product.get('brand') != None:
                    product_vals['brand'] = product.get('brand')
                if product.get('bechlem_id') != None:
                    product_vals['bechlem_id'] = product.get('bechlem_id')
                if product.get('model_id') != None:
                    product_vals['model_id'] = product.get('model_id')
                if product.get('model') != None:
                    product_vals['model'] = product.get('model')
                if product.get('star') != None:
                    product_vals['star'] = product.get('star')
                if product.get('designation') != None:
                    product_vals['designation'] = product.get('designation')

            
                if 'Printer' in rec:
                    printer = rec.get('Printer')
                    product_vals['printer_id'] = printer.get('id')
                    
                    if printer.get('model') != None:
                        product_vals['printer_model'] = printer.get('model')
                    if printer.get('oem') != None:
                        product_vals['printer_oem'] = printer.get('oem')
                    if printer.get('partnr') != None:
                        product_vals['printer_partnr'] = printer.get('partnr')
                    if printer.get('technology') != None:
                        product_vals['technology'] = printer.get('technology')
                    if printer.get('technologie') != None:
                        product_vals['technologie'] = printer.get('technologie')
                    if printer.get('type') != None:
                        product_vals['printer_type'] = printer.get('type')
                    if printer.get('categorie') != None:
                        product_vals['printer_categorie'] = printer.get('categorie') 
                           
                    product_vals['multifonction'] = printer.get('multifonction')
                    product_vals['numerisation'] = printer.get('numerisation')
                    product_vals['copie'] = printer.get('copie') 
                    
                    if printer.get('rectoverso') != None:
                        product_vals['rectoverso'] = printer.get('rectoverso')
                    if printer.get('rectoverso_mode') != None:
                        product_vals['rectoverso_mode'] = printer.get('rectoverso_mode')
                    if printer.get('rectoverso_auto') != None:
                        product_vals['rectoverso_auto'] = printer.get('rectoverso_auto')
                    
                    product_vals['couleur'] = printer.get('couleur')
                    
                    if printer.get('format') != None:
                        product_vals['format'] = printer.get('format')
                    if printer.get('connectivite') != None:
                        product_vals['connectivite'] = printer.get('connectivite')
                    if printer.get('ppm_noir') != None:
                        product_vals['ppm_noir'] = float(printer.get('ppm_noir'))
                    if printer.get('ppm_couleur') != None:
                        product_vals['ppm_couleur'] = float(printer.get('ppm_couleur'))
                    #2021-12-02
                    if printer.get('date_fabrication') != None:
                        product_vals['date_fabrication'] = printer.get('date_fabrication')
                    product_vals['volume'] = float(printer.get('volume'))
                    
                    if printer.get('segmentation') != None:
                        product_vals['segmentation'] = printer.get('segmentation')
                    if printer.get('argument') != None:
                        product_vals['argument'] = printer.get('argument')
                    product_vals['contrat'] = int(printer.get('contrat'))
                    
                
                if 'Supply' in rec:
                    supply = rec.get('Supply')
                    
                    if supply.get('id') != None:
                        product_vals['supply_id'] = supply.get('id')
                    if supply.get('oem') != None:
                        product_vals['supply_oem'] = supply.get('oem')    
                    if supply.get('partnr') != None:
                        product_vals['supply_partnr'] = supply.get('partnr')
                    if supply.get('technology') != None:
                        product_vals['supply_technology'] = supply.get('technology')
                    if supply.get('type') != None:
                        product_vals['supply_type'] = supply.get('type')
                    if supply.get('color') != None:
                        product_vals['supply_color'] = supply.get('color')
                    if supply.get('model') != None:
                        product_vals['supply_model'] = supply.get('model')
                    if supply.get('duree_extension') != None:
                        product_vals['supply_duree_extension'] = supply.get('duree_extension')
                    if supply.get('capacity_page') != None:
                        product_vals['supply_capacity_page'] = supply.get('capacity_page')
                    if supply.get('capacity_ml') != None:
                        product_vals['supply_capacity_ml'] = supply.get('capacity_ml')
                    if supply.get('capacity_gr') != None:
                        product_vals['supply_capacity_gr'] = supply.get('capacity_gr')
                    

                product_exists = self.search([('old_id','=',product.get('id'))], order='id desc', limit=1)

                prod = None
                if not product_exists:
                    print('-----create-------')
                    prod = self.create(product_vals)
                else:
                    print('-----update-------')
                    prod = product_exists.update(product_vals)
                    prod = product_exists
                
                if prod.model == 'Printer' and prod.technologie == 'CISS':
                    prod.categ_id = self.get_categ_id('ALFA TANK')
                elif prod.model == 'Printer' and prod.technologie != 'CISS':
                    prod.categ_id = self.get_categ_id('NORMAL PRINTER')
                elif prod.model == 'Supply' and prod.supply_type == 'AP':
                    prod.categ_id = self.get_categ_id('AP')
                elif prod.model == 'Supply' and prod.supply_type == 'COM':
                    prod.categ_id = self.get_categ_id('COM')
                elif prod.model == 'Supply' and prod.supply_type == 'COM2':
                    prod.categ_id = self.get_categ_id('COM 2')
                elif prod.model == 'Supply' and prod.supply_type == 'OEM':
                    if 'Poche' in prod.name:
                        prod.categ_id = self.get_categ_id('Poches')
                    elif ('rebuilt' in prod.name) or ('REBUILT' in prod.name):
                        prod.categ_id = self.get_categ_id('REBUILT')
                    else:
                        prod.categ_id = self.get_categ_id('OEM')
                    
                        
                
                print(prod)    
    
    
    def get_categ_id(self, name):
        product_category = self.env['product.category'].search([('name','=',name)], order='id desc', limit=1)
        
        if product_category:
            categ_id = product_category.id
        else:
            product_category = self.env['product.category'].search([('name','=','All')], order='id desc', limit=1)
            categ_id = product_category.id
        
        return categ_id
    
    
    def compute_qty_not_validated_yet(self):
        print('-----------------------------hello')
        StockMove = self.env['stock.move']
        
        delivery_picking_id = self.env['stock.picking.type'].search([('sequence_code','=','OUT')], limit=1)
        dropshipping_picking_id = self.env['stock.picking.type'].search([('sequence_code','=','DRS')], limit=1)

        
        for rec in self:
            qty_not_validated = 0
            move_ids = StockMove.search([('product_id','=',rec.id),('picking_id.state','not in',('cancel','done')),
                                         ('picking_id.picking_type_id','=',delivery_picking_id.id)])
            
            if move_ids:
                for move_id in move_ids:
                    qty_not_validated += move_id.product_uom_qty
            print (qty_not_validated)
            
                
            rec.qty_not_validated_yet = qty_not_validated
            
    
    old_id = fields.Char(string='Old ID')  
    created_datetime = fields.Datetime(string='Created')
    modified_datetime = fields.Datetime(string='Modified')
    sku = fields.Char(string='SKU')
    ean = fields.Char(string='EAN')
    upc = fields.Char(string='UPC')
    brand = fields.Char(string='Brand')
    bechlem_id = fields.Char(string='Bechlem ID')
    model_id = fields.Char(string='Model ID') 
    model = fields.Char(string='Model') 
    star = fields.Char(string='Star')
    designation = fields.Char(string='designation')
    
#     printer_fields
    printer_id = fields.Char(string='Printer ID')
    printer_model = fields.Char(string='Printer Model')
    printer_oem = fields.Char(string='Printer OEM')
    printer_partnr = fields.Char(string='Printer Partnr')
    technology = fields.Char(string='Technology')
    technologie = fields.Char(string='Technologie')
    printer_type = fields.Char(string='Printer Type')
    printer_categorie = fields.Char(string='Printer Categorie')
    multifonction = fields.Boolean(string='Multifonction')
    numerisation = fields.Boolean(string='Numerisation')
    copie = fields.Boolean(string='Copie')
    rectoverso = fields.Char(string='Rectoverso')
    rectoverso_mode = fields.Char(string='Rectoverso Mode')
    rectoverso_auto = fields.Char(string='Rectoverso Auto')
    couleur = fields.Boolean(string='couleur')
    format = fields.Char(string='Format')
    connectivite = fields.Char(string='connectivite')
    ppm_noir = fields.Float(string='PPM Noir')
    ppm_couleur = fields.Float(string='PPM Couleur')
    date_fabrication = fields.Date(sting='Date Fabrication')
    volume = fields.Float(string='Volume')
    segmentation = fields.Char(string='Segmentation')
    argument =  fields.Char(string='Argument')
    contrat = fields.Integer(string='contrat')
    
    #supply fields
    supply_id = fields.Char(string='Supply ID')
    supply_oem = fields.Char(string='Supply OEM')
    supply_partnr = fields.Char(string='Supply Partnr')
    supply_technology = fields.Char('Supply Technology')
    supply_type = fields.Char('Supply Type')
    supply_color = fields.Char('Supply Color')
    supply_model = fields.Char('Supply Model')
    supply_duree_extension = fields.Char('Duree Extension')
    supply_capacity_page = fields.Char('Capacity Page')
    supply_capacity_ml = fields.Char('Capacity ML')
    supply_capacity_gr = fields.Char('Capacity GR')
    
    qty_not_validated_yet = fields.Float(compute='compute_qty_not_validated_yet')
    can_be_sold_online = fields.Boolean(string='Can be Sold Online')
    capacity_ml=fields.Char('Capacity')
    
    
    
    
    
    


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    
    
    can_be_sold_online = fields.Boolean(string='Can be Sold Online')

    def write(self,vals):
        rec = super(ProductTemplate, self).write(vals)
        
        product_ids = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
        print('----------write-----------')
        if 'can_be_sold_online' in vals:
            print(vals.get('can_be_sold_online'))
            if vals.get('can_be_sold_online') == True:
                for product_id in product_ids:
                    product_id.write({'can_be_sold_online': True})
                    
            if vals.get('can_be_sold_online') == False:
                for product_id in product_ids:
                    product_id.write({'can_be_sold_online': False})

                
        if 'sale_ok' in vals:
            print(vals.get('sale_ok'))
            if vals.get('sale_ok') == True:
                for product_id in product_ids:
                    product_id.update({'sale_ok': True})
                     
            if vals.get('sale_ok') == False:
                for product_id in product_ids:
                    product_id.update({'sale_ok': False})
                
        
                     
        return rec
    
    
    
    
    def cron_api_fun(self):
        url = 'http://141.94.171.159/crm/Companies/getProductsProvidersToOdoo/iscron=cron'
        username = 'alfaprint'
        password = '590-Alfaprint'
        product_obj=self.env['product.template']
        partner_obj=self.env['res.partner']
        purchase_obj=self.env['purchase.order']
        sale_obj = self.env['sale.order']
        data=json.loads(requests.get(url, auth=(username, password)).content)
        print(data)
        count=0
        for rec in data:
            logging.info("Running command stock count %s", count)
            count=count+1
            product_id = product_obj.search([('default_code','=',rec['product_id']),('type','not in',['consu','service'])],limit=1)
            if product_id:
                if rec['stock'] != None:
                    need_quantity=int(rec['stock'])-product_id.qty_available
                    vendor_id = partner_obj.search([('old_api_id','=',int(rec['provider_id']))],limit=1)
                    if vendor_id:
                        if need_quantity >0:
                            purchase_order_line={'product_id':product_id.product_variant_id.id,'product_qty':need_quantity,'price_unit':float(rec['price'])}
                            purchase_order=purchase_obj.create({'partner_id':vendor_id.id,'order_line':[(0,0,purchase_order_line)]})
                            purchase_order.button_confirm()
                            picking_ids=purchase_order.mapped('picking_ids')
                            for picking in picking_ids:
                                for lines in picking.move_ids_without_package:
                                    lines.write({'quantity_done': lines.product_uom_qty})
                                picking.button_validate()
                            
                product_upate={}
                if rec['normal_price'] != None:
                    product_upate['list_price']=float(rec['normal_price'])
                if rec['price']!=None:
                    product_upate['standard_price']=float(rec['price'])
                if int(rec['provider_id'][0])!=1:
                    route_id = self.env['stock.location.route'].search([('name','=','Dropship')])
                    product_upate['route_ids']=[(6,0,route_id.ids)]


                product_id.write(product_upate)
    
