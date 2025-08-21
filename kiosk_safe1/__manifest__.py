# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Kiosk)",
    "version": "18.0.1.0.3",
    "summary": "Scan a barcode and display product price (with optional pricelist/partner)",
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
    "icon": "price_checker_kiosk/static/description/icon.png",
    "installable": True
}
