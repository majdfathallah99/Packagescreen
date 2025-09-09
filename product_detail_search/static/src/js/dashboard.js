from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, *args, **kwargs):
        """
        Accepts multiple calling conventions:
          - [barcode]
          - [[], barcode] or ["", barcode]
          - kwargs: {'barcode': '...'}
        Returns a list with a single dict or False.
        """
        # Extract barcode from args/kwargs safely
        barcode = kwargs.get("barcode")
        if barcode is None:
            if len(args) == 1:
                barcode = args[0]
            elif len(args) >= 2:
                # First arg may be [] or "" (ignored); second is the barcode
                barcode = args[1]

        if not barcode:
            return False

        product = self.env["product.product"].search([("barcode", "=", barcode)], limit=1)
        if not product:
            return False

        uom_name = product.uom_id.name or ""
        unit_price = product.list_price or 0.0
        currency = product.currency_id or self.env.company.currency_id

        # Choose a packaging: default > qty>1 > first
        packaging = product.packaging_ids.filtered(lambda p: getattr(p, "is_default", False))[:1]
        if not packaging:
            packaging = product.packaging_ids.filtered(lambda p: (p.qty or 0) > 1)[:1]
        if not packaging:
            packaging = product.packaging_ids[:1]
        packaging = packaging and packaging[0] or False

        package_qty = int(packaging.qty) if (packaging and packaging.qty) else 0
        package_price = (unit_price * package_qty) if package_qty else 0.0

        symbol = (currency and currency.symbol) or ""

        return [{
            "id": product.id,
            "name": product.display_name,
            "default_code": product.default_code or "",
            "uom": uom_name,
            "price": unit_price,
            "package_qty": package_qty,
            "package_price": package_price,
            "symbol": symbol,
            "currency_symbol": symbol,  # for templates using either key
        }]
