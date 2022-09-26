from odoo import _, api, fields, models
import json
import requests
from datetime import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'



    @api.depends('picking_ids','picking_ids.state','picking_ids.delivery_state','picking_ids.picking_type_id')
    def _get_picking(self):
        for record in self:
            if record.picking_ids:
                record.nbr_ready=len(record.picking_ids.filtered(lambda p: p.state == 'assigned' and p.picking_type_id.sequence_code=='OUT'  ))
            else:
                record.nbr_ready =0



    nbr_ready = fields.Integer(compute='_get_picking',store=True)
    picking_ids=fields.One2many('stock.picking','partner_id')

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = "nbr_ready desc, partner_id"
    
    def correct_test(self):
        for i in self.env['res.partner'].search([]):   
            i._get_picking()
    

 

    def correct_comment(self):
        for i in self.env['res.partner'].search([]):   
            i._get_picking()

        """url = "http://141.94.171.159/crm/Companies/getCommentsToOdoo/"
        username = 'alfaprint'
        password = '590-Alfaprint'
        data = json.loads(requests.get(url, auth=(username, password)).content)
        for d in data:
            print (d)
            order=self.env['sale.order'].search([('old_id','=',d['Comment']['order_id'])])
            if order:
                user_id=self.env['res.users'].search([('id','=',int(d['Comment']['user_id']))])
                if user_id:
                    exist_comment = self.env['mail.message'].search(
                        [('res_id', '=', order[0].id), ('model', '=', 'sale.order'),
                         ('date', '=', datetime.strptime(d['Comment']['created'], '%Y-%m-%d %H:%M:%S'))])
                    if not exist_comment:
                        new_message = order.message_post(author_id=user_id[0].partner_id.id,
                                                         body=d['Comment']['comment'],
                                                         message_type='comment')
                        print(new_message)
                        new_message.update({'date': datetime.strptime(d['Comment']['created'], '%Y-%m-%d %H:%M:%S'),
                                            })"""








    nbr_ready=fields.Integer(related='partner_id.nbr_ready',store=True)
