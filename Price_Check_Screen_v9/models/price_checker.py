# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PriceCheckerWizard(models.TransientModel):
    _name = "price.checker.wizard"
    _description = "Price Checker Wizard"

    # Input
    barcode = fields.Char(string="Scan/Type Barcode", help="Scan with a USB barcode scanner or type manually.")

    # Basic info
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_name = fields.Char(string="Name", readonly=True)
    uom_name = fields.Char(string="UoM", readonly=True)

    # Pricing
    list_price = fields.Monetary(string="List Price", currency_field="currency_id", readonly=True)
    price = fields.Monetary(string="Price", currency_field="currency_id", readonly=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id, readonly=True)

    # Image kept but not displayed
    image_128 = fields.Image(related="product_id.image_128", readonly=True)

    # Display-only big/bold HTML
    name_html = fields.Html(string="Name (HTML)", readonly=True)
    barcode_html = fields.Html(string="Barcode (HTML)", readonly=True)
    price_html = fields.Html(string="Price (HTML)", readonly=True)
    uom_html = fields.Html(string="UoM (HTML)", readonly=True)

    # Alternate UoMs
    other_uoms_html = fields.Html(string="Other UoMs & Prices", readonly=True)

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

            # Basic fields
            wiz.product_id = product.id
            wiz.product_name = product.display_name
            wiz.uom_name = product.uom_id.display_name if product.uom_id else False
            wiz.list_price = product.list_price or 0.0
            wiz.price = product.list_price or 0.0

            # HTML blocks (big & bold)
            wiz.name_html = wiz._html_block("h1", wiz.product_name or "")
            wiz.barcode_html = wiz._html_block("h2", wiz.barcode or "")
            sym = wiz.currency_id and wiz.currency_id.symbol or ""
            wiz.price_html = f"<h1><strong>{(wiz.price or 0.0):.2f} {sym}</strong></h1>"
            wiz.uom_html = wiz._html_block("h3", wiz.uom_name or "")

            # Alternate UoMs
            wiz.other_uoms_html = wiz._compute_other_uoms_html(product)

    def _find_product(self, barcode):
        if not barcode:
            return False
        Product = self.env["product.product"]
        # Prefer barcode exact match
        product = Product.search([("barcode", "=", barcode)], limit=1)
        if product:
            return product
        # Try internal reference
        product = Product.search([("default_code", "=", barcode)], limit=1)
        if product:
            return product
        # As a last resort, search by name contains
        product = Product.search([("name", "ilike", barcode)], limit=1)
        return product or False

    
    
    def _compute_other_uoms_html(self, product):
        """Build HTML for alternative UoMs in same category AND product packagings.
        - UoMs: convert list_price using product.uom_id._compute_price(list_price, u)
        - Packaging: search by product_tmpl_id (primary) and fallback to product_id;
                     price_total = list_price * qty; also show per-unit price.
        No CSS; use headings/strong only.
        """
        if not product:
            return False

        sym = self.currency_id and self.currency_id.symbol or ""

        # 1) Alternative UoMs in same category
        uom_section = ""
        if product.uom_id and product.uom_id.category_id:
            u_lines = []
            for u in product.uom_id.category_id.uom_ids:
                if u.id == product.uom_id.id:
                    continue
                try:
                    price_in_u = product.uom_id._compute_price(product.list_price or 0.0, u)
                except Exception:
                    price_in_u = 0.0
                u_lines.append(f"<p><strong>{u.display_name}</strong>: {price_in_u:.2f} {sym}</p>")
            if u_lines:
                head = f"<h3>Other Units / وحدات أخرى</h3>"
                uom_section = "<div>" + head + "".join(u_lines) + "</div>"

        # 2) Product Packagings (boxes, packs)
        pkg_section = ""
        p_lines = []
        Packaging = self.env['product.packaging']
        domain = [('product_tmpl_id', '=', product.product_tmpl_id.id)]
        pkgs = Packaging.search(domain)
        if not pkgs:
            # fallback just in case
            pkgs = Packaging.search([('product_id', '=', product.id)])
        for p in pkgs:
            qty = getattr(p, 'qty', 0.0) or 0.0  # contained quantity
            name = getattr(p, 'name', '') or 'Package'
            barcode = getattr(p, 'barcode', '') or ''
            sales_ok = getattr(p, 'sales', False)
            total_price = (product.list_price or 0.0) * qty
            per_unit = (total_price / qty) if qty else 0.0
            line = f"<p><strong>{name}</strong> ({qty:g} {product.uom_id.display_name if product.uom_id else ''})"
            if barcode:
                line += f" – {barcode}"
            if sales_ok:
                line += " ✅"
            line += f": <strong>{total_price:.2f} {sym}</strong> <small>(~{per_unit:.2f} {sym} / {product.uom_id.display_name if product.uom_id else ''})</small></p>"
            p_lines.append(line)
        if p_lines:
            head = "<h3>Packaging / التعبئة</h3>"
            pkg_section = "<div>" + head + "".join(p_lines) + "</div>"

        # 3) Default UoM header
        default_head = ""
        if product.uom_id:
            default_head = f"<div><h3>{product.uom_id.display_name}</h3><p><strong>{(product.list_price or 0.0):.2f} {sym}</strong></p></div>"

        result = default_head + uom_section + pkg_section
        return result or False


        sym = self.currency_id and self.currency_id.symbol or ""

        # 1) Alternative UoMs in same category
        uom_section = ""
        if product.uom_id and product.uom_id.category_id:
            u_lines = []
            for u in product.uom_id.category_id.uom_ids:
                if u.id == product.uom_id.id:
                    continue
                try:
                    price_in_u = product.uom_id._compute_price(product.list_price or 0.0, u)
                except Exception:
                    price_in_u = 0.0
                u_lines.append(f"<p><strong>{u.display_name}</strong>: {price_in_u:.2f} {sym}</p>")
            if u_lines:
                head = f"<h3>Other Units</h3>"
                uom_section = "<div>" + head + "".join(u_lines) + "</div>"

        # 2) Product Packagings (boxes, packs)
        pkg_section = ""
        try:
            pkgs = self.env['product.packaging'].search([('product_id', '=', product.id), ('active', 'in', [True, False])])
        except Exception:
            pkgs = self.env['product.packaging']
        p_lines = []
        for p in pkgs:
            # qty = number of base units in this package
            qty = getattr(p, 'qty', 0.0) or 0.0
            name = getattr(p, 'name', '') or 'Package'
            barcode = getattr(p, 'barcode', '') or ''
            total_price = (product.list_price or 0.0) * qty
            line = f"<p><strong>{name}</strong> ({qty:g} {product.uom_id.display_name if product.uom_id else ''})"
            if barcode:
                line += f" – {barcode}"
            line += f": {total_price:.2f} {sym}</p>"
            p_lines.append(line)
        if p_lines:
            head = "<h3>Packaging</h3>"
            pkg_section = "<div>" + head + "".join(p_lines) + "</div>"

        # 3) Default UoM header
        default_head = ""
        if product.uom_id:
            default_head = f"<div><h3>{product.uom_id.display_name}</h3><p><strong>{(product.list_price or 0.0):.2f} {sym}</strong></p></div>"

        result = default_head + uom_section + pkg_section
        return result or False


        sym = self.currency_id and self.currency_id.symbol or ""
        lines = []
        for u in product.uom_id.category_id.uom_ids:
            if u.id == product.uom_id.id:
                continue
            try:
                price_in_u = product.uom_id._compute_price(product.list_price or 0.0, u)
            except Exception:
                price_in_u = 0.0
            lines.append(f"<p><strong>{u.display_name}</strong>: {price_in_u:.2f} {sym}</p>")
        if not lines:
            return False

        head = f"<h3>{product.uom_id.display_name}</h3><p><strong>{(product.list_price or 0.0):.2f} {sym}</strong></p>"
        return "<div>" + head + "".join(lines) + "</div>"

    def _html_block(self, tag, text):
        text = text or ""
        # minimal escape
        text = (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;"))
        return f"<{tag}><strong>{text}</strong></{tag}>"

    def action_open(self):
        self.ensure_one()
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
        return {"type": "ir.actions.act_window_close"}
