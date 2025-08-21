# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PriceCheckerWizard(models.TransientModel):
    _name = "price.checker.wizard"
    _description = "Price Checker Wizard"

    barcode = fields.Char(string="Scan/Type Barcode", help="Scan with a USB barcode scanner or type manually.")
    partner_id = fields.Many2one("res.partner", string="Customer (optional)")
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_name = fields.Char(string="Name", readonly=True)
    uom_name = fields.Char(string="UoM", readonly=True)
    list_price = fields.Monetary(string="List Price", currency_field="currency_id", readonly=True)
    price = fields.Monetary(string="Price (pricelist)", currency_field="currency_id", readonly=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id)
    image_128 = fields.Image(related="product_id.image_128", readonly=True)

    def action_check(self):
        self.ensure_one()
        if not self.barcode:
            raise UserError(_("Please scan or type a barcode."))
        Product = self.env["product.product"]
        # Try product barcode, then template barcode, then default_code
        product = Product.search([("barcode", "=", self.barcode.strip())], limit=1)
        if not product:
            tmpl = self.env["product.template"].search([("barcode", "=", self.barcode.strip())], limit=1)
            if tmpl:
                product = Product.search([("product_tmpl_id", "=", tmpl.id)], limit=1)
        if not product:
            product = Product.search([("default_code", "=", self.barcode.strip())], limit=1)

        if not product:
            self.write({
                "product_id": False,
                "product_name": _("No product found for: %s") % self.barcode,
                "uom_name": False,
                "list_price": 0.0,
                "price": 0.0,
            })
            return

        self.product_id = product.id
        self.product_name = product.display_name
        self.uom_name = product.uom_id.display_name if product.uom_id else False
        self.list_price = product.list_price

        final_price = self.list_price
        if self.pricelist_id:
            # Try typical pricelist helpers gracefully
            try:
                final_price = self.pricelist_id._get_product_price(product, 1.0, self.partner_id)
            except Exception:
                try:
                    res = self.pricelist_id._compute_price_rule([(product, 1.0, self.partner_id)])
                    final_price = res.get(product.id, (self.list_price, False))[0]
                except Exception:
                    pass
        self.price = final_price

    def action_new_scan(self):
        self.write({
            "barcode": False,
            "product_id": False,
            "product_name": False,
            "uom_name": False,
            "list_price": 0.0,
            "price": 0.0,
        })
