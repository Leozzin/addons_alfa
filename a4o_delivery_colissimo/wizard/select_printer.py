# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
     
    
class SelectPrinter(models.TransientModel):
    _name = 'select.printer'
    _description = 'Printer Selection Wizard'


    printer_id = fields.Many2one(
        comodel_name='printing.printer',
        default=lambda self: self._context.get('default_printer_id'),
        string='Printer',
        help="printer")
    
    def set_printer(self):
        carrier_id = self.env.context.get('carrier_id')
        if carrier_id:
            carrier = self.env['delivery.carrier'].browse(carrier_id)
            carrier.write({
                'coli_printer_id': self.printer_id.id,
                'coli_printer_name': "printing.printer,%s" % (
                    str(self.printer_id.id))})
            