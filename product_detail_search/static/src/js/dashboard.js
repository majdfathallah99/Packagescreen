/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState } = owl;
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class ProductDetailSearchDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ barcode: "", details: null });
        this._typed = false;
    }
    onProductKeypress() { this._typed = true; }

    async change_product_barcode(ev) {
        this.state.barcode = ev.target.value || "";
        if (!this._typed) return;
        this._typed = false;

        const barcode = this.state.barcode.trim();
        if (!barcode) { this.state.details = null; return; }

        try {
            const res = await this.orm.call("product.template", "product_detail_search", [[], barcode]);
            this.state.details = (res && res.length) ? res[0] : null;
            if (!this.state.details) this.notification.add(_t("Product not found."), { type: "warning" });
        } catch (e) {
            this.notification.add(_t("Error fetching product."), { type: "danger" });
            this.state.details = null;
        }
    }
}
ProductDetailSearchDashboard.template = "CustomDashBoardFindProduct";
registry.category("actions").add("product_detail_search_barcode_main_menu", ProductDetailSearchDashboard);
