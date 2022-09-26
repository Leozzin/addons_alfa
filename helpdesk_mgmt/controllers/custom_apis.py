import odoo.http as http
from odoo.http import request
from odoo import _, SUPERUSER_ID


class HelpdeskTicketCustomController(http.Controller):

    @http.route('/helpdesk/ticket/create', type='json', auth='public', methods=["POST"])
    def create_from_crm(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        company_id = None
        if data['company_id'] is not None:
            company_id = env['res.partner'].sudo().search([('old_api_id', '=', data['company_id'])], limit=1).id
        sav_ir_user_id = None
        if data['sav_ir_user_id'] is not None and len(data["sav_ir_user_id"]) > 0:
            list_user = [int(uir_id) for uir_id in data['sav_ir_user_id'].split(';') if len(uir_id) > 0]
            sav_ir_user_id = []
            for usr in list_user:
                uid = env['res.users'].sudo().search([('partner_id', '=', usr)])
                if uid:
                    sav_ir_user_id.append(uid.id)
        # if data['sav_ir_user_id'] is not None:
        #     sav_ir_user_id = env['res.users'].sudo().search([('partner_id', '=', data['sav_ir_user_id'])]).id
        note = ""
        if data['note'] is not None:
            note = data['note']
        picking_id = None
        if data['order_ref'] is not None:
            picking_id = env['stock.picking'].sudo().search([('origin', '=', data['order_ref'])], limit=1).id
        user_id = None
        if data['user_id'] is not None and int(data['user_id']) != 0:
            # user_id = int(data['user_id'])
            user_id = env['res.users'].search([('partner_id', '=', int(data['user_id']))], limit=1).id
        stage_id = int(data["statutsav"]) + 1
        stage = env['helpdesk.ticket.stage'].sudo().search([('id', '=', stage_id)])
        if not stage:
            stage_id = None
        order_id = data['order_id']
        team_id = env['helpdesk.ticket.category'].sudo().search([('id', '=', stage_id)])
        env['helpdesk.ticket'].sudo().create({
            'number': data['order_id'],
            'name': data['ref'],
            'team_id': team_id.default_team_id.id,
            'category_id': int(data['type']),
            'order_date': data['order_date'],
            'partner_id': company_id,
            # 'user_id': user_id,
            'user_id': None,
            'users_ids': sav_ir_user_id,
            'note': note,
            'picking_id': picking_id,
            'stage_id': stage_id,
            "url_crm": f'http://141.94.171.159/crm/propals/view/{order_id}',
            "invoice": f'http://141.94.171.159/crm/Propals/viewpdf/{order_id}'
        })
        return {
            'status': 200,
            "message": "SAV Created!"
        }
    
    @http.route('/helpdesk/ticket/update', type='json', auth='public', methods=["POST"])
    def update_from_crm(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        data_to_save = {}
        if 'company_id' in data.keys():
            company_id = env['res.partner'].sudo().search([('old_api_id', '=', data['company_id'])], limit=1).id
            data_to_save['partner_id'] = company_id
        if 'sav_ir_user_id' in data.keys():
            list_user = [int(uir_id) for uir_id in data['sav_ir_user_id'].split(';') if len(uir_id) > 0]
            data_to_save['users_ids'] = []
            for usr in list_user:
                uid = env['res.users'].sudo().search([('partner_id', '=', usr)])
                if uid:
                    data_to_save['users_ids'].append(uid.id)
            # sav_ir_user_id = env['res.users'].sudo().search([('partner_id', '=', data['sav_ir_user_id'])]).id
            # data_to_save['users_ids'] = sav_ir_user_id
        note = ""
        if 'note' in data.keys():
            note = data['note']
            data_to_save['note'] = note
        picking_id = None
        if 'order_ref' in data.keys():
            picking_id = env['stock.picking'].sudo().search([('origin', '=', data['order_ref'])], limit=1).id
            data_to_save['picking_id'] = picking_id
        user_id = None
        if 'user_id' in data.keys():
            user_id = env['res.users'].sudo().search([('partner_id', '=', data['user_id'])], limit=1).id
            data_to_save['user_id'] = user_id
        if 'statutsav' in data.keys():
            data_to_save['stage_id'] = int(data["statutsav"]) + 1
            stage = env['helpdesk.ticket.stage'].sudo().search([('id', '=', data_to_save['stage_id'])])
            if not stage:
                data_to_save['stage_id'] = None
        if 'type' in data.keys():
            data_to_save['category_id'] = int(data['type'])
        helpdesk_ticket = env['helpdesk.ticket'].sudo().search([('number', '=', data['order_id'])], limit=1)
        if helpdesk_ticket:
            helpdesk_ticket.sudo().write(
                data_to_save,
                isCron=True
            )
        else:
            helpdesk_ticket = env['helpdesk.ticket'].sudo().create(data_to_save)
        return {
            'status': 200,
            "message": "SAV Updated!"
        }
    
    @http.route('/helpdesk/ticket/delete', type='json', auth='public', methods=["POST"])
    def delete_from_crm(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        if data['order_id'] is not None:
            helpdesk_ticket = env['helpdesk.ticket'].sudo().search([('number', '=', data['order_id'])], limit=1)
            helpdesk_ticket.sudo().unlink()
        
            return {
                'status': 200,
                "message": "SAV Deleted!"
            }
        else:
            return {
                'status': 400,
                "message": "Bad Request!"
            }
    
    @http.route('/helpdesk/ticket/comment/add', type='json', auth='public', methods=["POST"])
    def add_ticket_comment_crm(self):
        env = request.env(user=SUPERUSER_ID, su=True)
        data = request.jsonrequest['params']
        order_id = data['order_id']
        body = data['comment']
        # comment_id = data['id']
        created_date = data['created']
        ticket = env['helpdesk.ticket'].sudo().search([('number', '=', order_id)], limit=1)
        if ticket:
            # comment_exist = env['mail.message'].sudo().search([('old_api_id', '=', comment_id)], limit=1)
            # if not comment_exist:
            user_id = env['res.users'].sudo().search([('partner_id', '=', int(data['user_id']))], limit=1)
            ticket_comment = env['mail.message'].sudo().create(
                {
                    "subject": f"Re: {order_id} - {ticket.name}",
                    "body": f"<p>{body}</p>",
                    "parent_id": 0,
                    "model": "helpdesk.ticket",
                    "res_id": ticket.id,
                    "record_name": f"Re: {order_id} - {ticket.name}",
                    "message_type": "comment",
                    "subtype_id": 2,
                    "email_from": f"<{user_id.login}>",
                    "author_id": user_id.partner_id.id,
                    "create_uid": user_id.id,
                    "write_uid": user_id.id,
                    # "old_api_id": comment_id,
                    "date": created_date,
                    "fromCrm": True,
                }
            )
        else:
            return {
                    'status': 404,
                    "message": "Ticket Not Found!"
                }
        return {
            'status': 200,
            "message": "Comment Added!"
        }
