/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillUnmount } from "@odoo/owl";
export class PpdbReloader extends Component {
    setup() {
        this.bus = this.env.services.bus_service;
        this.action = this.env.services.action;
        try {
            this.bus.addChannel("pos_packaged_board");
            if (this.bus.start) { this.bus.start(); }
        } catch (e) {}
        this._onNotif = (ev) => {
            try {
                const notifs = (ev && ev.detail) || [];
                for (const n of notifs) {
                    const channel = n.channel || (Array.isArray(n.type) ? n.type[1] : n.type);
                    if (channel === "pos_packaged_board") {
                        const current = this.env.services.action.currentController;
                        if (current && current.model === "pos.packaged.card") {
                            this.action.doAction({ type: "ir.actions.client", tag: "reload" });
                        }
                        break;
                    }
                }
            } catch (e) {}
        };
        try { this.bus.addEventListener("notification", this._onNotif); } catch (e) {}
        onWillUnmount(() => { try { this.bus.removeEventListener("notification", this._onNotif);} catch(e){} });
    }
}
PpdbReloader.template = "pos_packaged_delivery_board.Reloader";
registry.category("main_components").add("pos_packaged_board_reloader", { Component: PpdbReloader });
