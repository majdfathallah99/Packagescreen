# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board",
    "version": "18.0.3.1.1",
    "summary": "Live on validate. Adds 'Done' stage & bulk move.",
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
