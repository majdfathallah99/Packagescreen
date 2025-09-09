/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({ barcode: "", details: null });

        this._timer = null;
        this._DEBOUNCE_MS = 220;   // treat scanner burst as one input
        this._MIN_LEN = 2;
        this._mounted = false;

        onMounted(() => { this._mounted = true; setTimeout(() => this._focus(), 0); });
        onWillUnmount(() => { this._mounted = false; if (this._timer) clearTimeout(this._timer); });
    }

    _focus() {
        if (!this._mounted) return;
        const el = this.el?.querySelector?.(".scan-input");
        if (el) { el.focus(); el.select?.(); }
    }

    _normalize(v) {
        let s = String(v || "").replace(/[\r\n\t]+/g, "").trim();
        // Some keyboard-wedge scanners prepend a letter (e.g., "k123..."): strip 1st non-alnum if present
        if (s && /[^0-9A-Za-z]/.test(s[0])) s = s.slice(1);
        if (s && /^[A-Za-z]$/.test(s[0])) s = s.slice(1);
        return s;
    }

    // --- Handlers used by your XML (support both styles)
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
    onProductKeypress() { /* legacy no-op */ }
    change_product_barcode(ev) {
        this.state.barcode = ev.target.value;
        this._debounceCommit();
    }

    _debounceCommit() {
        if (this._timer) clearTimeout(this._timer);
        this._timer = setTimeout(() => {
            const code = this._normalize(this.state.barcode);
            if (code && code.length >= this._MIN_LEN) this._commitScan(code);
        }, this._DEBOUNCE_MS);
    }

    async _commitScan(barcode) {
        if (!barcode) return;

        // Clear field *before* RPC so the next scan starts fresh
        this.state.barcode = "";
        setTimeout(() => this._focus(), 0);

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
                    // kiosk placeholders (no packaging logic here)
                    package_qty: 0,
                    package_price: 0,
                    symbol: "$",           // change to company currency if you want
                    currency_symbol: "$",
                };
            } else {
                this.state.details = null; // your template shows "لم يتم العثور على منتج"
            }
        } catch {
            // Quiet kiosk: no toast spam on errors
            this.state.details = null;
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
