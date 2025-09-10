from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # normalize Arabic/Persian digits just in case
    def _sanitize_code(self, code):
        s = (code or "").strip()
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰١٢٣٤٥٦٧٨٩", "01234567890123456789")
        return s.translate(trans)

    @api.model
    def product_detail_search(self, barcode):
        """
        Clone packaging behavior for regular barcodes:
        - Find product via product.barcode -> template.barcode -> packaging.barcode
        - Then ALWAYS choose a packaging for that product/template using the SAME rule
          as when a packaging barcode is scanned:
            1) If the scanned code was a packaging -> use that packaging
            2) Else prefer sales=True with the largest quantity
            3) Else the largest quantity overall
        - Works with either `contained_quantity` (v17/18) or `qty` (older DBs)
          and with packaging linked by product_id or product_tmpl_id.
        """
        code = self._sanitize_code(barcode)
        if not code:
            return False

        Product   = self.env["product.product"].sudo().with_context(active_test=False)
        Template  = self.env["product.template"].sudo().with_context(active_test=False)
        Packaging = self.env["product.packaging"].sudo().with_context(active_test=False)

        product = False
        scanned_pack = False

        # 1) product.product.barcode
        product = Product.search([("barcode", "=", code)], limit=1)

        # 2) product.template.barcode  -> main variant
        if not product:
            tmpl = Template.search([("barcode", "=", code)], limit=1)
            if tmpl:
                product = tmpl.product_variant_id or Product.search(
                    [("product_tmpl_id", "=", tmpl.id)], limit=1
                )

        # 3) product.packaging.barcode -> linked product/template
        if not product:
            scanned_pack = Packaging.search([("barcode", "=", code)], limit=1)
            if scanned_pack:
                product = scanned_pack.product_id or Product.search(
                    [("product_tmpl_id", "=", scanned_pack.product_tmpl_id.id)], limit=1
                )

        if not product:
            return False

        # --------- clone packaging-selection logic (used for BOTH paths) ---------
        def _qty(pk):
            """Return integer quantity from either contained_quantity or qty."""
            if not pk:
                return 0
            if "contained_quantity" in Packaging._fields:
                q = int(pk.contained_quantity or 0)
                if q:
                    return q
            if "qty" in Packaging._fields:
                return int(pk.qty or 0)
            return 0

        def _pick_pack(prod, prefer=None):
            # If we scanned a packaging barcode, use that exact packaging
            if prefer and _qty(prefer) >= 1:
                return prefer

            # All packagings attached to variant OR template
            packs = Packaging.search([
                "|",
                ("product_id", "=", prod.id),
                ("product_tmpl_id", "=", prod.product_tmpl_id.id),
            ])

            if not packs:
                return False

            # Prefer sales=True with the largest quantity
            if "sales" in Packaging._fields:
                sales_packs = packs.filtered(lambda p: bool(getattr(p, "sales", False)))
                if sales_packs:
                    return max(sales_packs, key=_qty)

            # Else largest quantity overall
            return max(packs, key=_qty)

        display_pack = _pick_pack(product, prefer=scanned_pack)
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
