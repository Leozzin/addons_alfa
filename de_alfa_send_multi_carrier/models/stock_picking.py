from odoo import fields, models
import base64
import os
import io
from PyPDF2 import PdfFileReader, PdfFileMerger
import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime
from odoo.exceptions import UserError
from odoo import _



class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_country=fields.Char(related="partner_id.delivery_country",store=True,string="Countr")

    def correct_country(self):
        #for i in self.env['res.partner'].search([('billing_country','!=',False)]):
         #   search=self.env['res.country'].search(['|',('code','=',i.billing_country),('name','=ilike',i.billing_country)])
         #   if search:
          #      i.country_id=search[0].id
        for i in self.env['res.partner'].search([]):
            i._get_picking()
            
    def correct_picking(self):
        for i in self.env['res.partner'].search([]):   
            i._get_picking()



    def send_product_tracking_to_website(self, carrier_id, tracking, detail_order_id):
        
        url = 'http://141.94.171.159/crm/Companies/majTracking?iscron=cron'
        post_data = {'detail_order_id':detail_order_id, 'carrier': str(
            carrier_id.name), 'tracking': tracking}
        response = requests.post(url, json=post_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))

    def tracking_send(self):
        for p in self:
            for move_line in p.move_line_ids_without_package:
                if move_line.result_package_id:
                    if move_line.result_package_id.carrier_tracking_ref:
                        self.send_product_tracking_to_website(p.carrier_id,
                                                              move_line.result_package_id.carrier_tracking_ref,
                                                              move_line.move_id.detail_order_id)
    def update_tracking(self):
        for s in self.env['stock.picking'].search([('carrier_id','=',2)]):
            s.tracking_state_update()
    def action_all_picking(self,picking):
            picking = picking.filtered(lambda s: s.pdf_label)
            if picking:
                dist = r'/opt/odoo/addons_alfa/de_alfa_ws_tnt/static/description/files/tnt_tmp'
                os.chdir(dist)
                print(os.listdir())
                for p in picking:
                    with open(p.origin+'.pdf', 'wb') as f:
                        f.write(base64.b64decode(p.pdf_label))
                    f.close()
                merger = PdfFileMerger(strict=True)

                for p in picking:
                    merger.append(PdfFileReader(open(p.origin+'.pdf', 'rb')),import_bookmarks=False)
                now = datetime.now()


                # dd/mm/YY H:M:SSS
                dt_string = now.strftime("%d-%m-%Y-%H:%M")
                name= 'TNT'+ str(dt_string)
                print (name)
                merger.write(name+'.pdf')
                merger.close()
                #for p in picking:
                    #os.remove(p.origin+'.pdf')

                attachment_id=self.env["ir.attachment"].create(
                    {

                        "name": name+'.pdf',
                        "type": "url",
                        "url": '/de_alfa_ws_tnt/static/description/files/tnt_tmp/' + name+'.pdf',
                        # "url": "/theme_default\static/description/icon.png",
                      # "res_model": 'stock.picking',
                      #  "res_id": picking[0].id,
                    }
                )

                download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')

                url=str(base_url) + str(download_url)
                print(url)
                file = os.path.join('/opt/odoo/addons_alfa/de_alfa_ws_tnt/files/tnt_tmp', name + '.pdf')
                os.system('lp ' + file)
                #return {
                #    'type': 'ir.actions.act_url',
                #    'url': url,
                #    'target': 'new',
                #}
            return True
    def action_all_in_pdf(self):
            picking = self.env['stock.picking'].browse(self.env.context.get('active_ids')).filtered(lambda s: s.pdf_label)
            if picking:
                dist = r'/opt/odoo/addons_alfa/de_alfa_ws_tnt/static/description/files/tnt_tmp'
                os.chdir(dist)
                print(os.listdir())
                for p in picking:
                    with open(p.origin+'.pdf', 'wb') as f:
                        f.write(base64.b64decode(p.pdf_label))
                    f.close()
                merger = PdfFileMerger(strict=True)

                for p in picking:
                    merger.append(PdfFileReader(open(p.origin+'.pdf', 'rb')),import_bookmarks=False)
                now = datetime.now()


                # dd/mm/YY H:M:SSS
                dt_string = now.strftime("%d-%m-%Y-%H:%M")
                name= 'TNT'+ str(dt_string)
                print (name)
                merger.write(name+'.pdf')
                merger.close()
                #for p in picking:
                    #os.remove(p.origin+'.pdf')

                attachment_id=self.env["ir.attachment"].create(
                    {

                        "name": name+'.pdf',
                        "type": "url",
                        "url": '/de_alfa_ws_tnt\static/description/files/tnt_tmp/' + name+'.pdf',
                        # "url": "/theme_default\static/description/icon.png",
                      # "res_model": 'stock.picking',
                      #  "res_id": picking[0].id,
                    }
                )

                download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')

                url=str(base_url) + str(download_url)
                print(url)
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }



    def action_move_to_reparation(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        print('action_move_to_reparation')
        pickings = self.env['stock.picking'].sudo().browse(self.env.context.get('active_ids'))
        if pickings:
            for p in pickings:
                print(">>>>>picking: ", p)
                list_products = []
                for item in p.move_ids_without_package:
                    print(">>>>>> ", item.product_id.id)
                    product = self.env['product.product'].sudo().browse([('id', '=', item.product_id.id)])
                    list_products.append({
                        "product_id": item.product_id.id,
                        "product_uom": item.product_uom.id,
                        "quantity_done": item.quantity_done,
                        "forecast_availability": item.forecast_availability,
                        "product_uom_qty": item.product_uom_qty,
                        "name": item.name,
                        "location_id": item.location_id.id,
                        "location_dest_id": item.location_dest_id.id
                    })
                stock_move_reparation = env['stock.move'].sudo().create(list_products)
                print(">>>>>>>>>>>stock move created!")
                picking_reparation_data = {
                    "partner_id": (p.partner_id.id,),
                    "picking_type_id": (43,),
                    "location_id": (54,),
                    "location_dest_id": (p.location_dest_id.id,),
                    "origin": p.origin
                }
                picking_reparation = env['stock.picking'].sudo().create(picking_reparation_data)
                print(">>>>>>>>>>>picking created!")
                for item in stock_move_reparation:
                    item.picking_id = picking_reparation
                picking_reparation.move_ids_without_package = stock_move_reparation
                v = picking_reparation.action_confirm()
                picking_reparation.action_toggle_is_locked()
                p.unlink()
            print(">>>>>send to reparation done!<<<<<")
        return {
                    'type': 'ir.actions.act_url',
                    'url': "/web#action=306&active_id=1&model=stock.picking&view_type=list&cids=&menu_id=170",
                    'target': 'self',
                }
    def action_move_to_reparation2(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        pickings = self.env['stock.picking'].sudo().browse(self.env.context.get('active_ids'))
        if pickings:
            for p in pickings:
                for item in p.move_ids_without_package:
                    product_data = {
                        "product_id": item.product_id.id,
                        "product_uom": item.product_uom.id,
                        "quantity_done": item.quantity_done,
                        "forecast_availability": item.forecast_availability,
                        "product_uom_qty": item.product_uom_qty,
                        "name": item.name,
                        "location_id": item.location_id.id,
                        "location_dest_id": item.location_dest_id.id
                    }
                    stock_move_reparation = env['stock.move'].sudo().create([product_data])
                    picking_reparation_data = {
                        "partner_id": (p.partner_id.id,),
                        "picking_type_id": (16,),
                        "location_id": (2,),
                        "location_dest_id": (p.location_dest_id.id,),
                        "origin": p.origin
                    }
                    picking_reparation = env['stock.picking'].sudo().create(picking_reparation_data)
                    for prod in stock_move_reparation:
                        prod.picking_id = picking_reparation
                    picking_reparation.move_ids_without_package = stock_move_reparation
                    v = picking_reparation.action_confirm()
                    picking_reparation.action_toggle_is_locked()
                p.unlink()
            return {
                'type': 'ir.actions.act_url',
                'url': "/web#action=306&active_id=1&model=stock.picking&view_type=list&cids=&menu_id=170",
                'target': 'self',
            }

    def action_change_location_to_amz(self):
        pickings = self.env['stock.picking'].sudo().browse(self.env.context.get('active_ids'))
        if pickings:
            for picking in pickings:
                picking.sudo().write({'location_id': 56})
                for item in picking.move_line_ids_without_package:
                    item.sudo().write({'location_id': 56})

    def send_carrier(self):
        # record = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        # num = 0
        # for r in record:
        #     print ("rescord")
        #     print (r)
        #     print (num)
        #     if r.package_ids:
        #         num = num + len(record.package_ids)
        #     else:
        #         num = num + 1
        # print ("Hello num")
        # print (num)
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model' :'stock.carrier.transfer',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': dict(self.env.context, default_pick_ids=[(4, p.id) for p in self]),

        }

    def test(self):
        raise UserError(_("Don't touch \"Test\" action! -_-"))
        query = """select origin from stock_picking where state='cancel' group by origin"""
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        res = []
        for r in result:
            res.append(r[0])
        for origin in res:
            records = self.env['stock.picking'].sudo().search([('origin', '=', origin), ('state', '=', 'cancel')])
            pickings = self.env['stock.picking'].sudo().browse(records.ids[:-1])
            pickings.sudo().unlink()

    def resend_carrier(self):
        # record = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        # num = 0
        # for r in record:
        #     print ("rescord")
        #     print (r)
        #     print (num)
        #     if r.package_ids:
        #         num = num + len(record.package_ids)
        #     else:
        #         num = num + 1
        # print ("Hello num")
        # print (num)
        records = self.env['stock.picking'].sudo().browse(self.ids)
        for picking in records:
            picking.sudo().write({"delivery_state": None})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model' :'stock.carrier.transfer',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': dict(self.env.context, default_pick_ids=[(4, p.id) for p in self]),

        }