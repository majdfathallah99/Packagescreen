/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount, onPatched } = owl;
import { useService } from "@web/core/utils/hooks";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({ barcode: "", details: null });

        this._timer = null;
        this._DEBOUNCE_MS = 220;
        this._MIN_LEN = 2;
        this._mounted = false;

        onMounted(() => {
            this._mounted = true;
            // focus ASAP and on the next ticks to beat any late layout
            this._focus();
            setTimeout(() => this._focus(), 0);
            setTimeout(() => this._focus(), 120);
            requestAnimationFrame(() => this._focus());
        });
        onPatched(() => {
            // if anything re-rendered (e.g., details appear), keep the input focused
            this._focus();
        });
        onWillUnmount(() => {
            this._mounted = false;
            if (this._timer) clearTimeout(this._timer);
        });
    }

    _focus() {
        if (!this._mounted) return;
        const el = (this.refs && this.refs.scanInput)
            ? this.refs.scanInput
            : this.el?.querySelector?.(".scan-input");
        if (el && document.activeElement !== el) {
            el.focus();
            el.select?.();
        }
    }

    _normalize(v) {
        let s = String(v || "").replace(/[\r\n\t]+/g, "").trim();
        // Strip a leading stray letter some scanners add (e.g., "k123...")
        if (s && /^[A-Za-z]$/.test(s[0])) s = s.slice(1);
        return s;
    }

    // Handlers used by the template (support both styles)
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

        // Clear and refocus immediately so the next scan is ready
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
                    package_qty: 0,
                    package_price: 0,
                    symbol: "$",
                    currency_symbol: "$",
                };
            } else {
                this.state.details = null; // template shows "لم يتم العثور على منتج"
            }
        } catch {
            this.state.details = null; // quiet kiosk
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
