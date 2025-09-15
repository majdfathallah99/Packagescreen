from odoo import api, models
from odoo.tools import float_round

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, raw_code):
        """
        عند مسح باركود:
        - لو كان باركود تغليف: package_price = سعر الـ UoM المطابق للتغليف.
        - لو كان باركود منتج: أيضاً نحسب package_price باختيار تغليف/UoM افتراضي للعرض في بطاقة "عبوة".
        أولوية جلب سعر UoM: model 'product.multi.uom.price' (variant) ثم 'product.tmpl.multi.uom.price' (template).
        """

        # ---------------- helpers ----------------
        def _normalize(code):
            if not code:
                return ""
            trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
            return code.translate(trans).strip()

        def _find_product_by_barcode(code):
            Product = self.env["product.product"]
            p = Product.search([("barcode", "=", code)], limit=1)
            if p:
                return p
            tmpl = self.search([("barcode", "=", code)], limit=1)
            if tmpl:
                return tmpl.product_variant_id or tmpl.product_variant_ids[:1]
            return False

        def _find_packaging_by_barcode(code):
            return self.env["product.packaging"].search([("barcode", "=", code)], limit=1)

        def _uom_from_packaging(packaging, product):
            """
            الأفضل: حقل packaging.uom_id (الذي أضفناه).
            لو مش موجود: محاولة مطابقة اسم التغليف مع UoM داخل نفس الفئة.
            """
            if getattr(packaging, "uom_id", False):
                return packaging.uom_id
            UoM = self.env["uom.uom"]
            name = (packaging.name or "").strip()
            if not name:
                return False
            cat = product.uom_id.category_id.id if product.uom_id else False
            domain = [("name", "=ilike", name)]
            if cat:
                domain.append(("category_id", "=", cat))
            return UoM.search(domain, limit=1)

        def _get_uom_price(product, uom):
            """سعر الـ UoM من الموديلين (variant ثم template) إن وُجدا."""
            # variant-level
            try:
                VariantPrice = self.env["product.multi.uom.price"]
                vp = VariantPrice.search(
                    [("product_id", "=", product.id), ("uom_id", "=", uom.id)],
                    limit=1,
                )
                if vp:
                    return vp.price
            except Exception:
                pass
            # template-level
            try:
                TmplPrice = self.env["product.tmpl.multi.uom.price"]
                tp = TmplPrice.search(
                    [("product_tmpl_id", "=", product.product_tmpl_id.id), ("uom_id", "=", uom.id)],
                    limit=1,
                )
                if tp:
                    return tp.price
            except Exception:
                pass
            return None

        def _pick_default_packaging(product):
            """
            نختار تغليفًا افتراضيًا للعرض إذا مسحنا باركود المنتج:
            - يفضَّل أول تغليف عنده uom_id مضبوط.
            - وإلا أي تغليف موجود.
            """
            packs = product.product_tmpl_id.packaging_ids
            if not packs:
                return False
            with_uom = packs.filtered(lambda p: getattr(p, "uom_id", False))
            return with_uom[:1] or packs[:1]

        def _compute_package_info_for_product(product, forced_packaging=False):
            """
            يعيد (package_qty, package_price) للبطاقة "عبوة"
            سواء كان المسح للتغليف أو للمنتج.
            """
            packaging = forced_packaging or _pick_default_packaging(product)
            if not packaging:
                # لا يوجد تغليف، نحاول fallback على أول UoM سعر لهذا المنتج للعرض فقط
                uom_price = None
                uom_name = None
                try:
                    VariantPrice = self.env["product.multi.uom.price"]
                    row = VariantPrice.search([("product_id", "=", product.id)], limit=1)
                    if row:
                        uom_price = row.price
                        uom_name = row.uom_id.display_name
                except Exception:
                    try:
                        TmplPrice = self.env["product.tmpl.multi.uom.price"]
                        row = TmplPrice.search(
                            [("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1
                        )
                        if row:
                            uom_price = row.price
                            uom_name = row.uom_id.display_name
                    except Exception:
                        pass
                if uom_price is None:
                    return 1.0, None  # ما نعرضش سعر "عبوة"
                # نعرض السعر كما هو، والكمية 1 بشكل شكلي (ما في تغليف)
                price = float_round(uom_price, precision_rounding=product.currency_id.rounding)
                return 1.0, price

            # لدينا تغليف: نحسب السعر من UoM المرتبط
            uom = _uom_from_packaging(packaging, product)
            if not uom:
                return packaging.qty or 1.0, None
            price = _get_uom_price(product, uom)
            if price is None:
                return packaging.qty or 1.0, None
            price = float_round(price, precision_rounding=product.currency_id.rounding)
            return (packaging.qty or 1.0), price

        # ---------------- main ----------------
        code = _normalize(raw_code)
        if not code:
            return False

        Product = self.env["product.product"]
        company = self.env.company

        product = _find_product_by_barcode(code)
        packaging = False

        if not product:
            # احتمال يكون باركود تغليف
            packaging = _find_packaging_by_barcode(code)
            if packaging:
                product = Product.browse(packaging.product_id.id)

        if not product:
            return False

        # سعر القطعة = سعر البيع العادي
        list_price = product.lst_price

        # احسب بيانات "عبوة" في كل الحالات:
        if packaging:
            package_qty, package_price = _compute_package_info_for_product(product, forced_packaging=packaging)
        else:
            package_qty, package_price = _compute_package_info_for_product(product)

        # (اختياري) قائمة أسعار UoM للعرض
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

        res = {
            "id": product.id,
            "display_name": product.display_name,
            "barcode": product.barcode or "",
            "default_code": product.default_code or "",
            # بطاقة "قطعة" — هذا هو الذي تريده:
            "list_price": list_price,
            # بطاقة "عبوة" — الآن تُملأ حتى مع باركود المنتج:
            "package_qty": package_qty,
            "package_price": package_price,
            # معلومات إضافية للواجهة إن احتجتها
            "uom_prices": uom_prices,
            "category": product.categ_id.display_name if product.categ_id else "",
            "qty_available": product.qty_available,
            "company_id": [company.id, company.name],
            "type": product.type or "",
            "specification": product.description_sale or "",
            "tax_amount": "",
        }
        return [res]
