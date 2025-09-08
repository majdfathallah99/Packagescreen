/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onMounted, onWillUpdateProps } from "@odoo/owl";

patch(FormController.prototype, "price_check_kiosk_autofocus", {
    setup() {
        this._super(...arguments);
        const focusBarcode = () => {
            const el = this.root.el?.querySelector('input[name="barcode"]');
            if (el) {
                el.focus();
                el.select?.();
            }
        };
        onMounted(() => {
            document.querySelector(".modal-dialog")?.classList.add("modal-fullscreen");
            document.querySelector(".o_dialog")?.classList.add("modal-fullscreen");
            focusBarcode();
        });
        onWillUpdateProps(focusBarcode);
        this.focusBarcode = focusBarcode;
    },

    async saveButtonClicked(ev) {
        ev?.preventDefault?.();
    },
});

document.addEventListener("keydown", (ev) => {
    const active = document.activeElement;
    if (active && active.getAttribute("name") === "barcode" && ev.key === "Enter") {
        ev.preventDefault();
        ev.stopPropagation();
        active.dispatchEvent(new Event("change", { bubbles: true }));
        active.blur();
        setTimeout(() => active.focus(), 100);
    }
});
