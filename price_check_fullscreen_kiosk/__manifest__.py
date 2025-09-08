# -*- coding: utf-8 -*-
{
    "name": "Price Checker (Fullscreen Kiosk)",
    "summary": "Scan barcode and show large prices for unit/package in fullscreen popup.",
    "version": "18.0.1.0.0",
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
            "price_check/static/src/scss/price_checker_kiosk.scss",
            "price_check/static/src/js/price_checker_kiosk.js",
        ],
    },
    "icon": "price_check/static/description/icon.png",
    "installable": True,
    "application": True,
}
