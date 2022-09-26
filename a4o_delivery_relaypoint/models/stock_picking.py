# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    mandatory_weight = fields.Boolean(string='Mandatory Shipping Weight',
        compute='_compute_mandatory_weight')

    @api.depends('packaging_id')
    def _compute_mandatory_weight(self):
        result = False
        if self.packaging_id:
            method_name = ('%s_compute_mandatory_weight'
                % self.packaging_id.package_carrier_type)
            if hasattr(self, method_name):
                result = getattr(self, method_name)()
        self.mandatory_weight = result


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_delivery_relaypoint(self):
        if hasattr(self,
                '%s_get_delivery_relaypoint' % self.carrier_id.delivery_type):
            return getattr(self,
                '%s_get_delivery_relaypoint' % self.carrier_id.delivery_type)()
        return False

    @api.depends('carrier_id')
    def compute_delivery_relaypoint(self):
        for picking in self:
            picking.relaypoint_delivery = picking._get_delivery_relaypoint()

    relaypoint_delivery = fields.Boolean('Delivery to a relay point ?',
        compute='compute_delivery_relaypoint')
    original_partner_id = fields.Many2one('res.partner', 'Original Partner',
        readonly=True)

    def button_validate(self):
        self.ensure_one()
        if (self.relaypoint_delivery and not self.partner_id.code_relaypoint):
            raise UserError(_("You cannot choose a relay point delivery "
                "without choosing a relay point! Go to the 'additional info' "
                "page to select the relay point!"))
        return super().button_validate()

    def action_get_relaypoint(self):
        context = dict(self.env.context or {})
        # Get addresses
        addr = self.partner_id.parent_id or self.partner_id
        address_ids = [addr.id] + [x.id for x in addr.child_ids]
        context.update({
            'picking_id': self.id,
            'address_ids': address_ids,
            'default_address': self.partner_id.id,
            })
        return {
            'name': _('Select the address'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delivery.carrier.relaypoint',
            'view_id': self.env.ref(
                'a4o_delivery_relaypoint.select_relaypoint_view_form').id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }

    @api.depends('sale_id')
    def get_delivery_price(self):
        if not self.sale_id:
            return 0.0
        return sum([
                l.price_total
                for l in self.sale_id.order_line
                if l.is_delivery
                ])