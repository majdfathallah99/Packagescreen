# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Autoscan)",
    "version": "18.0.1.1.2",
    "summary": "Scan a barcode and instantly see product & price (no button)",
    "author": "You",
    "license": "LGPL-3",
    "category": "Sales/Products",
    "depends": ["product", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/price_checker_views.xml",
        "views/price_checker_menu.xml"
    ],
    "application": True,
    "images": ["static/description/icon.png"],
    "icon": "price_checker_kiosk_autoscan_fix2/static/description/icon.png",
    "installable": True
}
