from odoo import api, fields,models, _
from datetime import datetime
import base64, urllib
from io import BytesIO
import xlrd
from odoo.exceptions import UserError
class ImportData(models.TransientModel):
    _name="import.data"
    _description = 'Import Account Data'

    upload_file = fields.Binary("File")
    user = fields.Boolean()

    def read_excel(self):
        if not self.upload_file:
            raise UserError(_("Error!, Please Select a File"))
        else:
            val = base64.decodestring(self.upload_file )
            tempfile = BytesIO()
            tempfile.write(val)
            work_book = xlrd.open_workbook(file_contents=tempfile.getvalue()) 
        return work_book

    contract_template = fields.Binary(string="Template")




    
    

    def data_upload_account(self):
        wb = self.read_excel()
        sheet= wb.sheet_by_index(0)
        sheet_rows=sheet.nrows
        partner_obj = self.env['res.partner']
        user_obj = self.env['res.users']
        
        count = 0
        temp_duplicate = 0
        lst = []
        if self.user != True:
            for row in range(1,sheet_rows):
                data_dict={}    
                account_id = partner_obj.search([('old_api_id','=',sheet.row_values(row)[0])])
                if account_id:
                    continue
                else:
                    address=True
                    vals={
                    'old_api_id':int(sheet.row_values(row)[0]),
                    'name':sheet.row_values(row)[1],
                    'supplier_rank':1
                    }
                    partner_obj.create(vals)
                    count=count+1
        else:
            for row in range(1,sheet_rows):
                data_dict={}    
                account_id = user_obj.search([('old_api_id','=',sheet.row_values(row)[0])])
                if account_id:
                    continue
                else:
                    address=True
                    vals={
                    'old_api_id':int(sheet.row_values(row)[0]),
                    'name':sheet.row_values(row)[1],
                    
                    }
                    if sheet.row_values(row)[2]:
                        vals['login']=sheet.row_values(row)[2]
                    else:
                        vals['login']=sheet.row_values(row)[1]
                    user_obj.create(vals)
                    count=count+1

            
        
        
        if count == 0:
            message = 'Accounts Already Exits !!!!! '
        if count !=0 and temp_duplicate==0:
            message = 'All Accounts uploaded successfully !!!!! '
        if count !=0 and temp_duplicate!=0:
            message = str(count)+' New Accounts Uploaded and '+str(temp_duplicate)+ ' Accounts uploaded dupliicate!!!!! '

        # message = 'All Accounts uploaded successfully !!!!! '
        temp_id = self.env['wizard.message'].create({'text':message})
        return {
        'name':_("Test Result"),
        'view_mode': 'form',
        'view_id': False,
        'view_type': 'form',
        'res_model': 'wizard.message',
        'res_id': temp_id.id,
        'type': 'ir.actions.act_window',
        'nodestroy': True,
        'target': 'new',
        'domain': '[]',
       }
