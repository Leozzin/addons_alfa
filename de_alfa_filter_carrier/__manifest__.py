{
    "name": "Alfa carrier filter",
    "summary": "Condition to show carrier",
    "version": "14.0.1.0.1",
    "category": "Delivery",
    "website": "https://alfaprint.fr",
    "author": "Alfaprint-amal",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "development_status": "Production/Stable",
    "depends": ["de_alfa_send_multi_carrier"],
    "data": [

        "views/delivery_carrier_view.xml",
        "wizard/stock_carrier_transfer_views.xml",
    ],
}
