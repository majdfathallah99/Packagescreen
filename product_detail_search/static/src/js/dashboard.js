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
        // Some USB scanners prepend a stray letter; keep this guard but it won't break normal barcodes
        if (s && /^[A-Za-z]$/.test(s[0])) s = s.slice(1);
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

    // ---------- Lookup (supports product + packaging barcodes) ----------
    async _commitScan(barcode) {
        if (!barcode) return;

        // Clear + refocus immediately for next scan
        this.state.barcode = "";
        setTimeout(() => this._focus(), 0);

        try {
            // Call server method that checks product.barcode, then product.packaging.barcode
            const out = await this.orm.call(
                "product.template",
                "product_detail_search",
                [barcode]
            );

            const d = (out && out[0]) || null;

            if (d) {
                // Normalize keys so templates can use either symbol or currency_symbol
                this.state.details = {
                    id: d.id,
                    name: d.name,
                    default_code: d.default_code || "",
                    uom: d.uom || "",
                    price: d.price || 0,
                    package_qty: d.package_qty || 0,
                    package_price: d.package_price || 0,
                    currency_symbol: d.currency_symbol || "$",
                    symbol: d.currency_symbol || "$",
                    scanned_as: d.scanned_as || "product",
                    scanned_barcode: d.scanned_barcode || barcode,
                };
            } else {
                this.state.details = null; // template displays "لم يتم العثور على منتج"
            }
        } catch {
            this.state.details = null; // stay quiet in kiosk mode
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
