# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, fields, models


class ChooseDeliveryPackage(models.TransientModel):
    _description = 'Delivery Package Selection Wizard'
    _inherit = 'choose.delivery.package'

    mandatory_weight = fields.Boolean('Mandatory weight',
        compute='_compute_mandatory_weight')
    
    @api.depends('delivery_packaging_id')
    def _compute_mandatory_weight(self):
        result = False
        if self.delivery_packaging_id:
            method_name = ('%s_compute_mandatory_weight'
                % self.delivery_packaging_id.package_carrier_type)
            if hasattr(self, method_name):
                result = getattr(self, method_name)()
        self.mandatory_weight = result
