# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _

DEFAULT_WINDOW_DAYS = 90

class PosPackagedCard(models.Model):
    _name = "pos.packaged.card"
    _description = "Card: POS packaged product to hand to customer"
    _order = "id desc"
    _rec_name = "product_id"

    _sql_constraints = [
        ("uniq_line", "unique(pos_order_line_id)", "This POS line is already on the board."),
    ]

    # Links
    pos_order_line_id = fields.Many2one("pos.order.line", string="POS Line", required=True, ondelete="cascade", index=True)
    order_id = fields.Many2one("pos.order", string="POS Order", index=True)

    # Product / quantities
    product_id = fields.Many2one("product.product", string="Product", required=True, index=True)
    product_tmpl_id = fields.Many2one(related="product_id.product_tmpl_id", comodel_name="product.template", store=False, readonly=True)
    default_uom_id = fields.Many2one("uom.uom", string="Default UoM", required=True)
    used_uom_id = fields.Many2one("uom.uom", string="Used UoM (POS)", required=True, index=True)
    qty = fields.Float(string="Qty", digits="Product Unit of Measure", required=True, default=0.0)

    date_order = fields.Datetime(string="Sale Date", index=True)
    order_name = fields.Char(string="Order Name")

    state = fields.Selection([("new", "New Orders"), ("confirmed", "Confirmed Orders"), ("done", "Done")], default="new", index=True, required=True)
    note = fields.Char(string="Note")

    # --- Images ---
    image_128_product = fields.Image(related="product_id.image_128", readonly=True, store=False)
    image_128_template = fields.Image(related="product_tmpl_id.image_128", readonly=True, store=False)

    # Data URI for absolute fallback (used only if needed)
    image_data_uri = fields.Char(string="Image Data URI", compute="_compute_image_data_uri", store=False)

    @api.depends("image_128_product", "image_128_template")
    def _compute_image_data_uri(self):
        for rec in self:
            img = rec.image_128_product or rec.image_128_template
            if img:
                rec.image_data_uri = "data:image/png;base64," + (img.decode() if isinstance(img, bytes) else img)
            else:
                rec.image_data_uri = False

    # --- Actions ---
    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_reset(self):
        self.write({"state": "new"})
        return True

    @api.model
    def action_move_confirmed_to_done(self):
        """Move all cards in Confirmed to Done, then reload the view."""
        recs = self.search([("state", "=", "confirmed")])
        if recs:
            recs.write({"state": "done"})
        return {"type": "ir.actions.client", "tag": "reload"}

    # --- Sync helpers ---
    @api.model
    def _sync_window_start(self):
        days = self.env.context.get("ppdb_days", DEFAULT_WINDOW_DAYS)
        return fields.Datetime.now() - timedelta(days=days)

    @api.model
    def create_from_pos_lines(self, date_from=False, states=("paid",)):
        POL = self.env["pos.order.line"].sudo()
        domain = [("qty","!=",0)]
        if date_from:
            orders = self.env["pos.order"].sudo().search([("date_order", ">=", date_from)])
            if orders:
                domain.append(("order_id","in", orders.ids))
            else:
                return self.browse()
        if states:
            domain.append(("order_id.state","in", list(states)))

        uom_field = "uom_id" if "uom_id" in POL._fields else "product_uom_id"
        domain.append((uom_field, "!=", False))

        lines = POL.search(domain, order="id desc", limit=5000)
        created = self.browse()
        for line in lines:
            used_uom = getattr(line, uom_field)
            default_uom = line.product_id.product_tmpl_id.uom_id
            if not used_uom or used_uom.id == default_uom.id or not line.qty:
                continue
            vals = {
                "pos_order_line_id": line.id,
                "product_id": line.product_id.id,
                "default_uom_id": default_uom.id,
                "used_uom_id": used_uom.id,
                "qty": line.qty,
                "order_id": line.order_id.id,
                "date_order": line.order_id.date_order,
                "order_name": line.order_id.name,
                "state": "new",
            }
            try:
                created |= self.create(vals)
            except Exception:
                # uniqueness constraint prevents duplicates
                pass
        return created

    @api.model
    def create_from_one_order(self, order):
        self = self.sudo()
        POL = self.env["pos.order.line"].sudo()
        uom_field = "uom_id" if "uom_id" in POL._fields else "product_uom_id"
        created = self.browse()
        for line in order.lines:
            used_uom = getattr(line, uom_field, False)
            default_uom = line.product_id.product_tmpl_id.uom_id
            if not used_uom or used_uom.id == default_uom.id or not line.qty:
                continue
            vals = {
                "pos_order_line_id": line.id,
                "product_id": line.product_id.id,
                "default_uom_id": default_uom.id,
                "used_uom_id": used_uom.id,
                "qty": line.qty,
                "order_id": order.id,
                "date_order": order.date_order,
                "order_name": order.name,
                "state": "new",
            }
            try:
                created |= self.create(vals)
            except Exception:
                pass
        return created

    @api.model
    def action_refresh_board(self):
        self.create_from_pos_lines(self._sync_window_start(), ("paid",))
        return {
            "type": "ir.actions.act_window",
            "name": _("POS Packaged Delivery Board"),
            "res_model": "pos.packaged.card",
            "view_mode": "kanban,list,form,search",
            "target": "current",
        }

