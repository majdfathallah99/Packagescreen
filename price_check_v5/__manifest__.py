# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Kiosk Full Page + Wizard)",
    "summary": "Two ways: 1) Fullscreen page at /price_check/kiosk, 2) Popup wizard (optional).",
    "version": "18.0.1.0.5",
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
    "icon": "price_check/static/description/icon.png",
}
