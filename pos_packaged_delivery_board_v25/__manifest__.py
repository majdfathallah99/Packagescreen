# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board",
    "version": "18.0.2.0.0",
    "summary": "Two columns: New Orders / Confirmed. Confirm button. No popup.",
    "license": "LGPL-3",
    "author": "You",
    "category": "Point of Sale",
    "depends": ["point_of_sale", "product"],
    "data": [
        "views/menu.xml",
        "views/card_views.xml",
        "data/server_actions.xml",
        "security/ir.model.access.csv"
    ],
    "images": ["static/description/icon.svg"],
    "installable": True,
    "application": True
}
