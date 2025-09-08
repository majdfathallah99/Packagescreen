# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models,_


class ProductTemplate(models.Model):
    """Inheriting The product template for adding the product_detail_search
    method"""
    _inherit = 'product.template'

    def get_selection_label(self, object, field_name, field_value):
        return _(dict(
            self.env[object].fields_get(allfields=[field_name])[field_name][
                'selection'])[field_value])

    def product_detail_search(self, barcode):
    """Find by barcode and return ONLY: name, uom, price, package qty, package price."""
    product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
    if not product:
        return False

    # Unit data
    uom_name = product.uom_id.name or ""
    unit_price = product.list_price or 0.0  # sales price
    currency = product.currency_id

    # Choose a packaging: prefer default, else first with qty>1, else first available
    packaging = product.packaging_ids.filtered(lambda p: getattr(p, "is_default", False))[:1]
    if not packaging:
        packaging = product.packaging_ids.filtered(lambda p: (p.qty or 0) > 1)[:1]
    if not packaging and product.packaging_ids:
        packaging = product.packaging_ids[:1]
    packaging = packaging and packaging[0] or False

    package_qty = int(packaging.qty) if (packaging and packaging.qty) else 0
    package_price = (unit_price * package_qty) if package_qty else 0.0

    return [{
        'id': product.id,
        'name': product.display_name,
        'uom': uom_name,
        'price': unit_price,
        'package_qty': package_qty,       # e.g. 10
        'package_price': package_price,   # e.g. 100 (= price * qty)
        'currency_symbol': currency.symbol or '',
    }]
