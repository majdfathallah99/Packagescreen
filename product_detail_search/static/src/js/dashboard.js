/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({ barcode: "", details: null });

        // timings
        this._DEBOUNCE_MS = 250;
        this._MIN_LEN = 2;
        this._timer = null;
        this._mounted = false;

        onMounted(() => { this._mounted = true; setTimeout(() => this._focus(), 0); });
        onWillUnmount(() => { this._mounted = false; if (this._timer) clearTimeout(this._timer); });
    }

    _focus() {
        if (!this._mounted) return;
        const el = this.el?.querySelector?.(".scan-input");
        if (el) { el.focus(); el.select?.(); }
    }
    _normalize(v) { return String(v || "").replace(/\r|\n/g, "").trim(); }

    // ---- New handlers (for XML using onKeyDown/onInput)
    onKeyDown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            const code = this._normalize(this.state.barcode);
            this._commitScan(code);
        }
    }
    onInput(ev) {
        this.state.barcode = ev.target.value;
        this._debounceCommit();
    }

    // ---- Back-compat handlers (for XML using onProductKeypress/change_product_barcode)
    onProductKeypress() { /* no-op: kept for legacy XML */ }
    change_product_barcode(ev) {
        this.state.barcode = ev.target.value;
        this._debounceCommit();
    }

    _debounceCommit() {
        if (this._timer) clearTimeout(this._timer);
        this._timer = setTimeout(() => {
            const code = this._normalize(this.state.barcode);
            if (code && code.length >= this._MIN_LEN) {
                this._commitScan(code);
            }
        }, this._DEBOUNCE_MS);
    }

    async _commitScan(barcode) {
        if (!barcode) return;
        try {
            const recs = await this.orm.searchRead(
                "product.product",
                [["barcode", "=", barcode]],
                ["id", "display_name", "default_code", "list_price", "uom_id"]
            );
            if (recs && recs.length) {
                const p = recs[0];
                this.state.details = {
                    id: p.id,
                    name: p.display_name,
                    default_code: p.default_code || "",
                    uom: (p.uom_id && p.uom_id[1]) || "",
                    price: p.list_price || 0,
                    // kiosk UI placeholders:
                    package_qty: 0,
                    package_price: 0,
                    symbol: "$",
                    currency_symbol: "$",
                };
            } else {
                this.state.details = null; // template shows 'not found' message
            }
        } catch (e) {
            this.state.details = null; // quiet failure for kiosk mode
        } finally {
            this.state.barcode = "";   // ready for next scan
            setTimeout(() => this._focus(), 0);
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
