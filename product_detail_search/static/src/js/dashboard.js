/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({ barcode: "", details: null });
        this._typed = false;
        this._timer = null;
        this._DEBOUNCE = 250;
        this._mounted = false;

        onMounted(() => { this._mounted = true; setTimeout(() => this._focus(), 0); });
        onWillUnmount(() => { this._mounted = false; if (this._timer) clearTimeout(this._timer); });
    }

    _focus() {
        if (!this._mounted) return;
        const el = this.el && this.el.querySelector && this.el.querySelector(".scan-input");
        if (el) { el.focus(); el.select && el.select(); }
    }

    onProductKeypress() { this._typed = true; }

    change_product_barcode(ev) {
        this.state.barcode = ev.target.value;
        if (!this._typed) return;
        if (this._timer) clearTimeout(this._timer);
        this._timer = setTimeout(() => this.get_product(), this._DEBOUNCE);
    }

    async get_product() {
        const barcode = (this.state.barcode || "").replace(/\r|\n/g, "").trim();
        if (!barcode) { this.state.details = null; return; }

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
                    symbol: "$",            // change to company currency if you prefer
                    currency_symbol: "$",
                };
            } else {
                this.state.details = null;   // template shows "لم يتم العثور على منتج"
            }
        } catch (e) {
            this.state.details = null;       // quiet kiosk: no toast spam
        } finally {
            this.state.barcode = "";         // ready for next scan
            setTimeout(() => this._focus(), 0);
        }
    }
}

ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
