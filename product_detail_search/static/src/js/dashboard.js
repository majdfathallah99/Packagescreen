/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ barcode: "", details: null, history: [] });

        this._debounceTimer = null;
        this._DEBOUNCE_MS = 250;   // pause between keystrokes before we treat it as a finished scan
        this._MIN_LEN = 6;         // ignore very short inputs to reduce false calls
        this._mounted = false;

        onMounted(() => {
            this._mounted = true;
            this.focusInput();
        });
        onWillUnmount(() => {
            this._mounted = false;
            if (this._debounceTimer) clearTimeout(this._debounceTimer);
        });
    }

    focusInput() {
        if (!this._mounted) return;
        const el = this.refs.scanInput;
        if (el) {
            el.focus();
            el.select();
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
                this.notification.add(_t("Product not found."), { type: "warning" });
            } else {
                // add to history (keep latest 20)
                this.state.history.unshift({
                    ts: Date.now(),
                    name: details.name,
                    barcode: barcode,
                    price: details.price ?? details.list_price,
                    uom: details.uom,
                    symbol: details.symbol || details.currency_symbol || "",
                });
                if (this.state.history.length > 20) this.state.history.pop();
            }
        } catch (e) {
            this.notification.add(_t("Error fetching product."), { type: "danger" });
            this.state.details = null;
        } finally {
            // prepare for next scan: clear & refocus (so user never has to delete)
            this.state.barcode = "";
            this.focusInput();
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add(
    "product_detail_search_barcode_main_menu",
    ProductDetailSearchDashboard
);
