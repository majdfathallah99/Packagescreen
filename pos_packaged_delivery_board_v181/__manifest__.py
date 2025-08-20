# -*- coding: utf-8 -*-
{
    "name": "POS Packaged Delivery Board",
    "version": "18.0.3.1.0+autorefresh",
    "summary": "Paid-only, live on validate. UI: no 'New' button (create disabled in views).",
    "license": "LGPL-3",
    "author": "You",
    "category": "Point of Sale",
    "depends": ['point_of_sale', 'product', 'web'],
    "data": [
        "views/menu.xml",
        "views/card_views.xml",
        "data/server_actions.xml",
        "security/ir.model.access.csv"
    ],
    "images": ["static/description/icon.svg"],
    "installable": True,
    "application": True
, "assets": {
    "web.assets_backend": [
        "pos_packaged_delivery_board_v18_nowizard_paidonly_live_nocreate/static/src/js/auto_refresh.js", "pos_packaged_delivery_board_v18_nowizard_paidonly_live_nocreate/static/src/xml/auto_refresh.xml"
    ]
}

}
