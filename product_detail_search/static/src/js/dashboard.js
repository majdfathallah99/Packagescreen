/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this._t = _t; // expose to template

        this.state = useState({ barcode: "", details: null });

        this._debounceTimer = null;
        this._DEBOUNCE_MS = 250;   // wait for scanner to finish
        this._MIN_LEN = 6;         // ignore very short codes
        this._mounted = false;

        onMounted(() => {
            this._mounted = true;
            setTimeout(() => this.focusInput(), 0);
        });
        onWillUnmount(() => {
            this._mounted = false;
            if (this._debounceTimer) clearTimeout(this._debounceTimer);
        });
    }

    focusInput() {
        if (!this._mounted) return;
        const el = (this.refs && this.refs.scanInput)
            ? this.refs.scanInput
            : (this.el && this.el.querySelector && this.el.querySelector(".scan-input"));
        if (el) {
            el.focus();
            if (el.select) el.select();
        }
    }

    onKeyDown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            const code = (this.state.barcode || "").trim();
            this._commitScan(code);
        }
    }

    onInput(ev) {
        this.state.barcode = ev.target.value;
        if (this._debounceTimer) clearTimeout(this._debounceTimer);
        this._debounceTimer = setTimeout(() => {
            const code = (this.state.barcode || "").trim();
            if (code && code.length >= this._MIN_LEN) {
                this._commitScan(code);
            }
        }, this._DEBOUNCE_MS);
    }

    async _commitScan(barcode) {
        if (!barcode) return;
        try {
            const res = await this.orm.call("product.template", "product_detail_search", [[], barcode]);
            const details = (res && res.length) ? res[0] : null;
            this.state.details = details;

            if (!details) {
                this.notification.add(this._t("Product not found."), { type: "warning" });
            }
        } catch {
            this.notification.add(this._t("Error fetching product."), { type: "danger" });
            this.state.details = null;
        } finally {
            this.state.barcode = "";
            setTimeout(() => this.focusInput(), 0);
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
