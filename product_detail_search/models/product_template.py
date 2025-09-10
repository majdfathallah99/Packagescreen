from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _sanitize_code(self, code):
        s = (code or "").strip()
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰١٢٣٤٥٦٧٨٩", "01234567890123456789")
        return s.translate(trans)

    @api.model
    def product_detail_search(self, barcode):
        """
        Find product by:
          1) product.product.barcode
          2) product.template.barcode (main variant)
          3) product.packaging.barcode (linked product/template)

        Then ALWAYS pick a packaging to display for that product/template:
          - prefer sales=True with the largest quantity
          - else the largest quantity overall
        """
        code = self._sanitize_code(barcode)
        if not code:
            return False

        Product   = self.env["product.product"].sudo().with_context(active_test=False)
        Template  = self.env["product.template"].sudo().with_context(active_test=False)
        Packaging = self.env["product.packaging"].sudo().with_context(active_test=False)

        product = False
        scanned_pack = False

        # 1) Variant barcode
        product = Product.search([("barcode", "=", code)], limit=1)

        # 2) Template barcode -> main variant
        if not product:
            tmpl = Template.search([("barcode", "=", code)], limit=1)
            if tmpl:
                product = tmpl.product_variant_id or Product.search([("product_tmpl_id", "=", tmpl.id)], limit=1)

        # 3) Packaging barcode -> linked product/template
        if not product:
            scanned_pack = Packaging.search([("barcode", "=", code)], limit=1)
            if scanned_pack:
                product = scanned_pack.product_id or Product.search(
                    [("product_tmpl_id", "=", scanned_pack.product_tmpl_id.id)], limit=1
                )

        if not product:
            return False

        # ---------- choose a packaging to DISPLAY ----------
        def _qty_from_obj(p):
            # Handle both field names across versions
            if hasattr(p, "contained_quantity"):
                return int(p.contained_quantity or 0)
            if hasattr(p, "qty"):
                return int(p.qty or 0)
            return 0

        # if user scanned a packaging barcode, use that packaging
        display_pack = scanned_pack if scanned_pack else False

        if not display_pack:
            # collect ALL packagings linked to variant OR template
            packs = Packaging.search([
                "|",
                ("product_id", "=", product.id),
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
            ])

            if packs:
                # 1) prefer sales=True with the largest quantity
                if "sales" in Packaging._fields:
                    sales_packs = packs.filtered(lambda r: bool(getattr(r, "sales", False)))
                    if sales_packs:
                        display_pack = max(sales_packs, key=_qty_from_obj)
                # 2) else largest quantity overall
                if not display_pack:
                    display_pack = max(packs, key=_qty_from_obj)

        package_qty = _qty_from_obj(display_pack) if display_pack else 0

        unit_price = product.list_price or 0.0
        package_price = unit_price * package_qty if package_qty else 0.0
        currency = product.currency_id or self.env.company.currency_id

        return [{
            "id": product.id,
            "name": product.display_name,
            "default_code": product.default_code or "",
            "uom": product.uom_id and product.uom_id.display_name or "",
            "price": unit_price,
            "package_qty": int(package_qty),
            "package_price": package_price,
            "currency_symbol": (currency and currency.symbol) or "",
            "scanned_as": "packaging" if scanned_pack else "product",
            "scanned_barcode": code,
        }]
