# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import os
import logging
import csv
from csv import reader
from odoo import _
from odoo.exceptions import UserError
from ftplib import FTP


_logger = logging.getLogger(__name__)


class GlsRequest(object):
    def __init__(self, carrier, record):
        self.carrier = carrier
        self.record = record
        self.appVersion = 14
        self.host = self.carrier.gls_alfa_host
        self.user =self.carrier.gls_alfa_user
        self.password =self.carrier.gls_alfa_password
        self.ftp = FTP(self.host, self.user, self.password)




   



    def _prepare_create_shipping(self):
        tableau_csv=[['ORDERID', 'ORDERIDREF', 'ORDERNAME',
         'ORDERWEIGHTUNI', 'CONSID', 'CONTACTNAME', 'CONTACTPHONE',
         'CONTACTMAIL', 'STREET1', 'STREET2',
         'CONTRYCODE', 'ZIPCODE', 'CITY'],
         [self.record.id,self.record.sale_reference,self.record.partner_id.name,1.3,self.record.partner_id.id,self.record.partner_id.name,
            self.record.partner_id.phone, self.record.partner_id.email,self.record.partner_id.delivery_addres, self.record.partner_id.region_name,
           self.record.partner_id.delivery_country,self.record.partner_id.delivery_code_zip,self.record.partner_id.delivery_city]]


        return tableau_csv



    def _send_shipping(self):
            if not self.record.package_ids:
                print ("hello not packages")
                try:
                    self.record._put_in_pack(self.record.move_line_ids_without_package)
                except:
                    pass
            if not self.record.partner_id.phone:
                raise UserError(_("""Ajouter un phone number"""))
            if not self.record.partner_id.delivery_country and not self.record.partner_id.delivery_city and not self.record.partner_id.delivery_code_zip:
                self.record.partner_id.delivery_addres=self.record.partner_id.street 
                self.record.partner_id.delivery_country=self.record.partner_id.billing_country
                self.record.partner_id.delivery_city=self.record.partner_id.city
                self.record.partner_id.delivery_code_zip=self.record.partner_id.zip
                
                if not self.record.partner_id.billing_country:
                    self.record.partner_id.billing_country='FR'
                    self.record.partner_id.delivery_country='FR'
                    
                    
                
                    
                if not self.record.partner_id.city or not self.record.partner_id.zip or not self.record.partner_id.street:
                                
                    raise UserError(_("""Veuillez saisir les informations de livraisons"""))
            try:
                if not self.record.sale_reference or len(self.record.sale_reference) == 0:
                    raise UserError(_(f"Empty Sale Reference {self.record.origin}!"))
            except:
                raise UserError(_(f"Empty Sale Reference {self.record.origin}!"))
            namefile=r'%s.csv' % (self.record.sale_reference)
            LocalDestinationPath =os.path.join(r'/opt/odoo/addons_alfa/de_alfa_ftp_gls/static/description/files/gls',namefile)
        
            with open(LocalDestinationPath, 'w+',newline='') as f:  # Ouverture du fichier CSV en écriture
                ecrire = csv.writer(f,delimiter=';')
                for i in self._prepare_create_shipping():
                    ecrire.writerow(i)
            ftp = self.ftp
            
 
            try:
                with open( LocalDestinationPath, 'rb' ) as file :
                    ftp.storbinary('STOR %s' % namefile, file)
                self.record.delivery_state="shipping_recorded_in_carrier"
                os.remove(LocalDestinationPath)
            except:
             
                ftp.close()


    
                                    


    def tracking_state_update(self):
        return True
        



