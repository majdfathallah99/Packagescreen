{
    "name": "Find Products in Pos and Stock using Barcode",
    "version": "18.0.1.0.5",  # <- bump to force fresh assets
    "category": "Point of Sale",
    "summary": "Find products by barcode in POS & Inventory",
    "description": "Minimal dashboard + POS helpers.",
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["point_of_sale", "stock"],
    "data": [
        "views/stock_views.xml",
    ],
    "images": ["static/description/banner.jpg"],
    "assets": {
        # BACKEND (dashboard)
        "web.assets_backend": [
            "product_detail_search/static/src/js/dashboard.js",
            "product_detail_search/static/src/xml/dashboard_templates.xml",
            "product_detail_search/static/src/css/dashboard.css",
            # If barcode.css is really needed, keep it; otherwise comment it out while testing
            # "product_detail_search/static/src/css/barcode.css",
        ],
        # POS (enable AFTER backend is stable)
        "point_of_sale.assets": [
            "product_detail_search/static/src/css/pos.css",
            "product_detail_search/static/src/js/find_product_button.js",
            "product_detail_search/static/src/js/find_product.js",
            "product_detail_search/static/src/js/product_details.js",
            "product_detail_search/static/src/xml/find_product_screen_templates.xml",
            "product_detail_search/static/src/xml/product_details_templates.xml",
            "product_detail_search/static/src/xml/chrome_templates.xml",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
