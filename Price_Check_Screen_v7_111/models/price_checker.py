# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PriceCheckerWizard(models.TransientModel):
    _name = "price.checker.wizard"
    _description = "Price Checker Wizard"

    barcode = fields.Char(string="Scan/Type Barcode", help="Scan with a USB barcode scanner or type manually.")
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_name = fields.Char(string="Name", readonly=True)
    uom_name = fields.Char(string="UoM", readonly=True)
    list_price = fields.Monetary(string="List Price", currency_field="currency_id", readonly=True)
    price = fields.Monetary(string="Price", currency_field="currency_id", readonly=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id, readonly=True)
    image_128 = fields.Image(related="product_id.image_128", readonly=True)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Behave like a real price checker:
        - On each scan/entry, show ONLY the last product found.
        - Clear the barcode field immediately after a successful match so it's ready for the next scan.
        """
        for wizard in self:
            code = (wizard.barcode or '').strip()
            if not code:
                # If cleared, also clear results
                wizard.update({
                    'product_id': False,
                    'product_name': False,
                    'uom_name': False,
                    'list_price': 0.0,
                    'price': 0.0,
                })
                continue

            Product = wizard.env['product.product']
            # Try exact barcode on product first
            product = Product.search([('barcode', '=', code)], limit=1)
            if not product:
                # Try template barcode via product variant
                product = Product.search([('product_tmpl_id.barcode', '=', code)], limit=1)
            if not product:
                # Fall back to internal reference (default_code)
                product = Product.search([('default_code', '=', code)], limit=1)

            if product:
                wizard.update({
                    'product_id': product.id,
                    'product_name': product.display_name or product.name,
                    'uom_name': product.uom_id and product.uom_id.name or False,
                    'list_price': product.lst_price,  # show template price
                    'price': product.lst_price,
                    'barcode': False,  # IMPORTANT: clear after match
                })
            else:
                # Not found -> keep typed code visible, but clear previous product info
                wizard.update({
                    'product_id': False,
                    'product_name': _('Not found'),
                    'uom_name': False,
                    'list_price': 0.0,
                    'price': 0.0,
                })

    def action_new_scan(self):
        # Still keep this method (even if button hidden) in case someone triggers it from dev tools.
        self.update({
            "barcode": False,
            "product_id": False,
            "product_name": False,
            "uom_name": False,
            "list_price": 0.0,
            "price": 0.0,
        })
