from odoo import fields, models


class HelpdeskTicketOperations(models.Model):

    _name = "helpdesk.ticket.operations"
    _description = "Helpdesk Ticket Operations"
    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket", string="Ticket ID", tracking=True, index=True
    )

    product_id = fields.Many2one(
        comodel_name="product.product", string="Product ID", tracking=True, index=True
    )
    qty = fields.Float(string="Quantity")
    uom_id = fields.Many2one(
        comodel_name="uom.uom", string="Unit of Mesure", tracking=True, index=True
    )
    # lot_id = fields.Many2one(
    #     comodel_name="stock.production.lot", string="Lot/Serial Number", tracking=True, index=True
    # )

    lot_id = fields.Char(string="Lot/Serial Number")
    supplier_id = fields.Many2one(comodel_name="res.partner", string="Supplier")
    ref_provider = fields.Char(string="Provider Ref")
