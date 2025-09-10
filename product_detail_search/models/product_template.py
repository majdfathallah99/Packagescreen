from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # optional: normalize Arabic-Indic digits, trim spaces
    def _sanitize_code(self, code):
        s = (code or "").strip()
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
        return s.translate(trans)

    @api.model
    def product_detail_search(self, barcode):
        """
        Robust lookup: product.product -> product.template -> product.packaging.
        ALWAYS tries to include a packaging (sales preferred) even when scanning a normal barcode.
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

        # ------- pick a packaging to display (even for normal barcodes) -------
        # Helper to read qty across versions
        def _qty(pk):
            if not pk:
                return 0
            if "qty" in Packaging._fields:
                return int(pk.qty or 0)
            if "contained_quantity" in Packaging._fields:
                return int(pk.contained_quantity or 0)
            return 0

        package_qty = 0
        pack_rec = False

        if scanned_pack:
            pack_rec = scanned_pack
            package_qty = _qty(pack_rec)

        if not package_qty:
            # Prefer a SALES packaging tied to this product or its template
            domain_base = ["|",
                ("product_id", "=", product.id),
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
            ]
            # first: sales=True
            if "sales" in Packaging._fields:
                pack_rec = Packaging.search(["&", ("sales", "=", True)] + domain_base, limit=1)
                package_qty = _qty(pack_rec)

            # second: any packaging with qty > 1
            if not package_qty:
                candidates = Packaging.search(domain_base, limit=1)
                if candidates:
                    pack_rec = candidates
                    package_qty = _qty(pack_rec)

        unit_price = product.list_price or 0.0
        package_price = (unit_price * package_qty) if package_qty else 0.0
        currency = (product.currency_id or self.env.company.currency_id)

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
