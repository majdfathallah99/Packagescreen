from odoo import api, models
from odoo.tools import float_round

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, raw_code):
        """
        لا نستخدم التغليف إطلاقاً.
        - 'piece_price' / 'list_price'  = سعر البيع للقطعة.
        - 'uom_price'  / 'pack_price'   = سعر الـ UoM (أول سطر موجود للمنتج؛ variant أولاً ثم template).
        - نرجّع أيضاً 'uom_id' و 'uom_name' للعرض.
        """

        # -------- helpers --------
        def _normalize(code):
            if not code:
                return ""
            trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
            return code.translate(trans).strip()

        def _find_product_by_barcode(code):
            Product = self.env["product.product"]
            # باركود المتغيّر
            p = Product.search([("barcode", "=", code)], limit=1)
            if p:
                return p
            # باركود التيمبلِت
            tmpl = self.search([("barcode", "=", code)], limit=1)
            if tmpl:
                return tmpl.product_variant_id or tmpl.product_variant_ids[:1]
            return False

        def _get_first_uom_price(product):
            """
            يرجّع tuple: (uom, price) من جداول أسعار UoM
            أولوية: مستوى الـ variant ثم مستوى الـ template.
            لو أكثر من سطر، نأخذ أول نتيجة (يمكن تخصيص الاختيار لاحقًا).
            """
            # 1) على مستوى الـ variant
            try:
                VariantPrice = self.env["product.multi.uom.price"]
                vp = VariantPrice.search([("product_id", "=", product.id)], limit=1)
                if vp:
                    return vp.uom_id, vp.price
            except Exception:
                pass
            # 2) على مستوى الـ template
            try:
                TmplPrice = self.env["product.tmpl.multi.uom.price"]
                tp = TmplPrice.search(
                    [("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1
                )
                if tp:
                    return tp.uom_id, tp.price
            except Exception:
                pass
            return None, None

        # -------- main --------
        code = _normalize(raw_code)
        if not code:
            return False

        Product = self.env["product.product"]
        company = self.env.company

        product = _find_product_by_barcode(code)
        if not product:
            return False

        # سعر القطعة
        list_price = product.lst_price

        # سعر الـ UoM (بدون تغليف)
        uom, uom_price = _get_first_uom_price(product)
        if uom_price is not None:
            uom_price = float_round(uom_price, precision_rounding=product.currency_id.rounding)

        # (اختياري) نرسل كل أسعار الـ UoM للعرض في الواجهة لو احتجتها
        uom_prices = []
        try:
            VariantPrice = self.env["product.multi.uom.price"]
            for row in VariantPrice.search([("product_id", "=", product.id)]):
                uom_prices.append({
                    "uom_id": row.uom_id.id,
                    "uom_name": row.uom_id.display_name,
                    "price": row.price,
                })
        except Exception:
            try:
                TmplPrice = self.env["product.tmpl.multi.uom.price"]
                for row in TmplPrice.search([("product_tmpl_id", "=", product.product_tmpl_id.id)]):
                    uom_prices.append({
                        "uom_id": row.uom_id.id,
                        "uom_name": row.uom_id.display_name,
                        "price": row.price,
                    })
            except Exception:
                pass

        # نرجّع مفاتيح واضحة + aliases علشان الـ JS يلقط أي تسمية:
        res = {
            "id": product.id,
            "display_name": product.display_name,
            "barcode": product.barcode or "",
            "default_code": product.default_code or "",

            # بطاقة "قطعة"
            "list_price": list_price,
            "piece_price": list_price,     # alias

            # بطاقة "عبوة" (هنا المقصود UoM)
            "uom_id": uom.id if uom else False,
            "uom_name": uom.display_name if uom else "",
            "uom_price": uom_price,        # التسمية الأساسية
            "pack_price": uom_price,       # alias للواجهة الحالية
            "pack_qty": 1.0,               # ثابت لعرض "×" إن كان لازم

            # إضافيات
            "uom_prices": uom_prices,
            "category": product.categ_id.display_name if product.categ_id else "",
            "qty_available": product.qty_available,
            "company_id": [company.id, company.name],
            "type": product.type or "",
            "specification": product.description_sale or "",
            "tax_amount": "",
        }
        return [res]
