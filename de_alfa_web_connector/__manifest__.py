{
    "name": "Alfa Print Web Connector",
    "author": "Dynexcel",
    "website": "https://www.dynexcel.com",
    "category": "sale",
    "summary": "To connect Odoo with alfa website ",
    "description": """To connect Odoo with alfa website, using rest API's""",
    "version": "14.0.1.1",
    "depends": ["base", "sale", "sale_management", "purchase", "stock" ],
    "application": True,
    "data": [
        'wizard/wizard_message_view.xml',
        'wizard/import_wizard_views.xml',
        'wizard/change_supplier.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/mail_data.xml',
        'views/res_partner_views.xml',
        'views/cron_view.xml',
        'views/sale_view.xml',
        'views/purchase_order.xml',
        'views/product_product_view.xml',
        'views/product_supplierinfo_view.xml',
        'views/stock_picking.xml',
        'views/picking_ticket_id.xml',
        'views/picking_delivery_type.xml',
    ],
    "qweb": [],
    "auto_install": False,
    "installable": True,
    "license": "OPL-1",
    "price": 20,
    "currency": "EUR"
}
