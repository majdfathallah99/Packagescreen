/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount, onPatched } = owl;
import { useService } from "@web/core/utils/hooks";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({ barcode: "", details: null });

        // Scan debounce
        this._DEBOUNCE_MS = 220;
        this._MIN_LEN = 2;
        this._timer = null;

        // Global scan buffer (fallback when input isn't focused)
        this._scanBuf = "";
        this._bufTimer = null;

        this._mounted = false;

        onMounted(() => {
            this._mounted = true;
            // focus aggressively (SPA can steal focus)
            this._focus();
            setTimeout(() => this._focus(), 0);
            setTimeout(() => this._focus(), 120);
            requestAnimationFrame(() => this._focus());

            // Global listener so scanning works even if focus moves
            this._onGlobalKeydown = (ev) => this._handleGlobalKeydown(ev);
            document.addEventListener("keydown", this._onGlobalKeydown, { capture: true });
        });

        onPatched(() => this._focus());

        onWillUnmount(() => {
            this._mounted = false;
            if (this._timer) clearTimeout(this._timer);
            if (this._bufTimer) clearTimeout(this._bufTimer);
            if (this._onGlobalKeydown) {
                document.removeEventListener("keydown", this._onGlobalKeydown, { capture: true });
            }
        });
    }

    // ---------- Focus helpers ----------
    _focus() {
        if (!this._mounted) return;
        const el = (this.refs && this.refs.scanInput) ? this.refs.scanInput : this.el?.querySelector?.(".scan-input");
        if (el && document.activeElement !== el) {
            el.focus();
            el.select?.();
        }
    }
    _normalize(v) {
        let s = String(v || "").replace(/[\r\n\t]+/g, "").trim();
        if (s && /^[A-Za-z]$/.test(s[0])) s = s.slice(1); // strip stray leading letter from some scanners
        return s;
    }

    // ---------- Input-bound handlers ----------
    onKeyDown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            const code = this._normalize(this.state.barcode);
            this._commitScan(code);
        }
    }
    onInput(ev) {
        this.state.barcode = ev.target.value;
        if (this._timer) clearTimeout(this._timer);
        this._timer = setTimeout(() => {
            const code = this._normalize(this.state.barcode);
            if (code && code.length >= this._MIN_LEN) this._commitScan(code);
        }, this._DEBOUNCE_MS);
    }

    // ---------- Global fallback: capture scans anywhere ----------
    _handleGlobalKeydown(ev) {
        // If user is already typing inside our input, do nothing
        const isOurInput = ev.target && (ev.target === this.refs?.scanInput);
        if (isOurInput) return;

        // Ignore when typing in other inputs/contenteditables
        if (ev.target && (ev.target.tagName === "INPUT" || ev.target.tagName === "TEXTAREA" || ev.target.isContentEditable)) {
            return;
        }

        const k = ev.key;
        if (k === "Enter") {
            const code = this._normalize(this._scanBuf);
            this._scanBuf = "";
            if (code && code.length >= this._MIN_LEN) {
                ev.preventDefault();
                this._commitScan(code);
            }
            return;
        }

        // Accept digits/letters only
        if (/^[0-9A-Za-z]$/.test(k)) {
            this._scanBuf += k;
            if (this._bufTimer) clearTimeout(this._bufTimer);
            this._bufTimer = setTimeout(() => {
                const code = this._normalize(this._scanBuf);
                this._scanBuf = "";
                if (code && code.length >= this._MIN_LEN) this._commitScan(code);
            }, 180);
        }
    }

    // ---------- Lookup ----------
    async _commitScan(barcode) {
        if (!barcode) return;

        // Clear + refocus immediately for next scan
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
                this.state.details = null; // template displays "لم يتم العثور على منتج"
            }
        } catch {
            this.state.details = null; // no toasts in kiosk mode
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
