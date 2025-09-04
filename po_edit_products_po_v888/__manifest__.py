# -*- coding: utf-8 -*-
{
    "name": "PO Edit Products Popup",
    "version": "18.0.1.0.0",
    "summary": "Edit product prices (sale/cost), price per UoM, and packaging price from a Purchase Order popup",
    "category": "Purchases",
    "author": "ChatGPT",
    "license": "LGPL-3",
    "depends": ["purchase","uom","product"],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order_view.xml",
        "views/wizard_views.xml"
    ],
    "installable": True,
    "application": False
}
