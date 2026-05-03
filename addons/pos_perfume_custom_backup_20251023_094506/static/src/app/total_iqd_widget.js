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

    get totalIQD() {
        if (!this.currentOrder) return 0;
        return Math.floor(this.currentOrder.get_total_with_tax() * 1300);
    }

    get formattedTotalIQD() {
        return this.totalIQD.toLocaleString('en-US');
    }
}
