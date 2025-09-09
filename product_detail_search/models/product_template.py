from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _sanitize_code(self, code):
        s = (code or "").strip()
        # Arabic-Indic → ASCII
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
        s = s.translate(trans)
        # collapse internal spaces
        s = " ".join(s.split())
        return s

    @api.model
    def product_detail_search(self, barcode):
        code = self._sanitize_code(barcode)
        if not code:
            return False

        # Use sudo() + include archived to avoid record-rule/active filters blocking the match
        Product   = self.env["product.product"].sudo().with_context(active_test=False)
        Template  = self.env["product.template"].sudo().with_context(active_test=False)
        Packaging = self.env["product.packaging"].sudo().with_context(active_test=False)

        product = False
        packaging = False

        # 1) Exact match on variant barcode
        product = Product.search([("barcode", "=", code)], limit=1)

        # 1.b) Try the same without/with leading zeros (some DBs strip/pad)
        if not product and code.isdigit():
            product = Product.search([("barcode", "=", code.lstrip("0"))], limit=1) or \
                      Product.search([("barcode", "=", code.zfill(13))], limit=1)

        # 2) Template barcode
        if not product:
            tmpl = Template.search([("barcode", "=", code)], limit=1)
            if not tmpl and code.isdigit():
                tmpl = Template.search([("barcode", "=", code.lstrip("0"))], limit=1) or \
                       Template.search([("barcode", "=", code.zfill(13))], limit=1)
            if tmpl:
                product = tmpl.product_variant_id or Product.search(
                    [("product_tmpl_id", "=", tmpl.id)], limit=1
                )

        # 3) Optional fallback: internal reference (some users scan SKU labels)
        if not product:
            product = Product.search([("default_code", "=", code)], limit=1)

        # 4) Packaging barcode
        if not product:
            packaging = Packaging.search([("barcode", "=", code)], limit=1)
            if not packaging and code.isdigit():
                packaging = Packaging.search([("barcode", "=", code.lstrip("0"))], limit=1) or \
                            Packaging.search([("barcode", "=", code.zfill(13))], limit=1)
            if packaging:
                product = packaging.product_id or Product.search(
                    [("product_tmpl_id", "=", packaging.product_tmpl_id.id)], limit=1
                )

        if not product:
            _logger.info("product_detail_search: no match for code=%s", code)
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
            # Show a default sales packaging if present (works on both product_id/product_tmpl_id)
            pk = Packaging.search([
                "|", ("product_id", "=", product.id),
                     ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ("sales", "=", True),
            ], limit=1)
            package_qty = _pack_qty(pk)

        unit_price    = product.list_price or 0.0
        package_price = unit_price * package_qty if package_qty else 0.0
        currency      = (product.currency_id or self.env.company.currency_id)

        res = {
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
        }
        _logger.info("product_detail_search: hit %s via %s for code=%s",
                     res["id"], res["scanned_as"], code)
        return [res]
