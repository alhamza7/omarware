/** @odoo-module */

import { Component, onMounted, useState, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { PosPerfumeScreen } from "./pos_perfume_screen";

/**
 * Main POS Perfume Application
 * This is the entry point for the fullscreen POS Perfume interface
 */
class PosPerfumeApp extends Component {
    static components = { PosPerfumeScreen };
    static template = xml`
        <div class="pos-perfume-app-wrapper" style="height: 100vh; overflow: hidden;">
            <t t-if="state.dataLoaded">
                <PosPerfumeScreen />
            </t>
            <t t-else="">
                <div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 18px; color: #714B67;">
                    <i class="fa fa-spinner fa-spin" style="margin-right: 10px;"/> Loading NBS POS...
                </div>
            </t>
        </div>
    `;

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ dataLoaded: false });
        
        onMounted(async () => {
            await this.loadPosData();
            this.state.dataLoaded = true;
        });
    }

    async loadPosData() {
        try {
            console.log("🔄 Loading POS data...");
            
            // Load POS configuration (if exists)
            let posConfig = {};
            try {
                const configs = await this.orm.searchRead(
                    "pos.config",
                    [],
                    ["name", "pricelist_id", "currency_id"],
                    { limit: 1 }
                );
                posConfig = configs[0] || {};
                console.log("✅ POS config loaded");
            } catch (e) {
                console.log("ℹ️ POS config not found, using defaults");
            }
            
            // Load partners using searchRead (same as POS original)
            let partners = [];
            try {
                console.log("🔄 Loading partners...");
                
                // Use searchRead with empty domain to get all partners
                partners = await this.orm.searchRead(
                    "res.partner",
                    [],  // Empty domain = all partners
                    ["id", "name", "email", "phone", "mobile"],
                    { 
                        limit: 3000,
                        order: "name"
                    }
                );
                
                console.log(`✅ Successfully loaded ${partners.length} partners from database`);
                
            } catch (e) {
                console.error("❌ Failed to load partners:", e);
                console.error("Error details:", e.message, e.data);
                partners = [];
            }
            
            // Always add walk-in customer at the beginning
            partners.unshift({
                id: 0,
                name: "Walk-in Customer",
                phone: false,
                mobile: false,
                email: false
            });
            
            // Store in global pos object (compatible with POS hooks)
            window.pos = {
                config: posConfig,
                partners: partners,
                get_cashier: () => {
                    return { 
                        name: odoo.session_info.name || odoo.session_info.username || "Cashier" 
                    };
                }
            };
            
            console.log("✅ POS Perfume data loaded successfully");
            console.log(`📦 ${partners.length} customers loaded`);
            console.log("Partners sample:", partners.slice(0, 3));
            
        } catch (error) {
            console.error("Error loading POS data:", error);
            this.notification.add(
                "Failed to load POS configuration",
                { type: "danger" }
            );
        }
    }
}

// Register as a client action
registry.category("actions").add("pos_perfume_custom.PosPerfumeApp", PosPerfumeApp);

export default PosPerfumeApp;

