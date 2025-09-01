# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Autoscan)",
    "version": "18.0.1.1.4",
    "summary": "Scan a barcode and instantly see product & price (no Enter)",
    "author": "You",
    "license": "LGPL-3",
    "category": "Sales/Products",
    "depends": ["product", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/price_checker_views.xml",
        "views/price_checker_menu.xml",
        "views/price_checker_views_extend.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "price_checker_kiosk_autoscan_fix3/static/src/js/price_checker_autoscan.js"
        ]
    },
    "application": True,
    "images": ["static/description/icon.png"],
    "icon": "price_checker_kiosk_autoscan_fix3/static/description/icon.png",
    "installable": True
}
