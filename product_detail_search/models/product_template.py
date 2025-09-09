from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, barcode):
        """Return product details by product barcode OR packaging barcode."""
        Product = self.env['product.product']
        Packaging = self.env['product.packaging']

        product = Product.search([('barcode', '=', barcode)], limit=1)
        packaging = False

        # 1) If no product barcode match, try packaging barcode
        if not product:
            packaging = Packaging.search([('barcode', '=', barcode)], limit=1)
            if packaging:
                # packaging can link to product OR product_tmpl depending on version
                product = packaging.product_id or (
                    packaging.product_tmpl_id
                    and Product.search([('product_tmpl_id', '=', packaging.product_tmpl_id.id)], limit=1)
                )

        if not product:
            return False

        # 2) Determine packaging quantity
        # Field name may be `qty` (v16/17) or `contained_quantity` (v18+ in some DBs)
        def _pack_qty(pk):
            if not pk:
                return 0
            if 'qty' in Packaging._fields:
                return int(pk.qty or 0)
            if 'contained_quantity' in Packaging._fields:
                return int(pk.contained_quantity or 0)
            return 0

        package_qty = _pack_qty(packaging) if packaging else 0
        # if scanned product barcode (not packaging), still try to show a default sales packaging
        if not package_qty:
            pk = Packaging.search([
                '|', ('product_id', '=', product.id),
                     ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('sales', '=', True)
            ], limit=1)
            package_qty = _pack_qty(pk)

        unit_price = product.list_price or 0.0
        package_price = unit_price * package_qty if package_qty else 0.0
        currency = product.currency_id or self.env.company.currency_id

        return [{
            'id': product.id,
            'name': product.display_name,
            'default_code': product.default_code or "",
            'uom': product.uom_id and product.uom_id.display_name or "",
            'price': unit_price,
            'package_qty': int(package_qty),
            'package_price': package_price,
            'currency_symbol': (currency and currency.symbol) or "",
            # meta about what was scanned
            'scanned_as': 'packaging' if packaging else 'product',
            'scanned_barcode': barcode,
        }]
