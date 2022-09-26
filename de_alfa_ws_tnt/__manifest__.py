# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Alfa Delivery TNT",
    "summary": "Integrate TNT webservice",
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
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "views/delivery_carrier_view.xml",
        "views/product_packaging.xml",
        "views/stock_picking.xml",
        "views/stock_move.xml"


    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
