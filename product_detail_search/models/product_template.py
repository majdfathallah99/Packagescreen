from odoo import api, models
from odoo.tools import float_round

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def product_detail_search(self, raw_code):
        """
        لو الباركود تابع لتغليف، نخلي الـ package_price = سعر الـ UoM القادم من pos_multi_uom_price
        (أولوية: مستوى الـ variant ثم مستوى الـ template).
        """
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

        def _map_packaging_to_uom(packaging, product):
            """مطابقة بالاسم داخل نفس فئة الـ UoM (بدون تعديل الموديل)."""
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

        code = _normalize(raw_code)
        if not code:
            return False

        Product = self.env["product.product"]
        company = self.env.company

        product = _find_product_by_barcode(code)
        packaging = False
        package_qty = 1.0
        package_price = None

        if not product:
            packaging = _find_packaging_by_barcode(code)
            if packaging:
                product = Product.browse(packaging.product_id.id)
                package_qty = packaging.qty or 1.0

        if not product:
            return False

        list_price = product.lst_price

        # لو تغليف: نحاول نجيب سعر الـ UoM ونحطه مكان package_price
        if packaging:
            uom = _map_packaging_to_uom(packaging, product)
            if uom:
                uom_price = _get_uom_price(product, uom)
                if uom_price is not None:
                    package_price = float_round(
                        uom_price, precision_rounding=product.currency_id.rounding
                    )
                else:
                    # ما في سعر UoM؟ خليها ترجع لسعر المنتج الأساسي
                    package_price = float_round(
                        list_price, precision_rounding=product.currency_id.rounding
                    )

        # (اختياري) نرسل لواجهة البحث قائمة أسعار الـ UoM للعرض فقط
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
            "list_price": list_price,

            "package_qty": package_qty,
            "package_price": package_price,  # ← هنا صار سعر الـ UoM

            "uom_prices": uom_prices,
            "category": product.categ_id.display_name if product.categ_id else "",
            "qty_available": product.qty_available,
            "company_id": [company.id, company.name],
            "type": product.type or "",
            "specification": product.description_sale or "",
            "tax_amount": "",
        }
        return [res]
