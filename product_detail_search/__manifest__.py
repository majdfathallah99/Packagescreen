# -*- coding: utf-8 -*-
{
    'name': 'Find Products in Pos and Stock using Barcode',
    'version': '18.0.1.0.24',  # bumped so upgrade reloads assets/data
    'category': 'Point of Sale',
    'summary': 'Find Products in Pos and Stock using Barcode utilizes barcode '
               'scanning to quickly identify and track items. Each product is assigned a unique barcode.',
    'description': 'Find Products in Pos and Stock using Barcode in the POS and inventory modules '
                   'enhances operational efficiency, reduces manual errors, improves customer service, '
                   'and provides insights for better inventory management and decisions.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'stock'],
    'data': [
        'views/stock_views.xml',      
        'views/app_menu.xml',
    ],
    'images': [
        'static/description/icon.png',   # show as app icon/preview
        'static/description/banner.jpg',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'product_detail_search/static/src/css/pos.css',
            'product_detail_search/static/src/js/find_product_button.js',
            'product_detail_search/static/src/js/find_product.js',
            'product_detail_search/static/src/js/product_details.js',
            'product_detail_search/static/src/xml/find_product_screen_templates.xml',
            'product_detail_search/static/src/xml/product_details_templates.xml',
            'product_detail_search/static/src/xml/chrome_templates.xml',
        ],
        'web.assets_backend': [
            'product_detail_search/static/src/css/barcode.css',
            'product_detail_search/static/src/css/dashboard.css',
            'product_detail_search/static/src/js/dashboard.js',
            'product_detail_search/static/src/xml/dashboard_templates.xml',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
