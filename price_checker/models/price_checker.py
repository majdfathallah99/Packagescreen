# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PriceCheckerWizard(models.TransientModel):
    _name = "price.checker.wizard"
    _description = "Price Checker Wizard"
    barcode = fields.Char(string="Scan/Type Barcode")
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
        product = self.env["product.product"].search([("barcode","=",self.barcode)], limit=1)
        if not product:
            self.product_name = _("No product found")
            return
        self.product_id = product.id
        self.product_name = product.display_name
        self.uom_name = product.uom_id.display_name
        self.list_price = product.list_price
        price = self.list_price
        if self.pricelist_id:
            try:
                price = self.pricelist_id._get_product_price(product, 1.0, self.partner_id)
            except Exception:
                pass
        self.price = price

    def action_new_scan(self):
        self.barcode = False
        self.product_id = False
        self.product_name = False
        self.uom_name = False
        self.list_price = 0.0
        self.price = 0.0
