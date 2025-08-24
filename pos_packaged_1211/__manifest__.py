# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board (1234)",
    "version": "18.0.4.0.3",
    "summary": "Adds 'Done' stage and a Kanban header button to move Confirmed → Done.",
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
