from odoo import fields, models


class HelpdeskTicketOperations(models.Model):

    _name = "helpdesk.ticket.packages"
    _description = "Helpdesk Ticket Packages"
    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket", string="Ticket ID", tracking=True, index=True
    )
    name = fields.Char(string="Package Ref")
    tracking_ref = fields.Char(string="Tracking Ref")
    tracking_url = fields.Char(string="Tracking URL")
    carrier = fields.Char(string="Carrier")
    