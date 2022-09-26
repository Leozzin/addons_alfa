{
    "name": "Alfa compute ready",
    "summary": "Computer number of ready picking",
    "version": "14.0.1.0.1",
    "category": "Delivery",
    "website": "https://alfaprint.fr",
    "author": "Alfaprint-amal",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "development_status": "Production/Stable",
    "depends": ["stock","delivery_state"],
    "data": [
        "views/res_partner.xml",
        "views/stock_picking_view.xml",
    ],
}
