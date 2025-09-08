# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
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
            p = self.env["product.product"].search([("barcode", "=", self.barcode)], limit=1)
            if not p:
                p = self.env["product.product"].search([("default_code", "=", self.barcode)], limit=1)
            if not p:
                p = self.env["product.product"].search([("name", "ilike", self.barcode)], limit=1)

        if not p:
            self.update({
                "product_id": False,
                "currency_id": self.env.company.currency_id.id,
                "kiosk_html": self._render_kiosk(None),
            })
            return

        self.product_id = p.id
        self.currency_id = p.currency_id.id or self.env.company.currency_id.id

        cur = p.currency_id or self.env.company.currency_id
        sym = html_escape(cur.symbol or "")
        base_price = p.list_price

        # pick a packaging if available (sale packaging with min qty), else None
        pkg_records = p.packaging_ids.filtered(lambda x: not x.hide_on_ui)  # generic condition
        pkg_records = pkg_records.sorted("qty")
        pkg = pkg_records[:1]
        pkg_price = None
        pkg_name = None
        if pkg:
            pkg = pkg[0]
            qty = pkg.qty or 1.0
            pkg_name = pkg.name or _("Package")
            pkg_price = base_price * qty

        self.kiosk_html = self._render_kiosk({
            "name": p.display_name,
            "left_title": pkg_name or _("Unit"),
            "left_value": pkg_price if pkg_price is not None else base_price,
            "right_title": _("Piece") if pkg_name else _("Unit"),
            "right_value": base_price if pkg_name else None,
            "currency_symbol": sym,
        })

    def _render_kiosk(self, data):
        if not data:
            return """
<div class="pc-kiosk">
  <div class="pc-logo"></div>
  <div class="pc-name">—</div>
  <div class="pc-row">
    <div class="pc-col">
      <div class="pc-pill pc-pill-left">—</div>
      <div class="pc-price">—</div>
    </div>
    <div class="pc-col">
      <div class="pc-pill pc-pill-right">—</div>
      <div class="pc-price">—</div>
    </div>
  </div>
</div>
"""
        def fmt(v):
            # Format like 32.000 (3 decimals), using dot as thousands in your sample.
            return f"{v:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")

        left_value = data.get("left_value")
        right_value = data.get("right_value")
        sym = html_escape(data.get("currency_symbol") or "")
        name = html_escape(data.get("name") or "")
        left_title = html_escape(data.get("left_title") or "")
        right_title = html_escape(data.get("right_title") or "")

        return f"""
<div class="pc-kiosk">
  <div class="pc-logo"></div>
  <div class="pc-name">{name}</div>
  <div class="pc-row">
    <div class="pc-col">
      <div class="pc-pill pc-pill-left">{left_title}</div>
      <div class="pc-price">{fmt(left_value)} {sym}</div>
    </div>
    <div class="pc-col">
      <div class="pc-pill pc-pill-right">{right_title}</div>
      <div class="pc-price">{(fmt(right_value) + ' ' + sym) if right_value is not None else ''}</div>
    </div>
  </div>
</div>
"""
