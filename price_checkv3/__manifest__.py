# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Fullscreen Kiosk)",
    "summary": "Fullscreen barcode price checker with big dual prices (package & piece).",
    "version": "18.0.1.0.3",
    "category": "Sales/Point of Sale",
    "author": "ChatGPT",
    "license": "LGPL-3",
    "depends": ["base", "product", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/price_checker_kiosk_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "price_check/static/src/css/price_checker_kiosk.css",
            "price_check/static/src/js/price_checker_kiosk.js",
        ],
    },
    "icon": "price_check/static/description/icon.png",
    "installable": True,
    "application": True,
}
