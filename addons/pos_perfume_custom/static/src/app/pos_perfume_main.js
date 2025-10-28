/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { TotalIQDWidget } from "@pos_perfume_custom/app/total_iqd_widget";
import { PosPerfumeScreen } from "@pos_perfume_custom/app/pos_perfume_screen";
import { registry } from "@web/core/registry";

// Patch payment screen to add IQD widget
patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        console.log('✅ POS Perfume: Payment screen patched!');
    }
});

// Register the IQD widget component
PaymentScreen.components = {
    ...PaymentScreen.components,
    TotalIQDWidget,
};

// Register the POS Perfume Screen in the registry
// This can be accessed via menu or button
registry.category("pos_screens").add("PosPerfumeScreen", PosPerfumeScreen);

// Optional: Add button to main product screen to access perfume interface
patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },
    
    async openPerfumeInterface() {
        // Navigate to perfume screen
        this.pos.showScreen("PosPerfumeScreen");
    }
});

console.log('✅ POS Perfume Custom: Module loaded successfully!');
console.log('✅ IQD Widget registered');
console.log('✅ Perfume Screen registered');
console.log('✅ Exchange rate: 1 USD = 1,300 IQD');
console.log('✅ Design: 50/50 split layout with Excel-like order table');
console.log('✅ Features: Multi-warehouse, dual currency, keyboard navigation');
