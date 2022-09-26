# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_hs_code(self):
        hscode = None
        if hasattr(self, 'hs_code_id'):
            # If use of OCA module
            hscode = self.get_hs_code_recursively()
            hscode = hscode and hscode.hs_code or None
        else:
            # If use of community only or entreprise module
            hscode = self.hs_code
        return hscode

    def get_origin_country(self):
        if hasattr(self, 'intrastat_origin_country_id'):
            country = self.intrastat_origin_country_id.code
        elif hasattr(self, 'origin_country_id'):
            country = self.origin_country_id.code or False
        else:
            country = None
        return country
