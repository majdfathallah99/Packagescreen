from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, barcode):
        """Find by barcode and return data for the kiosk dashboard."""
        product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
        if not product:
            return False

        uom_name = product.uom_id.name or ""
        unit_price = product.list_price or 0.0
        currency = product.currency_id or self.env.company.currency_id

        # pick packaging (default > qty>1 > first)
        packaging = product.packaging_ids.filtered(lambda p: getattr(p, "is_default", False))[:1]
        if not packaging:
            packaging = product.packaging_ids.filtered(lambda p: (p.qty or 0) > 1)[:1]
        if not packaging:
            packaging = product.packaging_ids[:1]
        packaging = packaging and packaging[0] or False

        package_qty = int(packaging.qty) if (packaging and packaging.qty) else 0
        package_price = (unit_price * package_qty) if package_qty else 0.0

        return [{
            'id': product.id,
            'name': product.display_name,
            'default_code': product.default_code or "",
            'uom': uom_name,
            'price': unit_price,
            'package_qty': package_qty,
            'package_price': package_price,
            'symbol': (currency and currency.symbol) or "",
            'currency_symbol': (currency and currency.symbol) or "",
        }]
