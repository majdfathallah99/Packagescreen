/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onMounted, onPatched } from "@odoo/owl";

patch(FormController.prototype, "price_check_kiosk_autofocus", {
    setup() {
        this._super(...arguments);

        const toFullscreen = () => {
            document.querySelector(".modal-dialog")?.classList.add("modal-fullscreen");
            document.querySelector(".o_dialog")?.classList.add("modal-fullscreen");
        };

        const focusBarcode = () => {
            const root = this?.root?.el;
            if (!root) return;
            const el = root.querySelector('input[name="barcode"]');
            if (el) {
                el.focus();
                el.select?.();
            }
        };

        onMounted(() => {
            toFullscreen();
            focusBarcode();
        });
        onPatched(() => {
            toFullscreen();
            focusBarcode();
        });
    },

    async saveButtonClicked(ev) {
        ev?.preventDefault?.(); // don’t close the kiosk
    },
});

// Enter triggers onchange without clicking elsewhere
document.addEventListener("keydown", (ev) => {
    const a = document.activeElement;
    if (a && a.getAttribute("name") === "barcode" && ev.key === "Enter") {
        ev.preventDefault();
        ev.stopPropagation();
        a.dispatchEvent(new Event("change", { bubbles: true }));
        a.blur();
        setTimeout(() => a.focus(), 80);
    }
});
