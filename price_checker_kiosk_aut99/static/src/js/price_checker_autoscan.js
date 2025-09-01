/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, "price_checker_kiosk_autoscan_fix3.autoscan", {
    mounted() {
        this._super(...arguments);
        this._pc_bindAutoscan();
    },
    updated() {
        this._super(...arguments);
        this._pc_bindAutoscan();
    },
    _pc_bindAutoscan() {
        try {
            // Only for our wizard
            const isPriceChecker = this.props && this.props.resModel === "price.checker.wizard";
            if (!isPriceChecker) return;
            const input = this.el && this.el.querySelector("input[name='barcode']");
            if (!input) return;
            if (!input.dataset.pcBound) {
                input.dataset.pcBound = "1";
                input.focus();
                if (input.select) input.select();
                // Fire onchange instantly on any input (scanner keystrokes)
                input.addEventListener("input", () => {
                    try { this.model.notifyFieldChange("barcode"); } catch (e) {}
                });
                input.addEventListener("change", () => {
                    try {
                        this.model.notifyFieldChange("barcode");
                    } catch (e) {
                        // ignore
                    }
                });
                input.addEventListener("keydown", (ev) => {
                    if (ev.key === "Enter") {
                        try { this.model.notifyFieldChange("barcode"); } catch (e) {}
                        ev.preventDefault();
                        ev.stopPropagation();
                    }
                });
            }
        } catch (e) {
            // no-op
        }
    },
});
