# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Alfa Delivery Chronopost",
    "summary": "Integrate Chronopost webservice",
    "version": "14.0.1.0.0",
    "category": "Delivery",
    "website": "https://alfaprint.fr",
    "author": "Amal-ALFA",
    "license": "AGPL-3",
    "depends": [
        "delivery",
        "delivery_state",
        "product_dimension",
        "base_sparse_field",
    ],
    "data": [
        "views/delivery_carrier_view.xml",
        # "views/product_packaging.xml",
        # "views/stock_picking.xml"


    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
