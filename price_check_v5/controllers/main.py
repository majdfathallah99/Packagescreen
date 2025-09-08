# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class PriceCheckerKiosk(http.Controller):

    @http.route("/price_check/kiosk", type="http", auth="user", website=True)
    def kiosk_page(self, **kw):
        return request.render("price_check.kiosk_template", {})

    @http.route("/price_check/api/lookup", type="json", auth="user")
    def api_lookup(self, barcode=None):
        if not barcode:
            return {"ok": False}
        p = request.env["product.product"].sudo().search([("barcode","=",barcode)], limit=1)
        if not p:
            p = request.env["product.product"].sudo().search([("default_code","=",barcode)], limit=1)
        if not p:
            p = request.env["product.product"].sudo().search([("name","ilike",barcode)], limit=1)
        if not p:
            return {"ok": False}
        cur = p.currency_id or request.env.company.currency_id
        sym = cur.symbol or ""
        base_price = p.list_price
        pkg = p.packaging_ids.sorted("qty")[:1]
        pkg_price = None
        if pkg:
            qty = pkg[0].qty or 1.0
            pkg_price = base_price * qty
        return {
            "ok": True,
            "name": p.display_name,
            "currency": sym,
            "left_title": "عبوة" if pkg_price is not None else "وحدة",
            "left_value": pkg_price if pkg_price is not None else base_price,
            "right_title": "قطعة" if pkg_price is not None else "",
            "right_value": base_price if pkg_price is not None else None,
        }
