# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Kiosk Full Page + Wizard)",
    "summary": "Full-page scanner at /price_check/kiosk + optional popup wizard. No SCSS.",
    "version": "18.0.1.0.6",
    "category": "Sales/Point of Sale",
    "author": "ChatGPT",
    "license": "LGPL-3",
    "depends": ["base", "product", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/price_checker_kiosk_view.xml",
        "views/price_checker_kiosk_template.xml",
    ],
    "installable": True,
    "application": True,
    "icon": "price_check/static/description/icon.png"
}
