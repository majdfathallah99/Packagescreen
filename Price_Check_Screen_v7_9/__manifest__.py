# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Autoscan)",
    "version": "18.0.1.1.9",
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
            "Price_Check_Screen_v7_7/static/src/css/price_checker.css",
            "Price_Check_Screen_v7_7/static/src/js/price_checker_autoscan.js"
        ]
    },
    "application": True,
    "images": ["static/description/icon.png"],
    "icon": "Price_Check_Screen_v7_7/static/description/icon.png",
    "installable": True
}
