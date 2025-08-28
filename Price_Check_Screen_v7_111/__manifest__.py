# -*- coding: utf-8 -*-
{
    "name": "Price Checker Kiosk (v7.5)",
    "version": "1.0.7.5",
    "summary": "Scan a barcode and instantly see product & price (no Enter)",
    "author": "You",
    "license": "LGPL-3",
    "category": "Sales/Products",
    "depends": ["product", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/price_checker_views.xml",
        "views/price_checker_menu.xml"
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
