# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import html_escape

class PriceCheckerWizard(models.TransientModel):
    _name = "price.checker.wizard"
    _description = "Price Checker"

    barcode = fields.Char(string="Barcode")
    product_id = fields.Many2one("product.product", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    kiosk_html = fields.Html(sanitize=False, readonly=True)

    @api.onchange("barcode")
    def _onchange_barcode(self):
        self.ensure_one()
        p = False
        if self.barcode:
            p = self.env["product.product"].search([("barcode","=",self.barcode)], limit=1)
            if not p:
                p = self.env["product.product"].search([("default_code","=",self.barcode)], limit=1)
            if not p:
                p = self.env["product.product"].search([("name","ilike",self.barcode)], limit=1)
        if not p:
            self.kiosk_html = self._render_kiosk(None)
            return
        self.product_id = p.id
        self.currency_id = p.currency_id.id or self.env.company.currency_id.id
        cur = p.currency_id or self.env.company.currency_id
        sym = html_escape(cur.symbol or "")
        base_price = p.list_price
        pkg = p.packaging_ids.sorted("qty")[:1]
        pkg_price = None
        if pkg:
            qty = pkg[0].qty or 1.0
            pkg_price = base_price * qty
        self.kiosk_html = self._render_kiosk({
            "name": p.display_name,
            "left_title": "عبوة" if pkg_price is not None else "وحدة",
            "left_value": pkg_price if pkg_price is not None else base_price,
            "right_title": "قطعة" if pkg_price is not None else "",
            "right_value": base_price if pkg_price is not None else None,
            "currency_symbol": sym,
        })

    def _render_kiosk(self, data):
        if not data:
            return "<div class='pc-kiosk'><div class='pc-name'>—</div></div>"
        def fmt(v): return f"{v:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sym = html_escape(data.get("currency_symbol") or "")
        name = html_escape(data.get("name") or "")
        lt = html_escape(data.get("left_title") or "")
        rt = html_escape(data.get("right_title") or "")
        lv = data.get("left_value")
        rv = data.get("right_value")
        right_block = f"<div class='pc-col'><div class='pc-pill pc-pill-right'>{rt}</div><div class='pc-price'>{fmt(rv)} {sym}</div></div>" if rv is not None else ""
        return f"""<div class="pc-kiosk"><div class="pc-logo"></div><div class="pc-name">{name}</div><div class="pc-row"><div class="pc-col"><div class="pc-pill pc-pill-left">{lt}</div><div class="pc-price">{fmt(lv)} {sym}</div></div>{right_block}</div></div>"""
