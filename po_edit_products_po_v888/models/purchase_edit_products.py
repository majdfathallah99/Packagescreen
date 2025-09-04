# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PoEditProductsWizard(models.TransientModel):
    _name = "po.edit.products.wizard"
    _description = "Edit Products from Purchase Order"

    purchase_id = fields.Many2one("purchase.order", string="Purchase Order", required=True)
    line_ids = fields.One2many("po.edit.products.wizard.line", "wizard_id", string="Lines")
    pkg_line_ids = fields.One2many("po.edit.products.wizard.pkg.line", "wizard_id", string="Packaging Lines")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        purchase = self.env["purchase.order"].browse(self.env.context.get("active_id"))
        if purchase:
            res["purchase_id"] = purchase.id
            product_ids = purchase.order_line.mapped("product_id").ids

            # product lines
            lines = []
            for prod in self.env["product.product"].browse(product_ids):
                lines.append((0,0,{
                    "product_id": prod.id,
                    "uom_id": prod.uom_id.id,
                }))
            res["line_ids"] = lines

            # packaging lines
            pkg_lines = []
            for pkg in self.env["product.packaging"].search([("product_id","in",product_ids)]):
                pkg_lines.append((0,0,{"packaging_id": pkg.id}))
            res["pkg_line_ids"] = pkg_lines
        return res

    def action_apply(self):
        return {"type": "ir.actions.act_window_close"}


class PoEditProductsWizardLine(models.TransientModel):
    _name = "po.edit.products.wizard.line"
    _description = "Edit Product Line"

    wizard_id = fields.Many2one("po.edit.products.wizard", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Product", required=False)

    sale_price = fields.Float(
        string="Sales Price",
        related="product_id.product_tmpl_id.list_price",
        readonly=False,
        digits="Product Price",
    )
    cost_price = fields.Float(
        string="Cost",
        related="product_id.product_tmpl_id.standard_price",
        readonly=False,
        digits="Product Price",
    )
    
# في PoEditProductsWizardLine
    
    uom_id = fields.Many2one(
        "uom.uom",
        string="UoM",
        required=True,
        # domain="[...]"  <-- قم بحذف هذا السطر أو التعليق عليه
    )
    

    price_in_uom = fields.Float(
        string="Price in UoM",
        compute="_compute_price_in_uom",
        inverse="_inverse_price_in_uom",
        store=False,
        digits="Product Price",
        help="Edit the price for the selected UoM; it will update the product Sales Price in the product's base UoM."
    )

    @api.depends('sale_price','uom_id','product_id')
    def _compute_price_in_uom(self):
        for rec in self:
            price = rec.sale_price or 0.0
            if rec.product_id and rec.uom_id:
                base_uom = rec.product_id.uom_id
                rec.price_in_uom = base_uom._compute_price(price, rec.uom_id)
            else:
                rec.price_in_uom = price

    def _inverse_price_in_uom(self):
        for rec in self:
            if rec.product_id and rec.uom_id:
                base_uom = rec.product_id.uom_id
                rec.sale_price = rec.uom_id._compute_price(rec.price_in_uom or 0.0, base_uom)
    @api.model_create_multi
    def create(self, vals_list):
        # Skip lines without a product (empty draft line created by editable list)
        clean = [vals for vals in vals_list if vals.get('product_id')]
        if not clean:
            return self.browse()
        return super().create(clean)


    @api.onchange('product_id')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # إذا لم يتم تحديد منتج، قم بإعادة تعيين كل شيء بصمت
        if not self.product_id:
            self.uom_id = False
            return {'domain': {'uom_id': []}}
    
        # -- التحقق ورسالة التحذير --
        # إذا كان المنتج المحدد ليس له وحدة قياس أساسية
        if not self.product_id.uom_id:
            # قم بإفراغ وحدة القياس
            self.uom_id = False
            
            # قم بإعداد رسالة التحذير
            warning_msg = {
                'title': _('Missing Configuration!'),
                'message': _('The selected product "%s" does not have a default Unit of Measure. Please configure it first.') % (self.product_id.display_name),
            }
            
            # أعد النطاق الفارغ مع رسالة التحذير
            return {
                'domain': {'uom_id': []},
                'warning': warning_msg
            }
        # -- نهاية التحقق --
    
        # إذا كان كل شيء على ما يرام، قم بتعيين وحدة القياس والنطاق كالمعتاد
        self.uom_id = self.product_id.uom_id
        domain = [('category_id', '=', self.product_id.uom_id.category_id.id)]
        return {'domain': {'uom_id': domain}}

    def _onchange_uom_id_validate(self):
        for rec in self:
            if rec.product_id and rec.uom_id and rec.uom_id.category_id != rec.product_id.uom_id.category_id:
                rec.uom_id = rec.product_id.uom_id
                return {
                    'warning': {
                        'title': _('Invalid UoM'),
                        'message': _('Please select a UoM in the same category as the product.'),
                    },
                    'domain': {'uom_id': [('category_id', '=', rec.product_id.uom_id.category_id.id)]},
                }
        return {}



class PoEditProductsWizardPkgLine(models.TransientModel):
    _name = "po.edit.products.wizard.pkg.line"
    _description = "Edit Packaging Prices"

    wizard_id = fields.Many2one("po.edit.products.wizard", required=True, ondelete="cascade")
    packaging_id = fields.Many2one("product.packaging", string="Packaging", required=True)
    product_id = fields.Many2one("product.product", related="packaging_id.product_id", store=False, readonly=True)
    name = fields.Char(related="packaging_id.name", string="Name", readonly=True)
    qty = fields.Float(related="packaging_id.qty", string="Qty in Package", readonly=True, digits="Product Unit of Measure")
    pkg_uom_id = fields.Many2one(related="packaging_id.product_uom_id", comodel_name="uom.uom", string="Package UoM", readonly=True)
    package_price = fields.Float(string="Package Price", related="packaging_id.list_price", readonly=False, digits="Product Price")
    unit_price_from_package = fields.Float(string="Unit Price (from package)", compute="_compute_unit_price_from_package", digits="Product Price")

    @api.depends('package_price', 'qty', 'pkg_uom_id', 'product_id')
    def _compute_unit_price_from_package(self):
        for rec in self:
            price = rec.package_price or 0.0
            qty = rec.qty or 1.0
            if not rec.product_id:
                rec.unit_price_from_package = 0.0
                continue
            base_uom = rec.product_id.uom_id
            pkg_uom = rec.pkg_uom_id or base_uom
            qty_in_base = pkg_uom._compute_quantity(qty, base_uom, rounding_method='HALF-UP') if pkg_uom and base_uom else qty
            rec.unit_price_from_package = price / qty_in_base if qty_in_base else 0.0
    @api.model_create_multi
    def create(self, vals_list):
        clean = [vals for vals in vals_list if vals.get('packaging_id')]
        if not clean:
            return self.browse()
        return super().create(clean)



class ProductPackaging(models.Model):
    _inherit = "product.packaging"
    list_price = fields.Float(string="Packaging Price", digits="Product Price",
                              help="Sales price of the whole package (e.g., price for a box).")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_edit_order_products(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Edit Products"),
            "res_model": "po.edit.products.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id},
        }
