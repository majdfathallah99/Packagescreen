from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # optional (keeps Arabic-Indic digits safe)
    def _sanitize_code(self, code):
        s = (code or "").strip()
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
        return s.translate(trans)

    @api.model
    def product_detail_search(self, barcode):
        Product   = self.env["product.product"]
        Packaging = self.env["product.packaging"]

        code = self._sanitize_code(barcode)

        # ► FIRST: match product by variant barcode OR template barcode (and default_code as a helpful fallback)
        product = Product.search([
            "|", "|",
            ("barcode", "=", code),                    # variant barcode
            ("product_tmpl_id.barcode", "=", code),    # template barcode
            ("default_code", "=", code),               # optional: internal reference
        ], limit=1)

        packaging = False

        # ► THEN: if no product match, try packaging barcode
        if not product:
            packaging = Packaging.search([("barcode", "=", code)], limit=1)
            if packaging:
                product = packaging.product_id or \
                          Product.search([("product_tmpl_id", "=", packaging.product_tmpl_id.id)], limit=1)

        if not product:
            return False

        # --- compute packaging qty if known ---
        def _pack_qty(pk):
            if not pk:
                return 0
            if "qty" in Packaging._fields:
                return int(pk.qty or 0)
            if "contained_quantity" in Packaging._fields:
                return int(pk.contained_quantity or 0)
            return 0

        package_qty = _pack_qty(packaging) if packaging else 0
        if not package_qty:
            pk = Packaging.search([
                "|", ("product_id", "=", product.id),
                     ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ("sales", "=", True),
            ], limit=1)
            package_qty = _pack_qty(pk)

        unit_price    = product.list_price or 0.0
        package_price = unit_price * package_qty if package_qty else 0.0
        currency      = self.env.company.currency_id

        return [{
            "id": product.id,
            "name": product.display_name,
            "default_code": product.default_code or "",
            "uom": product.uom_id and product.uom_id.display_name or "",
            "price": unit_price,
            "package_qty": int(package_qty),
            "package_price": package_price,
            "currency_symbol": (currency and currency.symbol) or "",
            "scanned_as": "packaging" if packaging else "product",
            "scanned_barcode": code,
        }]
