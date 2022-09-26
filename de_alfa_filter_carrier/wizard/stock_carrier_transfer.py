from odoo import fields, models,api
import ast



class StockCarrierTransfer(models.TransientModel):
    _inherit = "stock.carrier.transfer"

    @api.onchange('pick_ids')
    def onchange_pick_ids(self):
        list_carrier=[]
        message_info=[]
        for i in self.env['delivery.carrier'].search([]):
            domain=[]
            if i.domain:
                if not isinstance(i.domain, (list, tuple)):
                    domain = ast.literal_eval(i.domain)

            picking=self.env['stock.picking'].search(domain).ids
            if all (p in picking  for p in self.env.context.get('active_ids')):
                list_carrier.append(i.id)
            else:
                liste = []
                for p in self.env.context.get('active_ids'):

                    if not p in picking:
                        liste.append(self.env['stock.picking'].browse(p).name)

                message=str(liste) + ' dont  verifiy this condition for provider<b> ' + i.name +"</b> : " + i.domain
                message_info.append(message)
        self.message='<br>'.join(message_info)
        res = {'domain': {'carrier_id': [('id', 'in', list_carrier)]}}
        return res
    message=fields.Html("Message info")




