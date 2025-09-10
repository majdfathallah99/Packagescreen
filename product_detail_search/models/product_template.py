from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Normalize Arabic-Indic digits and trim
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

        Then ALWAYS choose a packaging to display for the found product/template:
          - prefer sales=True with highest qty
          - else any packaging with highest qty
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

        # 2) Template barcode
        if not product:
            tmpl = Template.search([("barcode", "=", code)], limit=1)
            if tmpl:
                product = tmpl.product_variant_id or Product.search(
                    [("product_tmpl_id", "=", tmpl.id)], limit=1
                )

        # 3) Packaging barcode
        if not product:
            scanned_pack = Packaging.search([("barcode", "=", code)], limit=1)
            if scanned_pack:
                product = scanned_pack.product_id or Product.search(
                    [("product_tmpl_id", "=", scanned_pack.product_tmpl_id.id)], limit=1
                )

        if not product:
            return False

        # ---------- choose a packaging to display (for normal barcodes too) ----------
        def _qty(pk):
            if not pk:
                return 0
            if "qty" in Packaging._fields:
                return int(pk.qty or 0)
            if "contained_quantity" in Packaging._fields:
                return int(pk.contained_quantity or 0)
            return 0

        # all packs attached to either the variant or its template
        packs = Packaging.search([
            "|",
            ("product_id", "=", product.id),
            ("product_tmpl_id", "=", product.product_tmpl_id.id),
        ])

        display_pack = False

        # if user actually scanned a packaging barcode, use that one
        if scanned_pack and _qty(scanned_pack) >= 1:
            display_pack = scanned_pack
        else:
            # 1) prefer sales=True (if field exists), with the largest qty
            sales_packs = packs
            if "sales" in Packaging._fields:
                sales_packs = packs.filtered(lambda p: bool(getattr(p, "sales", False)))
            if sales_packs:
                display_pack = max(sales_packs, key=_qty)
            # 2) else any pack with the largest qty
            if not display_pack and packs:
                display_pack = max(packs, key=_qty)

        package_qty = _qty(display_pack)
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
