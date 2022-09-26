# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Alfa carrier popup send",
    "summary": "multi action send",
    "version": "14.0.1.0.1",
    "category": "Delivery",
    "website": "https://alfaprint.fr",
    "author": "Alfaprint-amal",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "development_status": "Production/Stable",
    "depends": ["delivery","delivery_state","de_alfa_ws_tnt"],
    "data": [
        "wizard/stock_carrier_transfer_views.xml",
        "views/stock_picking.xml",
        "security/ir.model.access.csv",
         "data/data.xml"
    ],
}
