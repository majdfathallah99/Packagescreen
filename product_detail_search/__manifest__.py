# -*- coding: utf-8 -*-
{
    "name": "Find Products in POS and Stock using Barcode",
    "version": "18.0.1.0.6",  # bump version for rebuild
    "category": "Point of Sale",
    "summary": "Find products by barcode in POS & Inventory",
    "description": """
        Adds a barcode-based product search dashboard in Inventory and
        a helper in POS. Shows product name, unit price, UoM, and package price.
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["point_of_sale", "stock"],
    "data": [
        "views/stock_views.xml",
    ],
    "images": ["static/description/banner.jpg"],
    "assets": {
        # Backend dashboard (safe)
        "web.assets_backend": [
            "product_detail_search/static/src/js/dashboard.js",
            "product_detail_search/static/src/xml/dashboard_templates.xml",
            "product_detail_search/static/src/css/dashboard.css",
            # Uncomment if barcode.css actually exists
            # "product_detail_search/static/src/css/barcode.css",
        ],

        # POS assets (⚠️ enable later once backend is stable)
        # "point_of_sale.assets": [
        #     "product_detail_search/static/src/css/pos.css",
        #     "product_detail_search/static/src/js/find_product_button.js",
        #     "product_detail_search/static/src/js/find_product.js",
        #     "product_detail_search/static/src/js/product_details.js",
        #     "product_detail_search/static/src/xml/find_product_screen_templates.xml",
        #     "product_detail_search/static/src/xml/product_details_templates.xml",
        #     "product_detail_search/static/src/xml/chrome_templates.xml",
        # ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
