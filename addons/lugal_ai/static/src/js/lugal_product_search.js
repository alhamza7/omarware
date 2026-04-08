/** @odoo-module **/

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class LugalProductSearchComponent extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.action = useService("action");
        
        this.state = useState({
            searchQuery: "",
            products: [],
            selectedProduct: null,
            isLoading: false,
            filters: {
                category_id: null,
                min_price: null,
                max_price: null,
                available_only: false,
            },
            categories: [],
            aiSuggestion: null,
            totalCount: 0,
        });
        
        onMounted(() => {
            this.loadCategories();
            this.searchProducts(); // Load initial products
        });
    }
    
    async loadCategories() {
        try {
            const result = await this.rpc("/lugal/api/products/categories", {});
            
            if (result.success) {
                this.state.categories = result.categories;
            }
        } catch (error) {
            console.error("Error loading categories:", error);
        }
    }
    
    async searchProducts() {
        this.state.isLoading = true;
        this.state.aiSuggestion = null;
        
        try {
            const result = await this.rpc("/lugal/api/products/search", {
                query: this.state.searchQuery,
                filters: this.state.filters,
                limit: 50,
            });
            
            if (result.success) {
                this.state.products = result.products;
                this.state.totalCount = result.total_count;
                this.state.aiSuggestion = result.ai_suggestion;
            } else {
                this.notification.add("Error: " + result.error, {
                    type: "danger",
                });
            }
        } catch (error) {
            console.error("Error searching products:", error);
            this.notification.add("Failed to search products", {
                type: "danger",
            });
        } finally {
            this.state.isLoading = false;
        }
    }
    
    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            this.searchProducts();
        }
    }
    
    async selectProduct(product) {
        this.state.selectedProduct = product;
        
        // Load detailed info
        try {
            const result = await this.rpc("/lugal/api/products/details", {
                product_id: product.id,
            });
            
            if (result.success) {
                this.state.selectedProduct = {
                    ...product,
                    ...result.product,
                };
            }
        } catch (error) {
            console.error("Error loading product details:", error);
        }
    }
    
    closeProductDetails() {
        this.state.selectedProduct = null;
    }
    
    openProductForm(productId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.product',
            res_id: productId,
            views: [[false, 'form']],
            target: 'current',
        });
    }
    
    applyFilter(filterName, value) {
        this.state.filters[filterName] = value;
        this.searchProducts();
    }
    
    clearFilters() {
        this.state.filters = {
            category_id: null,
            min_price: null,
            max_price: null,
            available_only: false,
        };
        this.searchProducts();
    }
    
    async askAI() {
        if (!this.state.searchQuery.trim()) {
            this.notification.add("Please enter a question", {
                type: "warning",
            });
            return;
        }
        
        this.state.isLoading = true;
        
        try {
            const result = await this.rpc("/lugal/api/ask", {
                question: this.state.searchQuery,
                context: null,
            });
            
            if (result.success) {
                this.state.aiSuggestion = result.answer;
                this.notification.add("AI answered your question", {
                    type: "success",
                });
            } else {
                this.notification.add("Error: " + result.error, {
                    type: "danger",
                });
            }
        } catch (error) {
            console.error("Error asking AI:", error);
            this.notification.add("Failed to ask AI", {
                type: "danger",
            });
        } finally {
            this.state.isLoading = false;
        }
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat('en-US').format(num);
    }
}

LugalProductSearchComponent.template = "lugal_ai.LugalProductSearchTemplate";

registry.category("actions").add("lugal_product_search", LugalProductSearchComponent);

