from odoo import fields, models
import base64
import os
import io
from PyPDF2 import PdfFileReader, PdfFileMerger
import requests
from datetime import datetime
import csv
from csv import reader
from odoo import _
from odoo.exceptions import UserError
from ftplib import FTP




class StockPicking(models.Model):
    _inherit = "stock.picking"
    def get_tracking_ftp(self):
        carrier_id=self.env['delivery.carrier'].search([('delivery_type','=','gls_alfa')],limit=1)
        if carrier_id:
            dest=r'/opt\addons_alfa\de_alfa_ftp_gls\static\description\files\tracking'
            ftp=FTP(carrier_id.gls_alfa_host, carrier_id.gls_alfa_user, carrier_id.gls_alfa_password)
            ftp.cwd('/tracking')
            #liste = ftp.nlst('tracking/*.csv')
            liste = ftp.nlst('*.csv')
            for l in liste:
                os.chdir(dest)
                file_des=l
                with open(file_des,'wb') as file:
                    ftp.retrbinary('RETR %s' %l,file.write)
                with open(file_des, 'r') as read_obj:
                    csv_reader = reader(read_obj,delimiter=';')
                    # Iterate over each row in the csv using reader object
                    for row in csv_reader:
                        # row variable is a list that represents a row in csv
                        if len (row) >= 1:
                            table=row[0].split(';')
                            if len(table)>=17:
                                search=self.env['stock.picking'].search([('sale_reference','=',str(table[14])),('carrier_id','=',carrier_id.id)])
                                for record in search:
                                    record.carrier_tracking_ref=table[17]
                                    record.delivery_state="shipping_recorded_in_carrier"
                                    record.status_code="NLU"
                                    for p in record.package_ids:
                                        p.carrier_tracking_ref=record.carrier_tracking_ref
                                        p.carrier_tracking_url=record.carrier_tracking_url
                                        p.delivery_state="shipping_recorded_in_carrier"
                                        p.status_code="NLU"
                                    record.tracking_send()
                            