# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import requests
import json
import logging
from requests.auth import HTTPBasicAuth




class StockQuant(models.Model):
    _inherit = 'stock.quant'



    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        if self.location_id.usage=='internal':
            if self.product_id.sale_ok==True and self.product_id.type=='product':
                arrivage=[]
                onhand_qty= self.product_id.qty_available - self.product_id.qty_not_validated_yet
                moves = self.env['stock.move'].search(
                        [('product_id', '=', self.product_id.id), ('state', '=', 'assigned'), ('picking_type_id', '=', 1)])
                for m in moves:
                        if m.purchase_line_id:
                            arrivage.append(
                                ['1',m.purchase_line_id.price_unit, m.product_uom_qty,m.date.strftime('%Y-%m-%d')
                                , m.incertain])
                        elif m.sale_line_id:
                            arrivage.append(
                                ['1',m.sale_line_id.custom_supplier_price, m.product_uom_qty,m.date.strftime('%Y-%m-%d')
                                , m.incertain])
                        else:
                            arrivage.append(
                                ['1',0.0, m.product_uom_qty,m.date.strftime('%Y-%m-%d')
                                , m.incertain])
                post_data = {'price': self.product_id.standard_price, 'product_id': self.product_id.old_id,
                             'stock': onhand_qty,'arrivage': arrivage}
                url = 'http://141.94.171.159/crm/Companies/majStock?iscron=cron'
                requests.post(url, json=post_data, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint'))

        return res