# -*- coding: utf-8 -*-
{
    "name": "Find Products in POS and Stock using Barcode",
    "version": "18.0.1.0.7",  # bump for rebuild
    "category": "Point of Sale",
    "summary": "Find products by barcode in POS & Inventory",
    "description": "Minimal install while we isolate asset issues.",
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["point_of_sale", "stock"],
    "data": [
        "views/stock_views.xml",
    ],
    "images": ["static/description/banner.jpg"],
    # TEMP: no assets until it loads
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
