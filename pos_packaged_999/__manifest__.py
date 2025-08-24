# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board (Final)",
    "version": "18.0.4.0.0",
    "summary": "Adds 'Done' stage and a header button to move all Confirmed → Done.",
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
