# This file is part of an Adiczion's Module.
# The COPYRIGHT and LICENSE files at the top level of this repository
# contains the full copyright notices and license terms.
{
    'name': 'Colissimo Shipping',
    'version': '13.0.12',
    'author': 'Adiczion SARL',
    'category': 'Adiczion',
    'license': 'AGPL-3',
    'depends': [
        'delivery',
        'mail',
        'a4o_delivery_relaypoint',
        'a4o_delivery_slip',
    ],
    'external_dependencies': {'python': ['zeep', 'suds-community']},
    'demo': [],
    'website': 'http://adiczion.com',
    'description': """
Colissimo Shipping
==================

Send your shippings through Colissimo and track them online.

    """,
    'data': [
        # 'security/objects_security.xml',
        'security/ir.model.access.csv',
        'data/delivery_colissimo_data.xml',
        'views/delivery_colissimo_views.xml',
        'views/stock_picking_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/select_printer_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'test': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
