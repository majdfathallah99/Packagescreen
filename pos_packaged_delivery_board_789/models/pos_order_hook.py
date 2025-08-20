# -*- coding: utf-8 -*-
from odoo import models

class PosOrder(models.Model):
    _inherit = "pos.order"

    def action_pos_order_paid(self):
        # call original logic
        res = super().action_pos_order_paid()
        # create cards immediately
        created = self.sudo().env["pos.packaged.card"].create_from_one_order(self)
        # ping UI to auto-reload (tiny message; no data leak)
        try:
            bus = self.env["bus.bus"].sudo()
            if hasattr(bus, "sendone"):
                bus.sendone("pos_packaged_board", {"event": "refresh"})
            else:
                bus._sendone("pos_packaged_board", {"event": "refresh"})
        except Exception:
            # never block POS in case bus is unavailable
            pass
        return res
