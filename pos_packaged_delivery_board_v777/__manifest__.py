# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board",
    "version": "18.0.3.1.0+refreshonly",
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
    , "pos_packaged_delivery_board_v18_nowizard_paidonly_live_nocreate/data/server_actions.xml"],
    "images": ["static/description/icon.svg"],
    "installable": True,
    "application": True
}
