# -*- coding: utf-8 -*-
import os
from datetime import datetime
import requests
import json
from ftplib import FTP
import csv
from csv import reader
import datetime
import requests
from requests.auth import HTTPBasicAuth
from odoo import models, fields, api, _



class Leave(models.Model):
    _inherit = 'hr.leave'

    def importAbsenceFromCrm(self):
        url = "http://141.94.171.159/crm/Companies/getAbsenceToOdoo"

        data = json.loads(requests.get(url, auth=HTTPBasicAuth('alfaprint', '590-Alfaprint')).content)
        for line in data:
            user_obj = self.env["res.users"].sudo().search([('partner_id', '=', line['absences']['user_id'])], limit=1)
            employee_obj = self.env["hr.employee"].sudo().search([('user_id', '=', user_obj.id)], limit=1)
            holiday_status = self.env["hr.leave.type"].sudo().search([('name', '=', line['absences']['raison'])], limit=1)
            start = str(line['absences']['debut_absence']).split('-')
            end = str(line['absences']['fin_absence']).split('-')
            start.reverse()
            end.reverse()
            try:
                self.sudo().create({
                    "holiday_status_id": holiday_status.id,
                    "employee_id": employee_obj.id,
                    "holiday_type": "employee",
                    "date_from": "-".join(start),
                    "date_to": "-".join(end),
                })
            except:
                raise Exception(line['absences'])
