/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount, onPatched } = owl;
import { useService } from "@web/core/utils/hooks";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({ barcode: "", details: null });

        // Scan timing
        this._DEBOUNCE_MS = 220;
        this._MIN_LEN = 2;
        this._timer = null;

        // Global scan buffer (when input isn't focused)
        this._scanBuf = "";
        this._bufTimer = null;

        this._mounted = false;

        onMounted(() => {
            this._mounted = true;
            // Build stamp to confirm fresh assets are loaded
            console.log("PDS build 18.0.1.7");

            // Aggressive focus (SPA can steal it)
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

    // Keep code intact. Normalize Arabic-Indic digits; ignore single stray letter only.
    _normalize(v) {
        let s = String(v || "").replace(/[\r\n\t]+/g, "").trim();

        // Arabic-Indic → ASCII (both Arabic and Persian forms)
        const map = {
            "٠":"0","١":"1","٢":"2","٣":"3","٤":"4","٥":"5","٦":"6","٧":"7","٨":"8","٩":"9",
            "۰":"0","۱":"1","۲":"2","۳":"3","۴":"4","۵":"5","۶":"6","۷":"7","۸":"8","۹":"9"
        };
        s = s.replace(/[٠-٩۰-۹]/g, (ch) => map[ch] || ch);

        // If a single stray letter sneaks in (not a real scan), ignore it
        if (s.length === 1 && /[A-Za-z]/.test(s)) return "";

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

    // ---------- Lookup: server (supports packaging) + fallback (normal product barcodes) ----------
    async _commitScan(barcode) {
        if (!barcode) return;

        // Clear + refocus immediately for next scan
        this.state.barcode = "";
        setTimeout(() => this._focus(), 0);

        let details = null;

        try {
            // 1) Preferred: server method (handles product.barcode + product.template.barcode + packaging.barcode)
            const out = await this.orm.call(
                "product.template",
                "product_detail_search",
                [barcode]
            );
            const d = (out && out[0]) || null;

            if (d) {
                details = {
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
            }
        } catch {
            // ignore; fallback below
        }

        try {
            if (!details) {
                // 2) Fallback: EXACT match on variant barcode (product.product) — guarantees normal barcodes work
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
                        package_qty: 0,
                        package_price: 0,
                        currency_symbol: "$",
                        symbol: "$",
                        scanned_as: "product",
                        scanned_barcode: barcode,
                    };
                }
            }
        } catch {
            // ignore
        }

        try {
            if (!details) {
                // 3) Final fallback: template barcode -> pick main variant (keeps pre-packaging behavior)
                const tmpls = await this.orm.searchRead(
                    "product.template",
                    [["barcode", "=", barcode]],
                    ["id", "display_name", "uom_id"]
                );
                if (tmpls && tmpls.length) {
                    const tmpl = tmpls[0];
                    const vars = await this.orm.searchRead(
                        "product.product",
                        [["product_tmpl_id", "=", tmpl.id]],
                        ["id", "list_price"],
                    );
                    const v = vars && vars[0];
                    details = {
                        id: v ? v.id : tmpl.id,
                        name: tmpl.display_name,
                        default_code: "",
                        uom: (tmpl.uom_id && tmpl.uom_id[1]) || "",
                        price: (v && v.list_price) || 0,
                        package_qty: 0,
                        package_price: 0,
                        currency_symbol: "$",
                        symbol: "$",
                        scanned_as: "product",
                        scanned_barcode: barcode,
                    };
                }
            }
        } catch {
            // ignore
        }

        this.state.details = details || null; // template shows "لم يتم العثور على منتج" when null
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
