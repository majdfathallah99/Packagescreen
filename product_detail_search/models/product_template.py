from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, barcode):
        """Find by variant barcode, then template barcode, then packaging barcode.
        Returns one dict with unit + pack info for the chosen product.
        """
        Product = self.env["product.product"]
        Template = self.env["product.template"]
        Packaging = self.env["product.packaging"]

        product = False
        packaging = False

        # 1) Variant barcode
        product = Product.search([("barcode", "=", barcode)], limit=1)

        # 2) Template barcode (if variant has no barcode but template does)
        if not product:
            tmpl = Template.search([("barcode", "=", barcode)], limit=1)
            if tmpl:
                # prefer the main variant
                product = tmpl.product_variant_id or Product.search(
                    [("product_tmpl_id", "=", tmpl.id)], limit=1
                )

        # 3) Packaging barcode
        if not product:
            packaging = Packaging.search([("barcode", "=", barcode)], limit=1)
            if packaging:
                product = packaging.product_id or (
                    packaging.product_tmpl_id
                    and Product.search(
                        [("product_tmpl_id", "=", packaging.product_tmpl_id.id)],
                        limit=1,
                    )
                )

        if not product:
            return False

        # --- compute packaging qty if known ---
        def _pack_qty(pk):
            if not pk:
                return 0
            # tolerate field name differences
            if "qty" in Packaging._fields:
                return int(pk.qty or 0)
            if "contained_quantity" in Packaging._fields:
                return int(pk.contained_quantity or 0)
            return 0

        package_qty = _pack_qty(packaging) if packaging else 0
        if not package_qty:
            # show a default sales packaging if present
            pk = Packaging.search([
                "|", ("product_id", "=", product.id),
                     ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ("sales", "=", True),
            ], limit=1)
            package_qty = _pack_qty(pk)

        unit_price = product.list_price or 0.0
        package_price = unit_price * package_qty if package_qty else 0.0
        currency = self.env.company.currency_id

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
            "scanned_barcode": barcode,
        }]
