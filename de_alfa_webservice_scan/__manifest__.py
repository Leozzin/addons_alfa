# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Alfa webservice",
    "summary": "websevice",
    "version": "14.0.1.0.0",
    "category": "Delivery",
    "website": "https://alfaprint.fr",
    "author": "Amal-ALFA",
    "license": "AGPL-3",
    "depends": [
        "stock",

    ],

    "installable": True,
    "maintainers": ["victoralmau"],
    "data":[
        "report/report_picking.xml",
        "report/report_delivery_slip.xml",
        "views/serial_number.xml"
    ],
}
