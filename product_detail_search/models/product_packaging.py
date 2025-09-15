from odoo import models, fields

class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    uom_id = fields.Many2one(
        "uom.uom",
        string="UoM for POS UoM Price",
        help="عند مسح باركود هذا التغليف في الـ POS، استخدم هذه الوحدة وسعرها (من جدول UoM Price).",
    )
