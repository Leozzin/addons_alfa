# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Set carrier in transfert",
    "summary": "Set carrier in wizard transfert",
    "version": "14.0.1.0.1",
    "category": "Delivery",
    "website": "https://alfaprint.fr",
    "author": "Alfaprint-amal",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "development_status": "Production/Stable",
    "depends": ["delivery"],
    "data": [
        "wizard/stock_immediate_transfer_views.xml",
        "wizard/stock_backorder_confirmation.xml",
    ],
}
