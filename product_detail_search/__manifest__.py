# -*- coding: utf-8 -*-
{
    'name': 'Find Products in Pos and Stock using Barcode',
    'version': '18.0.1.0.6',  # bump so Odoo reloads
    'category': 'Point of Sale',
    'summary': (
        'Find Products in POS and Stock using barcode scanning to quickly '
        'identify and track items.'
    ),
    'description': (
        'Find Products in POS and Inventory enhances efficiency, reduces errors, '
        'improves customer service, and provides better inventory insights.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'stock'],
    'application': True,
    'installable': True,
    'auto_install': False,

    'data': [
        'views/stock_views.xml',
        'views/app_menu.xml',
    ],

    # images REMOVED (icon.png / banner.jpg)

    'assets': {
        'web.assets_backend': [
            # 'product_detail_search/static/src/css/barcode.css',  # REMOVED
            'product_detail_search/static/src/css/dashboard.css',
            'product_detail_search/static/src/js/dashboard.js',
            'product_detail_search/static/src/xml/dashboard_templates.xml',
        ],
        'point_of_sale.assets': [
            'product_detail_search/static/src/css/pos.css',
            'product_detail_search/static/src/js/find_product_button.js',
            'product_detail_search/static/src/js/find_product.js',
            'product_detail_search/static/src/js/product_details.js',
            'product_detail_search/static/src/xml/find_product_screen_templates.xml',
            'product_detail_search/static/src/xml/product_details_templates.xml',
            'product_detail_search/static/src/xml/chrome_templates.xml',
        ],
    },
}
