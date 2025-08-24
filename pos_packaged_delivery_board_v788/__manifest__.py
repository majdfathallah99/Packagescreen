# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board",
    "version": "18.0.3.1.0",
    "summary": "Paid-only, live on validate. UI: no 'New' button (create disabled in views).",
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
,
    'assets': {
        'web.assets_backend': [
            'pos_packaged_delivery_board_v7777/static/src/scss/ppdb_kanban.scss',
        ],
    }
}
