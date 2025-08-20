# -*- coding: utf-8 -*-
from odoo import models

class PosOrder(models.Model):
    _inherit = "pos.order"

    def action_pos_order_paid(self):
        # run original
        res = super().action_pos_order_paid()
        # create cards immediately
        self.sudo().env["pos.packaged.card"].create_from_one_order(self)
        # notify UI (best-effort)
        try:
            bus = self.env["bus.bus"].sudo()
            if hasattr(bus, "sendone"):
                bus.sendone("pos_packaged_board", {"event": "refresh"})
            else:
                # fallback older internals
                bus._sendone("pos_packaged_board", {"event": "refresh"})
        except Exception:
            pass
        return res
