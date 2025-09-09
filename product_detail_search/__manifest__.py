# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################## -*- coding: utf-8 -*-
{
    'name': 'Find Products in Pos and Stock using Barcode',
    'version': '18.0.1.0.1',  # bumped so upgrade applies cleanly
    'category': 'Point of Sale',
    'summary': (
        'Find Products in POS and Stock using barcode scanning to quickly '
        'identify and track items. Each product is assigned a unique barcode.'
    ),
    'description': (
        'Find Products in POS and Inventory enhances operational efficiency, '
        'reduces manual errors, improves customer service, and provides '
        'insights for better inventory management and decisions.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'stock'],

    'data': [
        'views/stock_views.xml',   # ✅ COMMA FIXED
        'views/app_menu.xml',
    ],

    'images': [
        'static/description/icon.png',   # optional: shows in Apps list
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
