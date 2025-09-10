from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _sanitize_code(self, code):
        s = (code or "").strip()
        # Arabic/Persian digits -> ASCII
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰١٢٣٤٥٦٧٨٩", "01234567890123456789")
        return s.translate(trans)

    @api.model
    def product_detail_search(self, barcode):
        """
        product.product.barcode -> product.template.barcode -> product.packaging.barcode
        Then ALWAYS choose a packaging to display for the found product/template:
          - prefer sales=True with the highest quantity
          - else the highest quantity
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

        # -------------------- choose a packaging to DISPLAY --------------------
        # Read all packagings attached to variant or template in one query
        packs = Packaging.search_read(
            ["|", ("product_id", "=", product.id),
                  ("product_tmpl_id", "=", product.product_tmpl_id.id)],
            ["id", "sales", "qty", "contained_quantity"],
            limit=0,
        )

        def _q(p):
            # Support both field names; ensure int >= 0
            return int((p.get("qty") if "qty" in p else p.get("contained_quantity") or 0) or 0)

        display_qty = 0

        if scanned_pack:
            # If the scanned code WAS a packaging barcode, use exactly that packaging
            pk = Packaging.browse(scanned_pack.id)
            display_qty = int((pk.qty if "qty" in Packaging._fields else pk.contained_quantity) or 0)
        else:
            # Prefer sales=True with the largest qty
            sales = [p for p in packs if p.get("sales")]
            if sales:
                display_qty = _q(max(sales, key=_q))
            elif packs:
                display_qty = _q(max(packs, key=_q))

        unit_price = product.list_price or 0.0
        package_qty = int(display_qty or 0)
        package_price = unit_price * package_qty if package_qty else 0.0
        currency = product.currency_id or self.env.company.currency_id

        return [{
            "id": product.id,
            "name": product.display_name,
            "default_code": product.default_code or "",
            "uom": product.uom_id and product.uom_id.display_name or "",
            "price": unit_price,
            "package_qty": package_qty,
            "package_price": package_price,
            "currency_symbol": (currency and currency.symbol) or "",
            "scanned_as": "packaging" if scanned_pack else "product",
            "scanned_barcode": code,
        }]
