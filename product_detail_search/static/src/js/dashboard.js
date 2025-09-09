// ---------- Lookup (original: normal barcodes only) ----------
async _commitScan(barcode) {
    if (!barcode) return;

    // Clear + refocus immediately for next scan
    this.state.barcode = "";
    setTimeout(() => this._focus(), 0);

    try {
        // 1) EXACT match on variant barcode (product.product)
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
                // same as before (no packaging math)
                package_qty: 0,
                package_price: 0,
                currency_symbol: "$",
                symbol: "$",
                scanned_as: "product",
                scanned_barcode: barcode,
            };
            return;
        }

        // 2) Fallback: template barcode -> pick main variant
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
            this.state.details = {
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
        } else {
            this.state.details = null; // "لم يتم العثور على منتج"
        }
    } catch {
        this.state.details = null;
    }
}
