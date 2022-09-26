# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import json



class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    def import_comment_avoir_cron(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

        sql = """ select max(date) from mail_message where model='helpdesk.ticket' and subject like '%Re:%'"""

        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()

        if result[0]:
            formatted_datetime = str(result[0].date()) + "_" + str(result[0].strftime("%H")) + "@" + str(
                result[0].strftime("%M")) + "@" + str(result[0].strftime("%S"))
            print(formatted_datetime)
            # formatted_datetime = "2022-01-01_00@00@00"
            # url = "http://141.94.171.159/crm/Companies/getCommentsToOdoo/" + str(
            # formatted_datetime) + "/avoir/iscron=cron"

            url = "http://141.94.171.159/crm/Companies/getCommentsToOdoo"

            data = json.loads(requests.get(url, auth=(username, password)).content)

            self.create_update_comments_avoir(data)
        print(">>>>> END IMPORT COMMENTS AVOIR <<<<<")

    def create_update_comments_avoir(self, data):
        list_comments = []
        for comment in data:
            comment_id = comment['Comment']['id']
            order_id = comment['Comment']['order_id']
            body = comment['Comment']['comment']
            created_date = comment['Comment']['created']
            user_id = comment['Comment']['user_id']
            ticket = self.env['helpdesk.ticket'].sudo().search([('number', '=', order_id)], limit=1)
            user = self.env['res.users'].sudo().search([('id', '=', user_id)], limit=1)
            if ticket:
                comment_exist = self.env['mail.message'].sudo().search([('old_api_id', '=', comment_id)], limit=1)
                if not comment_exist:
                    # print(order_id)
                    try:
                        data = {
                            "subject": f"Re: {order_id} - {ticket.name}",
                            "body": f"<p>{body}</p>",
                            "parent_id": 0,
                            "model": "helpdesk.ticket",
                            "res_id": ticket.id,
                            "record_name": f"Re: {order_id} - {ticket.name}",
                            "message_type": "comment",
                            "subtype_id": 2,
                            "email_from": f"<{user.login}>",
                            "author_id": user.partner_id.id,
                            "create_uid": user.id,
                            "write_uid": user.id,
                            "old_api_id": comment_id,
                            "date": created_date,
                        }
                        list_comments.append(data)
                        comments = self.env['mail.message'].sudo().create(data)
                    except:
                        raise Exception(f'ID: {comment_id}')

    def import_comment_cron(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

        sql = """ select max(date) from mail_message where model='sale.order'"""
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()
        print("Hi import")
        if result[0]:
            formatted_datetime = str(result[0].date()) + "_" + str(result[0].strftime("%H")) + "@" + str(
                result[0].strftime("%M")) + "@" + str(result[0].strftime("%S"))
            print(formatted_datetime)

            # url = "http://141.94.171.159/crm/Companies/getCommentsToOdoo/" + str(
            #     formatted_datetime) + "/iscron=cron"
            url = "http://141.94.171.159/crm/Companies/getCommentsToOdoo/" + str(
                formatted_datetime) + "/iscron=cron"
            data = json.loads(requests.get(url, auth=(username, password)).content)

            self.create_update_comment(data)

    def create_update_comment(self,data):

        for d in data:
            print(d)
            order = self.env['sale.order'].search([('old_id', '=', d['Comment']['order_id'])])
            if order:
                user_id = self.env['res.users'].search([('id', '=', int(d['Comment']['user_id']))])
                if user_id:
                    exist_comment=self.env['mail.message'].search([('res_id','=',order[0].id),('model','=','sale.order'),('date','=',datetime.strptime(d['Comment']['created'], '%Y-%m-%d %H:%M:%S'))])
                    if not exist_comment:
                        new_message = order.message_post(author_id=user_id[0].partner_id.id,
                                                     body=d['Comment']['comment'],
                                                     message_type='comment')
                        print(new_message)
                        new_message.update({'date': datetime.strptime(d['Comment']['created'], '%Y-%m-%d %H:%M:%S'),
                                            })
    
    
    def import_customers_products_orders(self):
        """run 5 cron at a time""" 
        self.import_customers_cron_modified()
        self.env['product.product'].import_products_cron_modified()
        print("hi1test")
        self.env['sale.order'].import_sale_orders_cron_modified()
        self.import_comment_cron()
        print("hi1test2")
        self.env['sale.order'].import_sale_avoirs_cron_modified()
        print("hi1test3")
        
        self.env['sale.order'].create_purchase_order_from_sale_modified()
        print("hi1test4")
    
    # def import_customers_products_orders(self):
    #     """run 5 cron at a time""" 
    #     try:
    #         self.import_customers_cron_modified()
    #     except:
    #         raise Exception('Error in import customers')
    #     try:
    #         self.env['product.product'].import_products_cron_modified()
    #     except:
    #         raise Exception('Error in import products')
    #     print("hi1test")
    #     try:
    #         self.env['sale.order'].import_sale_orders_cron_modified()
    #     except:
    #         raise Exception('Error in import sale_orders')
    #     try:
    #         self.import_comment_cron()
    #     except:
    #         raise Exception('Error in import comments')
    #     print("hi1test2")
    #     try:
    #         self.env['sale.order'].import_sale_avoirs_cron_modified()
    #     except:
    #         raise Exception('Error in import sale_avoirs')
    #     print("hi1test3")
    #     try:
    #         self.env['sale.order'].create_purchase_order_from_sale_modified()
    #     except:
    #         raise Exception('Error in import purchase_order')
    #     print("hi1test4")

    
    
    def import_customers_cron_modified(self):
        username = 'alfaprint'
        password = '590-Alfaprint'
        
        sql = """ select max(custom_modified) from res_partner """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchone()
        # self.send_email_error(f'Error in Cron create update customers! ID: {1546}')
        if result[0]:
            formatted_datetime = str(result[0].date())+"_"+str(result[0].strftime("%H"))+"@"+str(result[0].strftime("%M"))+"@"+str(result[0].strftime("%S"))
            print(formatted_datetime)
            
            # url = "http://141.94.171.159/crm/Companies/getCompaniesToOdoo/"+str(formatted_datetime)+"/iscron=cron"
            url = "http://141.94.171.159/crm/Companies/getCompaniesToOdoo/"+str(formatted_datetime)+"/iscron=cron"
            print('----------url-----------')
            data=json.loads(requests.get(url, auth=(username, password)).content)
            print(data)
            
            self.create_update_customers(data)
            
#         2022-01-25 09:20:47
#         2022-01-15_12@15@58
        
        
    
    def import_customers_cron(self):
        username = 'alfaprint'
        password = '590-Alfaprint'

#         url="http://141.94.171.159/crm/Companies/getCompaniesToOdoo/iscron=cron"
        # url = "http://141.94.171.159/crm/Companies/getCompaniesToOdoo/null/iscron=cron"
        url = "http://141.94.171.159/crm/Companies/getCompaniesToOdoo/null/iscron=cron"
        print('----------url-----------')
        data=json.loads(requests.get(url, auth=(username, password)).content)
        print(data)
        self.create_update_customers(data)

    def send_email_error(self, subject):
        mail_obj = self.env['mail.mail']
        values = {}
        values.update({'subject': subject})
        values.update({'email_to': 'hosni@alfaprint.fr'})
        values.update({'body_html': subject })
        values.update({'body': subject })
        
        msg_id = mail_obj.create(values)
        raise Exception(msg_id)
        if msg_id:
            mail_obj.send([msg_id])
    
    def create_update_customers(self, data):
        ResUsers = self.env['res.users']
        count = 0
        for rec in data:
            try:
                company = rec['Company']
                c = company['id']
                print(company)
                
                count = count + 1
                country=False
                if company.get('billing_country') != None:
                    search=self.env['res.country'].search(['|',('code','=',company.get('billing_country')),('name','=ilike',company.get('billing_country'))])
                    if search:
                        country=search[0].id
                billing_country=company.get('billing_country')   
                if company.get('billing_country') in ['france','france ','France','France ','FRANCE','FRANCE ','FR','fr','',None]:
                    billing_country='FR'
                if company.get('billing_country') in ['LUXEMBOURG','LUXEMBOURG ','Luxembourg','Luxembourg ','LU']:
                    billing_country='LU'
                if company.get('billing_country') in ['BELGIQUE','BELGIQUE ','Belgique','Belgique ','belgique','belgique ','BE']:
                    billing_country='BE'
                if company.get('billing_country') in ['ITALIE','ITALIE ','Italie','Italie ','italie','italie ','IT ']:
                    billing_country='IT'
                if company.get('billing_country') in ['Allemagne','Allemagne ','ALLEMAGNE','ALLEMAGNE ','allemagne','allemagne ','DE ']:
                    billing_country='DE'
                if company.get('billing_country') in ['Espagne','Espagne ','ESPAGNE','ESPAGNE ','espagne','espagne ','ES ']:
                    billing_country='ES'
                if company.get('billing_country') in ['Monaco','Monaco ','MONACO','MONACO ','monaco','monaco ','MC ']:
                    billing_country='MC'
                delivery_city=company.get('delivery_city')
                delivery_country=company.get('delivery_country')
                if company.get('delivery_country') in ['france','france ','France','France ','FRANCE','FRANCE ','FR','fr','',None]:
                    delivery_country='FR'
                if company.get('delivery_country') in ['LUXEMBOURG','LUXEMBOURG ','Luxembourg','Luxembourg ','LU']:
                    delivery_country='LU'
                if company.get('delivery_country') in ['BELGIQUE','BELGIQUE ','Belgique','Belgique ','belgique','belgique ','BE']:
                    delivery_country='BE'
                if company.get('delivery_country') in ['ITALIE','ITALIE ','Italie','Italie ','italie','italie ','IT ']:
                    delivery_country='IT'
                if company.get('delivery_country') in ['Allemagne','Allemagne ','ALLEMAGNE','ALLEMAGNE ','allemagne','allemagne ','DE ']:
                    delivery_country='DE'
                if company.get('delivery_country') in ['Espagne','Espagne ','ESPAGNE','ESPAGNE ','espagne','espagne ','ES ']:
                    delivery_country='ES'
                if company.get('delivery_country') in ['Monaco','Monaco ','MONACO','MONACO ','monaco','monaco ','MC ']:
                    delivery_country='MC'
                
                delivery_code_zip=company.get('delivery_code_zip')
                delivery_addres=company.get('delivery_addres')
                if (company.get('delivery_city') == None or company.get('delivery_city') == '') and (company.get('delivery_country')== None or company.get('delivery_country') == '') and (company.get('delivery_code_zip')==None or company.get('delivery_code_zip') == '') and (company.get('delivery_addres')==None or company.get('delivery_addres') == ''):
                    delivery_city=company.get('billing_city')
                    delivery_country=billing_country
                    delivery_code_zip=company.get('billing_code_zip')
                    delivery_addres=company.get('billing_addres')
                    
                customer_val = {
                    'country_id':country,
                    'old_api_id':company.get('id'),
    #                 'name':company.get('company_name'),
                    'street':company.get('billing_addres'),
                    'zip':company.get('billing_code_zip'),
                    'city':company.get('billing_city'),
                    'billing_country':billing_country,
                    'phone':str(company.get('phone1')).replace(chr(0),''),
                    'mobile':company.get('phone2'),
                    'customer_rank':1,
                    'delivery_city':delivery_city,
                    'delivery_country':delivery_country,
                    'delivery_code_zip':delivery_code_zip,
                    'delivery_addres':delivery_addres,
                    'custom_type':company.get('type'),
                }
                
                if company.get('company_name') != None:
                    customer_val['name'] = str(company.get('company_name')).replace(chr(0),'')
                else:
                    customer_val['name'] = '-'

                if company.get('modified') != None and company.get('modified') != '0000-00-00 00:00:00':
                    customer_val['custom_modified'] = datetime.strptime(company.get('modified'), '%Y-%m-%d %H:%M:%S')
            
                if company.get('billing_country') != None:
                    country_id = self.env['res.country'].search([('name','=',company.get('billing_country'))])
                    
                    if country_id:
                        customer_val['country_id']=country_id.id
                
                
                if company.get('user_id') != None:
                    user_id = ResUsers.search([('old_api_id','=',int(company.get('user_id')))], limit=1)
                    
                    if user_id:
                        customer_val['user_id']=user_id.id
                
                
                if company.get('siret') != None:
                    customer_val['siret']=company.get('siret')
                if company.get('activity') != None:
                    customer_val['activity']=company.get('activity')
                if company.get('email2') != None:
                    customer_val['email2']=company.get('email2')
                if str(company.get('email')) != None:
                    customer_val['email']=str(company.get('email'))
                if str(company.get('region_name')) != 'null':
                    customer_val['region_name']=str(company.get('region_name'))
                
                
                customer_id = self.search([('old_api_id','=',company.get('id')),('customer_rank','=',1)],limit=1)
                
                if not customer_id:
                    print('create')
                    customer_id = self.create(customer_val)
                else:
                    print('update')
                    customer_id = customer_id.update(customer_val)
                print(customer_id)
                print('-----count------',count)
            except:
                raise Exception(f'error in: {c}')
    
    
    
    
    
    
    
    
    
    
    

    old_api_id = fields.Char('Old ID')
    siret = fields.Char('Siret')
    activity = fields.Char('Activity')
    email2 = fields.Char('Email2')
    region_name = fields.Char('Region Name')
    delivery_city = fields.Char('Delivery City')
    delivery_country = fields.Char('Delivery Country')
    delivery_code_zip = fields.Char('Delivery Zip')
    delivery_addres = fields.Char('Delivery Address')
    custom_type = fields.Char('Type')
    custom_modified = fields.Datetime('Modified')
    billing_country = fields.Char('Billing Country')
    
    custom_category_id = fields.Many2one('res.partner.category.custom', string="Tags")

    


class ResUser(models.Model):
    _inherit = 'res.users'


    old_api_id = fields.Integer('Old ID')
    
    

class ResPartnerCategoryCustom(models.Model):    
    _name = 'res.partner.category.custom'
    
    
    name = fields.Char('Name',required=True)

