/** @odoo-module **/
// Safe hybrid: auto-reload the POS Packaged Delivery Board when
// a push notification arrives OR every 10s as a fallback.
import { registry } from "@web/core/registry";
import { Component, onWillUnmount } from "@odoo/owl";

const FALLBACK_MS = 10000; // 10 seconds

export class PpdbAutoRefresh extends Component {
    setup() {
        this.action = this.env.services.action;
        this.bus = this.env.services.bus_service;
        this._interval = null;

        // Fallback timer
        this._interval = setInterval(() => this._maybeReload(), FALLBACK_MS);

        // Push via bus (best-effort, fully guarded)
        try {
            this.bus.addChannel("pos_packaged_board");
            if (this.bus.start) { this.bus.start(); }
            this._onNotif = (ev) => {
                try {
                    const notifs = (ev && ev.detail) || [];
                    for (const n of notifs) {
                        const channel = n.channel || (Array.isArray(n.type) ? n.type[1] : n.type);
                        if (channel === "pos_packaged_board") {
                            this._maybeReload();
                            break;
                        }
                    }
                } catch (e) {}
            };
            this.bus.addEventListener("notification", this._onNotif);
        } catch (e) {}

        onWillUnmount(() => {
            try { if (this._interval) clearInterval(this._interval); } catch(e){}
            try { if (this._onNotif) this.bus.removeEventListener("notification", this._onNotif); } catch(e){}
        });
    }

    _maybeReload() {
        try {
            const current = this.action.currentController;
            if (current && current.model === "pos.packaged.card") {
                const hasModal = document.querySelector(".modal, .o_modal, .o_dialog");
                if (!hasModal) {
                    this.action.doAction({ type: "ir.actions.client", tag: "reload" });
                }
            }
        } catch (e) {}
    }
}
PpdbAutoRefresh.template = "pos_packaged_delivery_board.AutoRefreshMount";
registry.category("main_components").add("ppdb_auto_refresh_mount", { Component: PpdbAutoRefresh });
