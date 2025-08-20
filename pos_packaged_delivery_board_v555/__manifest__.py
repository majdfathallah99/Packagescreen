    # -*- coding: utf-8 -*-
    {
        "name": "POS Packaged Delivery Board",
        "version": "18.0.3.3.0",
        "summary": "Paid-only board for changed UoM lines, immediate on validate + auto-refresh.",
        "license": "LGPL-3",
        "author": "You",
        "category": "Point of Sale",
        "depends": ["point_of_sale", "product"],
        "data": [
            "views/menu.xml",
            "views/card_views.xml",
            "data/server_actions.xml",
            "security/ir.model.access.csv"
        ]
, "assets": {
    "web.assets_backend": [
        "pos_packaged_delivery_board/static/src/js/reloader.js",
        "pos_packaged_delivery_board/static/src/xml/reloader.xml"
    ]
}
,
        "images": ["static/description/icon.svg"],
        "installable": True,
        "application": True
    }
