# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

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
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id, readonly=True)
    image_128 = fields.Image(related="product_id.image_128", readonly=True)

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if "pricelist_id" in fields_list and not vals.get("pricelist_id"):
            pl = self.env["product.pricelist"].search([], limit=1)
            if pl:
                vals["pricelist_id"] = pl.id
        return vals

    def _find_product(self, code):
        Product = self.env["product.product"]
        code = (code or "").strip()
        if not code:
            return Product.browse()
        prod = Product.search([("barcode","=",code)], limit=1)
        if prod:
            return prod
        tmpl = self.env["product.template"].search([("barcode","=",code)], limit=1)
        if tmpl:
            v = Product.search([("product_tmpl_id","=",tmpl.id)], limit=1)
            if v:
                return v
        prod = Product.search([("default_code","=",code)], limit=1)
        return prod

    def _compute_price(self, product, partner, pricelist):
        if not product:
            return 0.0
        price = product.list_price
        if pricelist:
            try:
                price = pricelist._get_product_price(product, 1.0, partner)
            except Exception:
                try:
                    res = pricelist._compute_price_rule([(product, 1.0, partner)])
                    price = res.get(product.id, (product.list_price, False))[0]
                except Exception:
                    price = product.list_price
        return price

    @api.onchange("barcode", "pricelist_id", "partner_id")
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
            wiz.price = wiz._compute_price(product, wiz.partner_id, wiz.pricelist_id)

    def action_new_scan(self):
        self.update({
            "barcode": False,
            "product_id": False,
            "product_name": False,
            "uom_name": False,
            "list_price": 0.0,
            "price": 0.0,
        })
