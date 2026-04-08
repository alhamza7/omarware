/** @odoo-module */

import { Component } from "@odoo/owl";

export class TotalIQDWidget extends Component {
    static template = "pos_perfume_custom.TotalIQDWidget";

    get pos() {
        return this.env.services.pos;
    }

    get currentOrder() {
        return this.pos.get_order();
    }

    /** Uses order exchange_rate (synced from SAP via pos_perfume.default_exchange_rate_usd_iqd) or fallback 1560 */
    get totalIQD() {
        if (!this.currentOrder) return 0;
        const rate = this.currentOrder.exchange_rate || 1560;
        return Math.floor(this.currentOrder.get_total_with_tax() * rate);
    }

    get formattedTotalIQD() {
        return this.totalIQD.toLocaleString('en-US');
    }
}
