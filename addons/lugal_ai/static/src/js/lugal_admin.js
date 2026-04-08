/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class LugalAdminComponent extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            config: null,
            cacheStats: null,
            conversationStats: null,
            isLoading: false,
        });
        
        onMounted(() => {
            this.loadStats();
        });
    }
    
    async loadStats() {
        this.state.isLoading = true;
        
        try {
            // Load cache stats
            const cacheStats = await this.orm.call(
                "lugal.cache",
                "get_cache_stats",
                []
            );
            this.state.cacheStats = cacheStats;
            
            // Load conversation stats
            const conversationStats = await this.orm.call(
                "lugal.conversation",
                "get_conversation_stats",
                [],
                { days: 30 }
            );
            this.state.conversationStats = conversationStats;
            
        } catch (error) {
            console.error("Error loading stats:", error);
            this.notification.add("Failed to load statistics", {
                type: "danger",
            });
        } finally {
            this.state.isLoading = false;
        }
    }
    
    async cleanupCache() {
        try {
            const count = await this.orm.call(
                "lugal.cache",
                "cleanup_expired_cache",
                []
            );
            
            this.notification.add(`Cleaned up ${count} expired cache entries`, {
                type: "success",
            });
            
            this.loadStats();
        } catch (error) {
            console.error("Error cleaning cache:", error);
            this.notification.add("Failed to cleanup cache", {
                type: "danger",
            });
        }
    }
}

LugalAdminComponent.template = "lugal_ai.LugalAdminTemplate";

registry.category("actions").add("lugal_admin", LugalAdminComponent);

