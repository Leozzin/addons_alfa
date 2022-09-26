from datetime import datetime
from psutil import users
from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError
from odoo import _, SUPERUSER_ID
import requests
from requests.auth import HTTPBasicAuth
import json
from odoo.exceptions import UserError
from odoo import http
from odoo.http import request

class HelpdeskTicket(models.Model):
    _name = "helpdesk.ticket"
    _description = "Helpdesk Ticket"
    _rec_name = "number"
    _order = "priority desc, number desc, id desc"
    _mail_post_access = "read"
    _inherit = ["mail.thread.cc", "mail.activity.mixin", "portal.mixin"]

    def _get_default_stage_id(self):
        return self.env["helpdesk.ticket.stage"].search([], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env["helpdesk.ticket.stage"].search([])
        return stage_ids

    number = fields.Char(string="Ticket number", default="/", readonly=True)
    name = fields.Char(string="Title", readonly=True)
    description = fields.Html(sanitize_style=True)
    note = fields.Text('Description')
    order_date = fields.Datetime(string="Order Date")
    company_id = fields.Char(string="Company ID", required=True)
    user_id = fields.Many2one(
        comodel_name="res.users", string="Assigned user", tracking=True, index=True
    )
    user_ids = fields.Many2many(
        comodel_name="res.users", related="team_id.user_ids", string="Users"
    )
    users_ids = fields.Many2many(
        comodel_name="res.users", string="Users IR", tracking=True, index=True
    )
    url_crm = fields.Char('CRM URL', default='http://141.94.171.159/crm', readonly=True)
    stage_id = fields.Many2one(
        comodel_name="helpdesk.ticket.stage",
        string="Stage",
        group_expand="_read_group_stage_ids",
        default=_get_default_stage_id,
        tracking=True,
        ondelete="restrict",
        index=True,
        copy=False,
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")
    partner_name = fields.Char()
    partner_email = fields.Char(string="Email")

    last_stage_update = fields.Datetime(
        string="Last Stage Update", default=fields.Datetime.now
    )
    assigned_date = fields.Datetime(string="Assigned Date")
    closed_date = fields.Datetime(string="Closed Date")
    closed = fields.Boolean(related="stage_id.closed")
    unattended = fields.Boolean(related="stage_id.unattended", store=True)
    tag_ids = fields.Many2many(comodel_name="helpdesk.ticket.tag", string="Type")
    operations = fields.One2many('helpdesk.ticket.operations', "ticket_id", string="Operations")
    packages = fields.One2many('helpdesk.ticket.packages', "ticket_id", string="Packages")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    ref_amazon = fields.Char(string="Amazon Ref", readonly=True)
    ref_cdiscount = fields.Char(string="Cdiscount Ref", readonly=True)
    ref_ecom = fields.Char(string="Ecom Ref", readonly=True)
    invoice = fields.Char('Invoice', default='http://141.94.171.159/crm', readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    channel_id = fields.Many2one(
        comodel_name="helpdesk.ticket.channel",
        string="Channel",
        help="Channel indicates where the source of a ticket"
        "comes from (it could be a phone call, an email...)",
    )
    category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Category",
        required=True
    )
    team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Team:",
        required=True
    )
    priority = fields.Selection(
        selection=[
            ("0", "Low"),
            ("1", "Medium"),
            ("2", "High"),
            ("3", "Very High"),
        ],
        string="Priority",
        default="1",
    )
    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "helpdesk.ticket")],
        string="Media Attachments",
    )
    color = fields.Integer(string="Color Index")
    kanban_state = fields.Selection(
        selection=[
            ("normal", "Default"),
            ("done", "Ready for next stage"),
            ("blocked", "Blocked"),
        ],
        string="Kanban State",
    )
    active = fields.Boolean(default=True)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec.number + " - " + rec.name))
        return res

    def assign_to_me(self):
        self.write({"user_id": self.env.user.id})

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            return {'domain': {'picking_id': [('partner_id', '=', rec.partner_id.id)]}}

    @api.onchange("team_id", "user_id")
    def _onchange_dominion_user_id(self):
        if self.user_id and self.user_ids and self.user_id not in self.team_id.user_ids:
            self.update({"user_id": False})
            return {"domain": {"user_id": []}}
        if self.team_id:
            return {"domain": {"user_id": [("id", "in", self.user_ids.ids)]}}
        else:
            return {"domain": {"user_id": []}}

    # ---------------------------------------------------
    # CRUD
    # ---------------------------------------------------

    @api.model
    def create(self, vals):
        if vals.get('team_id') != 4:
            if vals.get('number') is None:
                users_ids = None
                if vals['users_ids'] is not None and len(vals['users_ids'][0][2]) > 0:
                    # users_ids = ";".join([str(c) for c in vals['users_ids'][0][2]])
                    users_ids = ""
                    for c in vals['users_ids'][0][2]:
                        user_partner = self.env['res.users'].sudo().search([('id', '=', c)], limit=1).partner_id.id
                        users_ids += str(user_partner) + ';'
                # if vals['users_ids']:
                #     users_ids = self.env['res.users'].search([('id', '=', vals['users_ids'])], limit=1).partner_id.id
                company_id = None
                company = self.env['res.partner'].sudo().search([('id', '=', vals['partner_id'])], limit=1)
                if company.old_api_id:
                    company_id = company.old_api_id
                picking_id = None
                picking = self.env['stock.picking'].sudo().search([('id', '=', vals['picking_id'])], limit=1)
                if picking:
                    picking_id = picking.origin
                order_id = "-"
                ref = "-"
                # user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
                user_id = None
                if vals['user_id']:
                    user_id = self.env['res.users'].search([('id', '=', vals['user_id'])], limit=1).partner_id.id
                # else:
                #     vals['user_id'] = user_id.id
                order_date = datetime.now().strftime("%Y-%m-%d")
                if vals['order_date']:
                    order_date = str(vals['order_date']).split()[0]
                else:
                    vals['order_date'] = datetime.now()
                # raise Exception(self.env['res.users'].search([('id', '=', self.env.uid)]).partner_id.id)
                data_to_crm = {
                    "order_id": order_id,
                    "ref": ref,
                    "type": vals['category_id'],
                    "order_date": order_date,
                    "company_id": company_id,
                    "user_id": user_id,
                    "sav_ir_user_id": users_ids,
                    "note": str(vals['note']).replace("'", " "),
                    "order_ref": picking_id,
                    "statutsav": int(vals['stage_id']) - 1,
                }
                # raise Exception(data_to_crm)
                returned_data = None
                # raise Exception(data_to_crm)
                try:
                    url = "http://141.94.171.159/crm/Companies/addSavFromOdoo"
                    response = requests.post(url, json=data_to_crm, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))
                    print(response)
                    print(response.content)
                    returned_data = json.loads(response.content)
                    if returned_data['order_id'] == "-" or returned_data['order_id'] is None:
                        raise UserError(_('Error in Order ID!'))
                except:
                #     # raise Exception()
                    raise Exception(data_to_crm)
                vals['name'] = returned_data['ref']
                vals['number'] = returned_data['order_id']

            picking = self.env['stock.picking'].sudo().search([('id', '=', vals['picking_id'])], limit=1)
            company = self.env['res.partner'].sudo().search([('id', '=', vals['partner_id'])], limit=1)
            order_id = vals['number']
            vals['url_crm'] = f'http://141.94.171.159/crm/propals/view/{order_id}'
            vals['invoice'] = f'http://141.94.171.159/crm/Propals/viewpdf/{order_id}'
            sale_order = self.env['sale.order'].sudo().search([('old_id', '=', picking.origin), ('partner_id', '=', company.id)], limit=1)
            if sale_order:
                if sale_order.provenance == "Cdiscount":
                    vals['ref_cdiscount'] = sale_order.provenance_ref
                elif sale_order.provenance == "Amazon":
                    vals['ref_amazon'] = sale_order.provenance_ref
                elif sale_order.provenance == "Ecom":
                    vals['ref_ecom'] = sale_order.provenance_ref
        # raise Exception(vals.get("number", "/"))
        if vals.get("number", "/") == "/":
            vals["number"] = self._prepare_ticket_number(vals)
        # raise Exception(vals.get("number"))
        if vals["team_id"] == 4:
            vals['name'] = "IT - " + vals['number']
        # raise Exception(vals.get("name"))
        if not vals.get("team_id") and vals.get("category_id"):
            vals["team_id"] = self._prepare_team_id(vals)
        if vals["picking_id"] is not None:
            list_operations = []
            picking = self.env['stock.picking'].sudo().search([('id', '=', vals['picking_id'])])
            for details in picking.move_ids_without_package:
                move_line = self.env['stock.move.line'].sudo().search([('move_id', '=', details.id)], limit=1)
                order_line = self.env['sale.order.line'].sudo().search([('order_id', '=', picking.sale_id.id), ('product_id', '=', details.product_id.id)], limit=1)
                # supplier_id = self.env['res.partner'].sudo().search([('old_api_id', '=', order_line.custom_supplier_id)], limit=1)
                data = {
                    # "name": details['name'],
                    "qty": details.product_qty,
                    "product_id": details.product_id.id,
                    "ref_provider": order_line.provider_ref,
                    "supplier_id": order_line.custom_supplier_id.id,
                    "uom_id": details.product_uom.id,
                    "lot_id": move_line.lot_id.name
                }
                list_operations.append((0, 0, data))
            list_packages = []
            for details in picking.package_ids:
                data = {
                    "name": details.name,
                    "tracking_ref": details.carrier_tracking_ref,
                    "tracking_url": details.carrier_tracking_url,
                    "carrier": picking.carrier_id.name,
                }
                list_packages.append((0, 0, data))
            vals['operations'] = list_operations
            vals['packages'] = list_packages
        return super().create(vals)

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "number" not in default:
            default["number"] = self._prepare_ticket_number(default)
        res = super().copy(default)
        return res

    def unlink(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.ids)
        for ticket in tickets:
            if ticket.team_id.id != 4:
                try:
                    sav_data = {
                        "order_id": ticket.number
                    }
                    url = "http://141.94.171.159/crm/Companies/deleteSav"
                    response = requests.post(url, json=sav_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))
                    returned_data = json.loads(response.content)
                except:
                    raise UserError(_('Error while deleting data from crm!'))
        return super().unlink()

    def write(self, vals, isCron=False):
        if self.team_id.id != 4:
            if not isCron:
                # if vals.keys() != ['priority']
                users_ids = None
                if self.users_ids is not None and len(self.users_ids.ids) > 0:
                    # users_ids = ";".join([str(c) for c in self.users_ids.ids])
                    users_ids = ""
                    for user_partner in self.users_ids:
                        users_ids += str(user_partner.partner_id.id) + ';'
                # if self.users_ids is not None:
                #     users_ids = self.users_ids.partner_id.id
                data_to_crm = {
                    "order_id": self.number,
                    "ref": self.name,
                    "type": self.category_id.id,
                    "order_date": str(self.order_date).split()[0],
                    "company_id": self.partner_id.old_api_id,
                    "user_id": self.user_id.partner_id.id,
                    "sav_ir_user_id": users_ids,
                    "note": str(self.note).replace("'", " "),
                    "order_ref": self.picking_id.origin,
                    "statutsav": int(self.stage_id.id) - 1
                }
                if data_to_crm['order_ref'] == False:
                    data_to_crm['order_ref'] = None
                print(data_to_crm)
                if vals.get("category_id"):
                    data_to_crm["type"] = vals["category_id"]
                if vals.get("order_date"):
                    data_to_crm["order_date"] = str(vals["order_date"]).split()[0]
                if vals.get("partner_id"):
                    data_to_crm["company_id"] = vals["partner_id"]
                # user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
                user_id = None
                if vals.get("user_id"):
                    user_id = self.env['res.users'].search([('id', '=', vals['user_id'])], limit=1)
                    data_to_crm["user_id"] = user_id.partner_id.id
                # else:
                #     vals['user_id'] = user_id.id
                #     data_to_crm["user_id"] = user_id.partner_id.id
                
                if vals.get("users_ids"):
                    if vals["users_ids"] is not None and len(vals["users_ids"]) > 0:
                        data_to_crm["sav_ir_user_id"]= ""
                        for c in vals['users_ids'][0][2]:
                            user_partner = self.env['res.users'].sudo().search([('id', '=', c)], limit=1).partner_id.id
                            data_to_crm["sav_ir_user_id"] += str(user_partner) + ';'
                    else:
                        data_to_crm["sav_ir_user_id"] = None
                # if vals.get("users_ids"):
                #     data_to_crm["sav_ir_user_id"] = None
                #     if vals["users_ids"] is not None:
                #         data_to_crm["sav_ir_user_id"] = self.users_ids.partner_id.id
                
                if vals.get("description"):
                    data_to_crm["note"] = vals["note"]
                if vals.get("picking_id"):
                    picking_id = self.env['stock.picking'].sudo().search([('id', '=',vals["picking_id"])], limit=1)
                    data_to_crm["order_ref"] = picking_id.origin
                    if vals["picking_id"] is not None:
                        list_operations = []
                        picking = self.env['stock.picking'].sudo().search([('id', '=', vals['picking_id'])])
                        for details in picking.move_ids_without_package:
                            move_line = self.env['stock.move.line'].sudo().search([('move_id', '=', details.id)], limit=1)
                            order_line = self.env['sale.order.line'].sudo().search([('order_id', '=', picking.sale_id.id), ('product_id', '=', details.product_id.id)], limit=1)
                            # supplier_id = self.env['res.partner'].sudo().search([('old_api_id', '=', order_line.custom_supplier_id)], limit=1)
                            data = {
                                # "name": details['name'],
                                "qty": details.product_qty,
                                "product_id": details.product_id.id,
                                "ref_provider": order_line.provider_ref,
                                "supplier_id": order_line.custom_supplier_id.id,
                                "uom_id": details.product_uom.id,
                                "lot_id": move_line.lot_id.name
                            }
                            list_operations.append((0, 0, data))
                        vals['operations'] = list_operations
                if vals.get("stage_id"):
                    data_to_crm["statutsav"] = int(vals["stage_id"]) - 1
                print("new", data_to_crm)
                # raise Exception(data_to_crm)
                if data_to_crm["order_date"] == False or data_to_crm["order_date"] == 'False':
                    data_to_crm["order_date"] = datetime.now().strftime("%Y-%m-%d")
                if data_to_crm["user_id"] == False:
                    data_to_crm["user_id"] = None
                # raise Exception(data_to_crm)
                try:
                    url = "http://141.94.171.159/crm/Companies/addSavFromOdoo"
                    response = requests.post(url, json=data_to_crm, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))
                    print(response)
                    # raise UserError(response.content)
                    returned_data = json.loads(response.content)
                    if returned_data['order_id'] == "-":
                        raise UserError(_('Error in Order ID!'))
                except:
                    raise Exception(data_to_crm)
        for _ticket in self:
            now = fields.Datetime.now()
            if vals.get("stage_id"):
                stage = self.env["helpdesk.ticket.stage"].browse([vals["stage_id"]])
                vals["last_stage_update"] = now
                if stage.closed:
                    vals["closed_date"] = now
            if vals.get("user_id"):
                vals["assigned_date"] = now
        return super().write(vals)

    def action_duplicate_tickets(self):
        for ticket in self.browse(self.env.context["active_ids"]):
            ticket.copy()

    def _prepare_ticket_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("helpdesk.ticket.sequence") or "/"

    def _compute_access_url(self):
        super()._compute_access_url()
        for item in self:
            item.access_url = "/my/ticket/%s" % (item.id)

    def _prepare_team_id(self, values):
        category = self.env["helpdesk.ticket.category"].browse(values["category_id"])
        if category.default_team_id:
            return category.default_team_id.id

    # ---------------------------------------------------
    # Mail gateway
    # ---------------------------------------------------

    def _track_template(self, tracking):
        res = super()._track_template(tracking)
        ticket = self[0]
        if "stage_id" in tracking and ticket.stage_id.mail_template_id:
            res["stage_id"] = (
                ticket.stage_id.mail_template_id,
                {
                    "auto_delete_message": True,
                    "subtype_id": self.env["ir.model.data"].xmlid_to_res_id(
                        "mail.mt_note"
                    ),
                    "email_layout_xmlid": "mail.mail_notification_light",
                },
            )
        return res

    @api.model
    def message_new(self, msg, custom_values=None):
        """Override message_new from mail gateway so we can set correct
        default values.
        """
        if custom_values is None:
            custom_values = {}
        defaults = {
            "name": msg.get("subject") or _("No Subject"),
            "description": msg.get("body"),
            "partner_email": msg.get("from"),
            "partner_id": msg.get("author_id"),
        }
        defaults.update(custom_values)

        # Write default values coming from msg
        ticket = super().message_new(msg, custom_values=defaults)

        # Use mail gateway tools to search for partners to subscribe
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=ticket, force_create=False
            )
            if p
        ]
        ticket.message_subscribe(partner_ids)

        return ticket

    def message_update(self, msg, update_vals=None):
        """Override message_update to subscribe partners"""
        email_list = tools.email_split(
            (msg.get("to") or "") + "," + (msg.get("cc") or "")
        )
        partner_ids = [
            p.id
            for p in self.env["mail.thread"]._mail_find_partner_from_emails(
                email_list, records=self, force_create=False
            )
            if p
        ]
        self.message_subscribe(partner_ids)
        return super().message_update(msg, update_vals=update_vals)

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        try:
            for ticket in self:
                if ticket.partner_id:
                    ticket._message_add_suggested_recipient(
                        recipients, partner=ticket.partner_id, reason=_("Customer")
                    )
                elif ticket.partner_email:
                    ticket._message_add_suggested_recipient(
                        recipients,
                        email=ticket.partner_email,
                        reason=_("Customer Email"),
                    )
        except AccessError:
            # no read access rights -> just ignore suggested recipients because this
            # imply modifying followers
            pass
        return recipients

    def to_attente_traitement(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 1})

    def to_traite(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 2})

    def to_a_cloturer(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 3})
    
    def to_resolu(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 4})
    
    def to_cours_traitement(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 5})

    def to_avoir_a_valider(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 6})
    
    def to_non_resolu(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 7})
    
    def to_avoir_fournisseur(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 8})
    
    def to_attente_retour_marchandise(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 9})

    def to_en_attente_paiement(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"stage_id": 10})
    
    def disassign_user(self):
        env = self.env(user=SUPERUSER_ID, su=True)
        tickets = env['helpdesk.ticket'].sudo().browse(self.env.context.get('active_ids'))
        for ticket in tickets:
            ticket.sudo().write({"user_id": None})

    def create_receipt(self, context=None):
        env = self.env(user=SUPERUSER_ID, su=True)
        if len(self.env.context.get('active_ids')) > 1:
            raise UserError('Create receipt action can only work with 1 ticket selected!')
        ticket = self
        receipt_data = {
            "is_locked": True,
            "immediate_transfer": False,
            "status_code": False,
            "priority": "0",
            "is_update": False,
            "owner_id": False,
            "package_level_ids_details": [],
            "last_pack": False,
            "move_ids_without_package": [],
            "package_level_ids": [],
            "carrier_id": False,
            "carrier_tracking_ref": False,
            "move_type": "direct",
            "user_id": 2,
            "company_id": 1,
            "note": False,
            "pdf_label": False,
            "message_follower_ids": [],
            "activity_ids": [],
            "message_ids": [],
            "partner_id": ticket.partner_id.id,
            "picking_type_id": 1,
            "location_id": 5,
            "location_dest_id": 8,
            "origin": str(ticket.number),
            "ticket_id": ticket.id,
            "name": f"WH/IN/{ticket.number}",
            "scheduled_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sale_reference": ticket.name
        }

        for line in ticket.picking_id.move_ids_without_package:
            receipt_data['move_ids_without_package'].append([0,0,{
                "company_id": 1,
                "state": "draft",
                "picking_type_id": 1,
                "location_id": 5,
                "location_dest_id": 8,
                "additional": False,
                "sale_line_id": False,
                "custom_supplier_id": False,
                "detail_order_id": 0,
                "description_picking": line.description_picking,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "lot_ids": [
                    [
                        6,
                        False,
                        []
                    ]
                ],
                "incertain": "1",
                "product_id": line.product_id.id,
                "product_uom": line.product_uom.id,
                "quantity_done": 0.0,
                "forecast_availability": 0.0,
                "product_uom_qty": line.product_uom_qty,
                "name": line.name,
                "location_id": 5,
                "location_dest_id": 8
            }])
        receipt_data['first_product_id'] = None
        if len(receipt_data['move_ids_without_package']) > 0:
            receipt_data['first_product_id'] = receipt_data['move_ids_without_package'][0][2]["product_id"]
        # raise Exception(receipt_data)
        records = env['stock.picking'].sudo().create(receipt_data)
        for rec in records:
            rec.write({"sale_reference": rec.ticket_id.name})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Receipt',
            'res_model': 'stock.picking',
            'res_id': records.id,
            'view_type': 'form',
            'view_mode': 'form',
        }
        

    def create_delivery_order(self, context=None):
        env = self.env(user=SUPERUSER_ID, su=True)
        if len(self.env.context.get('active_ids')) > 1:
            raise UserError('Create receipt action can only work with 1 ticket selected!')
        ticket = self
        delivery_data = {
            "is_locked": True,
            "immediate_transfer": False,
            "status_code": False,
            "priority": "0",
            "is_update": False,
            "owner_id": False,
            "package_level_ids_details": [],
            "last_pack": False,
            "move_ids_without_package": [],
            "package_level_ids": [],
            "carrier_id": False,
            "carrier_tracking_ref": False,
            "move_type": "direct",
            "user_id": 2,
            "company_id": 1,
            "note": False,
            "pdf_label": False,
            "message_follower_ids": [],
            "activity_ids": [],
            "message_ids": [],
            "partner_id": ticket.partner_id.id,
            "picking_type_id": 2,
            "location_id": 8,
            "location_dest_id": 5,
            "origin": str(ticket.number),
            "ticket_id": ticket.id,
            "name": f"WH/IN/{ticket.number}",
            "scheduled_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sale_reference": ticket.name
        }

        for line in ticket.picking_id.move_ids_without_package:
            delivery_data['move_ids_without_package'].append([0,0,{
                "company_id": 1,
                "state": "draft",
                "picking_type_id": 1,
                "location_id": 8,
                "location_dest_id": 5,
                "additional": False,
                "sale_line_id": False,
                "custom_supplier_id": False,
                "detail_order_id": 0,
                "description_picking": line.description_picking,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "lot_ids": [
                    [
                        6,
                        False,
                        []
                    ]
                ],
                "incertain": "1",
                "product_id": line.product_id.id,
                "product_uom": line.product_uom.id,
                "quantity_done": 0.0,
                "forecast_availability": 0.0,
                "product_uom_qty": line.product_uom_qty,
                "name": line.name,
                "location_id": 8,
                "location_dest_id": 5
            }])
        delivery_data['first_product_id'] = None
        if len(delivery_data['move_ids_without_package']) > 0:
            delivery_data['first_product_id'] = delivery_data['move_ids_without_package'][0][2]["product_id"]
        records = env['stock.picking'].sudo().create(delivery_data)
        for rec in records:
            rec.write({"sale_reference": rec.ticket_id.name})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Receipt',
            'res_model': 'stock.picking',
            'res_id': records.id,
            'view_type': 'form',
            'view_mode': 'form',
        }

    def test(self):
        self.env.user.notify_danger(message="Don't click test action! -_-", title="Stop")
        pickings = self.env['stock.picking'].sudo().search([('ticket_id', '!=', False)])
        for picking in pickings:
            picking.write({"sale_reference": picking.ticket_id.name})