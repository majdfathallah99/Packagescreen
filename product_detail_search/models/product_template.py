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
        Robust lookup:
          1) product.product.barcode
          2) product.template.barcode  -> take main variant
          3) product.packaging.barcode -> take linked product
        Then ALWAYS try to pick a packaging for the found product/template so
        package_qty/package_price are present for normal barcodes too.
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

        # ---------- Choose a packaging to DISPLAY ----------
        def _qty(pk):
            """Read qty across versions; ensure int >= 0."""
            if not pk:
                return 0
            if "qty" in Packaging._fields:
                return int(pk.qty or 0)
            if "contained_quantity" in Packaging._fields:
                return int(pk.contained_quantity or 0)
            return 0

        def _pick_display_pack(prod):
            """Prefer a sales pack with qty>=2; else any pack with qty>=2; else any pack with qty>=1."""
            dom_base = ["|",
                ("product_id", "=", prod.id),
                ("product_tmpl_id", "=", prod.product_tmpl_id.id),
            ]

            # A) if scanned a pack, use it
            if scanned_pack:
                return scanned_pack if _qty(scanned_pack) >= 1 else False

            # B) sales packs with qty>=2
            if "sales" in Packaging._fields:
                pk = Packaging.search(["&", ("sales", "=", True)] + dom_base, order="id", limit=50)
                best = next((p for p in pk if _qty(p) >= 2), False)
                if best:
                    return best

            # C) any pack with qty>=2
            any_pk = Packaging.search(dom_base, order="id", limit=50)
            best = next((p for p in any_pk if _qty(p) >= 2), False)
            if best:
                return best

            # D) as a last resort, any pack with qty>=1
            best = next((p for p in any_pk if _qty(p) >= 1), False)
            return best or False

        pack_rec = _pick_display_pack(product)
        package_qty = _qty(pack_rec)

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
