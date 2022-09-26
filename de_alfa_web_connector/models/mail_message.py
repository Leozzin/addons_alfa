# -*- coding: utf-8 -*-
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
import datetime
import requests
from requests.auth import HTTPBasicAuth



class Message(models.Model):
    _inherit = 'mail.message'

    old_api_id = fields.Char(string="Old API ID")

    def create_notif_email(self, values):
        # check_mail = self.env['mail.message'].sudo().search([('body', '=', values['body'])], limit=1)
        # if not check_mail:
        res = self.env['helpdesk.ticket'].sudo().search([('id', '=', values['res_id'])], limit=1)
        # record = self.env['helpdesk.ticket'].browse(res.id)
        partner = self.env['res.partner'].sudo().browse(res.user_id.partner_id.id)
        post_vars = {
            'subject': f"You have been received an email from {res.partner_id.name} in the Helpdesk Ticket {res.number} - {res.name}",
            'body': f"<p style=\"margin:0px\">\
                <span>Dear {res.user_id.partner_id.name},</span>\
                <br>\
                <span style=\"margin-top:8px\">\
                    You have been received an email from {res.partner_id.name} in the Helpdesk Ticket {res.number} - {res.name}.\
                </span>\
            </p>\
            <p style=\"margin-top:24px; margin-bottom:16px\">\
                <a \
                    style=\"background-color:#875A7B; padding:10px; text-decoration:none; color:#fff; border-radius:5px\" \
                    href=\"http://141.94.171.159:90/mail/view?model=helpdesk.ticket&amp;res_id={res.id}\" \
                    data-oe-model=\"helpdesk.ticket\" \
                    data-oe-id=\"{res.id}\"\
                >\
                    View Helpdesk Ticket\
                </a>\
            </p>",
            'author_id': 2,
            'partner_ids': [res.user_id.partner_id.id],
            'notification_ids': [(0,0,{'res_partner_id': res.user_id.partner_id.id, 'notification_type':'inbox'})]}
        # post_vars['body'] = json.dumps(values)
        partner.message_post(type="notification", subtype_xmlid="mail.mt_comment", **post_vars)
    
    def create_notif_comment(self, values, user_comment):
        res = self.env['helpdesk.ticket'].sudo().search([('id', '=', values['res_id'])], limit=1)
        partner = self.env['res.partner'].sudo().browse(res.user_id.partner_id.id)
        user = self.env['res.partner'].sudo().browse(user_comment)
        post_vars = {
            'subject': f"You have been received an email from {res.partner_id.name} in the Helpdesk Ticket {res.number} - {res.name}",
            'body': f"<p style=\"margin:0px\">\
                <span>Dear {res.user_id.partner_id.name},</span>\
                <br>\
                <span style=\"margin-top:8px\">\
                    You have been received a comment from {user.name} in the Helpdesk Ticket {res.number} - {res.name}.\
                </span>\
            </p>\
            <p style=\"margin-top:24px; margin-bottom:16px\">\
                <a \
                    style=\"background-color:#875A7B; padding:10px; text-decoration:none; color:#fff; border-radius:5px\" \
                    href=\"http://141.94.171.159:90/mail/view?model=helpdesk.ticket&amp;res_id={res.id}\" \
                    data-oe-model=\"helpdesk.ticket\" \
                    data-oe-id=\"{res.id}\"\
                >\
                    View Helpdesk Ticket\
                </a>\
            </p>",
            'author_id': 2,
            'partner_ids': [res.user_id.partner_id.id],
            'notification_ids': [(0,0,{'res_partner_id': res.user_id.partner_id.id, 'notification_type':'inbox'})]}
        partner.message_post(type="notification", subtype_xmlid="mail.mt_comment", **post_vars)
    
    @api.model
    def create(self, values_list):
        value = values_list
        # raise Exception(values_list)
        # for value in values_list:
        #     raise Exception(value)
        # raise Exception(values_list)
        if value['message_type'] == 'email'\
            and value['model'] == 'helpdesk.ticket'\
            and "Service Après Vente" not in value['subject']\
            and "Résolution de votre demande" not in value['subject']:
            # raise Exception(values_list)
            self.create_notif_email(values_list)
            list_attach_to_delete = []
            for attach in value['attachment_ids']:
                attach_obj = self.env['ir.attachment'].sudo().search([('id', '=', attach[1])], limit=1)
                if attach_obj.name == 'original_email.eml':
                    list_attach_to_delete.append(attach_obj.id)
                    value['attachment_ids'][value['attachment_ids'].index(attach)] = None
            if len(list_attach_to_delete) > 0:
                attachs_obj = self.env['ir.attachment'].sudo().browse(list_attach_to_delete)
                attachs_obj.sudo().unlink()
            values_list['attachment_ids'] = [v for v in value['attachment_ids'] if v is not None]
        # try: 
        if 'fromCrm' not in values_list.keys():
            if value['message_type'] != 'email':
                if value['model'] == 'helpdesk.ticket' \
                    and int(value['subtype_id']) == 2 \
                    and 'Helpdesk Ticket' not in value['body']\
                    and '<p style="margin:0px">' not in value['body'] \
                    and '">Vous avez été assigné à' not in value['body']\
                    and value['message_type'] == "comment"\
                    and len(value['body'])>0:
                    ticket = self.env['helpdesk.ticket'].sudo().search([('id', '=', value['res_id'])], limit=1)
                    data = {
                        "order_id": str(ticket.number),
                        "user_id": str(value['author_id']),
                        "comment": value['body']
                    }
                    datatojson = json.dumps(data)
                    datatocrm = json.loads(datatojson)
                    # raise Exception(data)
                    
                    # try:
                    url = "http://141.94.171.159/crm/Companies/addCommentFromOdoo"
                    response = requests.post(url, json=datatocrm, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))
                    # raise Exception(response.content)
                    # raise UserError(response.content)
                    # raise Exception(response)
                    returned_data = json.loads(response.content)
                    # except:
                    #     raise UserError(_('Error creating comment in crm!'))
        # except:
        #     r
        try:
            del values_list['fromCrm']
        except KeyError:
            pass
        if value['message_type'] != 'email':
            if value['model'] == 'helpdesk.ticket' \
                and int(value['subtype_id']) == 2 \
                and 'Helpdesk Ticket' not in value['body']\
                and '<p style="margin:0px">' not in value['body'] \
                and '">Vous avez été assigné à' not in value['body']\
                and value['message_type'] == "comment"\
                and len(value['body'])>0:
                ticket = self.env['helpdesk.ticket'].sudo().search([('id', '=', value['res_id'])], limit=1)
                # raise Exception(ticket.user_id.id)
                if ticket.user_id.id != False:
                    if value['author_id'] != ticket.user_id.partner_id.id:
                        # raise Exception('second if')
                        self.create_notif_comment(values_list, value['author_id'])
            # raise Exception(values_list)
        return super(Message, self).create(values_list)