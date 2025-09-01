# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PriceCheckerWizard(models.TransientModel):
    _name = "price.checker.wizard"
    _description = "Price Checker Wizard"

    barcode = fields.Char(string="Scan/Type Barcode", help="Scan with a USB barcode scanner or type manually.")
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_name = fields.Char(string="Name", readonly=True)
    uom_name = fields.Char(string="UoM", readonly=True)
    list_price = fields.Monetary(string="List Price", currency_field="currency_id", readonly=True)
    price = fields.Monetary(string="Price", currency_field="currency_id", readonly=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id, readonly=True)
    image_128 = fields.Image(related="product_id.image_128", readonly=True)

    # Display-only HTML blocks (big/bold via HTML tags, no CSS files)
    name_html = fields.Html(string="Name (HTML)", readonly=True)
    barcode_html = fields.Html(string="Barcode (HTML)", readonly=True)
    price_html = fields.Html(string="Price (HTML)", readonly=True)
    uom_html = fields.Html(string="UoM (HTML)", readonly=True)

    other_uoms_html = fields.Html(string="Other UoMs & Prices", readonly=True)

    def _find_product(self, code):
        Product = self.env["product.product"]
        code = (code or "").strip()
        if not code:
            return Product.browse()
        prod = Product.search([("barcode", "=", code)], limit=1)
        if prod:
            return prod
        tmpl = self.env["product.template"].search([("barcode", "=", code)], limit=1)
        if tmpl:
            v = Product.search([("product_tmpl_id", "=", tmpl.id)], limit=1)
            if v:
                return v
        prod = Product.search([("default_code", "=", code)], limit=1)
        return prod

    def _compute_price(self, product):
        return product.list_price if product else 0.0

    @api.onchange("barcode")
    def _onchange_autoscan(self):
        for wiz in self:
            product = wiz._find_product(wiz.barcode)
            if not product:
                wiz.update({
                    "product_id": False,
                    "product_name": False,
                    "uom_name": False,
                    "list_price": 0.0,
                    "price": 0.0,
            "name_html": False,
            "barcode_html": False,
            "price_html": False,
            "uom_html": False,
            "other_uoms_html": False,
                })
                continue
            \1
            wiz.name_html = wiz._html_block("h1", wiz.product_name or "")
            wiz.barcode_html = wiz._html_block("h2", wiz.barcode or "")
            # format price with currency symbol if available
            sym = wiz.currency_id and wiz.currency_id.symbol or ""
            wiz.price_html = f"<h1><strong>{(wiz.price or 0.0):.2f} {sym}</strong></h1>"
            wiz.uom_html = wiz._html_block("h3", wiz.uom_name or "")
            wiz.other_uoms_html = wiz._compute_other_uoms_html(product)
            wiz.other_uoms_html = wiz._compute_other_uoms_html(product)
            wiz.list_price = product.list_price
            wiz.price = wiz._compute_price(product)

    def action_check(self):
        # Compatibility if any view/button still calls this
        self._onchange_autoscan()
        return {
            "type": "ir.actions.act_window",
            "res_model": "price.checker.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_new_scan(self):
        self.update({
            "barcode": False,
            "product_id": False,
            "product_name": False,
            "uom_name": False,
            "list_price": 0.0,
            "price": 0.0,
            "name_html": False,
            "barcode_html": False,
            "price_html": False,
            "uom_html": False,
            "other_uoms_html": False,
        })

    def _compute_other_uoms_html(self, product):
        """Build simple HTML listing of alternative UoMs with computed prices.
        No CSS used; use headings/strong for emphasis to keep it readable and big."""
        if not product or not product.uom_id or not product.uom_id.category_id:
            return False
        # collect UoMs in same category (excluding the product default UoM)
        lines = []
        for u in product.uom_id.category_id.uom_ids:
            if u.id == product.uom_id.id:
                continue
            # compute price for this UoM from list_price of default UoM
            try:
                price_in_u = product.uom_id._compute_price(product.list_price, u)
            except Exception:
                price_in_u = 0.0
            lines.append(f"<p><strong>{u.display_name}</strong>: {price_in_u:.2f} {product.currency_id.symbol or ''}</p>")
        if not lines:
            return False
        # Include default uom & price first for clarity
        head = f"<h3>{product.uom_id.display_name}</h3><p><strong>{product.list_price:.2f} {product.currency_id.symbol or ''}</strong></p>"
        return "<div>" + head + "".join(lines) + "</div>"


    def _html_block(self, tag, text):
        text = text or ""
        # very simple escape for special chars
        text = (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))
        return f"<{tag}><strong>{text}</strong></{tag}>"
