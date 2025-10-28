/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { TotalIQDWidget } from "@pos_perfume_custom/app/total_iqd_widget";

// Patch payment screen to add our widget
patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        console.log('✅ POS Perfume: Payment screen patched!');
    }
});

// Register the component
PaymentScreen.components = {
    ...PaymentScreen.components,
    TotalIQDWidget,
};

console.log('✅ POS Perfume Custom: Module loaded successfully!');
console.log('✅ IQD Widget registered');
console.log('✅ Exchange rate: 1 USD = 1,300 IQD');
