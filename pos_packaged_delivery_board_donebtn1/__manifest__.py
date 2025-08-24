# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board (Done Button)",
    "version": "18.0.5.0.0",
    "summary": "Adds 'Done' stage and a control-bar button to move all Confirmed → Done.",
    "license": "LGPL-3",
    "author": "You",
    "category": "Point of Sale",
    "depends": ["point_of_sale", "product"],
    "data": [
        "views/menu.xml",
        "views/card_views.xml",
        "security/ir.model.access.csv"
    ],
    "images": ["static/description/icon.svg"],
    "installable": True,
    "application": True
}
