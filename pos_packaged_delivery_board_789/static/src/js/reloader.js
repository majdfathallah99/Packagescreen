/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class PpdbReloader extends Component {
    setup() {
        this.bus = useService("bus_service");
        this.action = useService("action");
        // subscribe to our channel
        this.bus.addChannel("pos_packaged_board");
        useBus(this.bus, "notification", (payload) => {
            const notifs = payload.detail || [];
            for (const n of notifs) {
                const channel = n.channel || n.type; // version tolerance
                if (channel === "pos_packaged_board") {
                    // Only reload if we're currently on our board model to avoid disrupting other pages
                    const current = this.env.services.action.currentController;
                    if (current && current.model === "pos.packaged.card") {
                        this.action.doAction({type: "ir.actions.client", tag: "reload"});
                    }
                    break;
                }
            }
        });
    }
}
PpdbReloader.template = "pos_packaged_delivery_board.Reloader";

// Mount globally so it's always listening
registry.category("main_components").add("pos_packaged_board_reloader", {
    Component: PpdbReloader,
});
