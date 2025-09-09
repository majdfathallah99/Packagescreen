/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this._t = _t;

        this.state = useState({ barcode: "", details: null });

        this._debounceTimer = null;
        this._DEBOUNCE_MS = 250;
        this._MIN_LEN = 6;
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

        let details = null;
        let hadRpcFailure = false;

        // 1) Preferred: call server helper
        try {
            const res = await this.orm.call(
                "product.template",
                "product_detail_search",
                [barcode]
            );
            details = (res && res.length) ? res[0] : null;
        } catch (e) {
            hadRpcFailure = true;
            // console.error("RPC product_detail_search failed:", e);
        }

        // 2) Fallback: plain search_read on product.product
        if (!details) {
            try {
                const recs = await this.orm.searchRead(
                    "product.product",
                    [["barcode", "=", barcode]],
                    ["id", "display_name", "default_code", "list_price", "uom_id"]
                );
                if (recs && recs.length) {
                    const p = recs[0];
                    details = {
                        id: p.id,
                        name: p.display_name,
                        default_code: p.default_code || "",
                        uom: (p.uom_id && p.uom_id[1]) || "",
                        price: p.list_price || 0,
                        // Fallback has no packaging computation:
                        package_qty: 0,
                        package_price: 0,
                        // We purposely don’t depend on company currency here; UI shows $ per your mock.
                        symbol: "$",
                        currency_symbol: "$",
                    };
                }
            } catch (e2) {
                // console.error("Fallback search_read failed:", e2);
                // Only show a toast if both attempts failed completely
                if (hadRpcFailure) {
                    this.notification.add(this._t("Error fetching product."), { type: "danger" });
                }
            }
        }

        // 3) Render or warn (single toast)
        if (!details) {
            this.state.details = null;
            this.notification.add(this._t("Product not found."), { type: "warning" });
        } else {
            this.state.details = details;
        }

        // 4) Prepare for next scan
        this.state.barcode = "";
        setTimeout(() => this.focusInput(), 0);
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add(
    "product_detail_search_barcode_main_menu",
    ProductDetailSearchDashboard
);
