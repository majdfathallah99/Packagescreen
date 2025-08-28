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

    def _find_product(self, code):
        Product = self.env["product.product"]
        code = (code or "").strip()
        if not code:
            return Product.browse()
        prod = Product.search([("barcode", "=", code)], limit=1)
        if prod:
            return prod
        tmpl = self.env["product.template"].search([("barcode", "=", code)], limit=1)
        if tmpl:
            v = Product.search([("product_tmpl_id", "=", tmpl.id)], limit=1)
            if v:
                return v
        prod = Product.search([("default_code", "=", code)], limit=1)
        return prod

    def _compute_price(self, product):
        return product.list_price if product else 0.0

    @api.onchange("barcode")
    def _onchange_autoscan(self):
        for wiz in self:
            product = wiz._find_product(wiz.barcode)
            if not product:
                wiz.update({
                    "product_id": False,
                    "product_name": False,
                    "uom_name": False,
                    "list_price": 0.0,
                    "price": 0.0,
                })
                continue
            wiz.product_id = product.id
            wiz.product_name = product.display_name
            wiz.uom_name = product.uom_id.display_name if product.uom_id else False
            wiz.list_price = product.list_price
            wiz.price = wiz._compute_price(product)

    def action_check(self):
        # Compatibility if any view/button still calls this
        self._onchange_autoscan()
        return {
            "type": "ir.actions.act_window",
            "res_model": "price.checker.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_new_scan(self):
        self.update({
            "barcode": False,
            "product_id": False,
            "product_name": False,
            "uom_name": False,
            "list_price": 0.0,
            "price": 0.0,
        })
