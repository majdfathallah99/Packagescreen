from odoo import api, models
from odoo.tools import float_round

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, raw_code):
        """
        Given a scanned `raw_code` (product EAN, template EAN, or packaging barcode),
        return a list with one dict describing the product and pricing to show in POS.

        CHANGE: If barcode hits a *packaging*, we now try to fetch the *UoM price*
        from pos_multi_uom_price (variant > template) and use it as the "package price".
        """
        # -------------------------------
        # Helpers
        # -------------------------------
        def _normalize(code):
            if not code:
                return ""
            trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
            return code.translate(trans).strip()

        def _find_product_by_barcode(code):
            Product = self.env["product.product"]
            # variant barcode
            p = Product.search([("barcode", "=", code)], limit=1)
            if p:
                return p
            # template barcode
            tmpl = self.search([("barcode", "=", code)], limit=1)
            if tmpl:
                # pick the first saleable variant
                v = tmpl.product_variant_id or tmpl.product_variant_ids[:1]
                return v
            return False

        def _find_packaging_by_barcode(code):
            return self.env["product.packaging"].search([("barcode", "=", code)], limit=1)

        def _map_packaging_to_uom(packaging, product):
            """Best-effort mapping:
            1) use packaging.uom_id if it exists (recommended)
            2) else map by name (case-insensitive) within the same UoM category as product's UoM
            """
            UoM = self.env["uom.uom"]
            # 1) explicit field (if you added it in your env)
            uom = getattr(packaging, "uom_id", False)
            if uom:
                return uom

            # 2) by name (safe category)
            name = (packaging.name or "").strip()
            if not name:
                return False
            cat = product.uom_id.category_id.id if product.uom_id else False
            domain = [("name", "=ilike", name)]
            if cat:
                domain.append(("category_id", "=", cat))
            uom = UoM.search(domain, limit=1)
            return uom

        def _get_uom_price(product, uom):
            """Look up price from your multi-UoM module.
            Try variant model first, then template model.
            Accepted model names seen in your module analysis:
              - 'product.multi.uom.price' (variant)
              - 'product.tmpl.multi.uom.price' (template)
            """
            # variant-level
            try:
                VariantPrice = self.env["product.multi.uom.price"]
                vp = VariantPrice.search(
                    [("product_id", "=", product.id), ("uom_id", "=", uom.id)],
                    limit=1,
                )
                if vp:
                    return vp.price
            except Exception:
                pass

            # template-level
            try:
                TmplPrice = self.env["product.tmpl.multi.uom.price"]
                tp = TmplPrice.search(
                    [("product_tmpl_id", "=", product.product_tmpl_id.id), ("uom_id", "=", uom.id)],
                    limit=1,
                )
                if tp:
                    return tp.price
            except Exception:
                pass

            return None

        # -------------------------------
        # Main logic
        # -------------------------------
        code = _normalize(raw_code)
        if not code:
            return False

        Product = self.env["product.product"]
        Packaging = self.env["product.packaging"]
        company = self.env.company

        product = _find_product_by_barcode(code)
        packaging = False
        package_qty = 1.0
        package_price = None  # we'll set it below

        if not product:
            # Maybe it's a packaging barcode
            packaging = _find_packaging_by_barcode(code)
            if packaging:
                product = Product.browse(packaging.product_id.id)
                package_qty = packaging.qty or 1.0

        if not product:
            return False

        # Base (unit) price shown by many templates
        list_price = product.lst_price

        # If packaging was scanned, compute "package_price" using UoM price
        if packaging:
            uom = _map_packaging_to_uom(packaging, product)
            if uom:
                uom_price = _get_uom_price(product, uom)
                if uom_price is not None:
                    # Use UoM price instead of packaging price
                    package_price = float_round(uom_price, precision_rounding=product.currency_id.rounding)
                else:
                    # No configured UoM price → fallback to product price (or keep None if you prefer)
                    package_price = float_round(list_price, precision_rounding=product.currency_id.rounding)

        # If not packaging (normal scan), keep default behavior (no package price)
        # Build UoM prices list for the details panel (optional)
        uom_prices = []
        try:
            VariantPrice = self.env["product.multi.uom.price"]
            for row in VariantPrice.search([("product_id", "=", product.id)]):
                uom_prices.append({
                    "uom_id": row.uom_id.id,
                    "uom_name": row.uom_id.display_name,
                    "price": row.price,
                })
        except Exception:
            try:
                TmplPrice = self.env["product.tmpl.multi.uom.price"]
                for row in TmplPrice.search([("product_tmpl_id", "=", product.product_tmpl_id.id)]):
                    uom_prices.append({
                        "uom_id": row.uom_id.id,
                        "uom_name": row.uom_id.display_name,
                        "price": row.price,
                    })
            except Exception:
                pass

        # Response expected by your JS
        res = {
            "id": product.id,
            "display_name": product.display_name,
            "barcode": product.barcode or "",
            "default_code": product.default_code or "",
            "list_price": list_price,

            # Packaging section used by the POS "details" module:
            "package_qty": package_qty,
            "package_price": package_price,  # <— now the UoM price when packaging is scanned

            # Extra info for UI
            "uom_prices": uom_prices,
            "category": product.categ_id.display_name if product.categ_id else "",
            "qty_available": product.qty_available,
            "company_id": [company.id, company.name],
            "type": product.type or "",
            "specification": product.description_sale or "",
            "tax_amount": "",
        }
        return [res]
