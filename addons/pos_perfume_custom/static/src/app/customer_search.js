/** @odoo-module */

import { Component, useState, useRef, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Customer Search Component
 * Component للبحث عن العملاء واختيارهم
 */
export class CustomerSearch extends Component {
    static template = "pos_perfume_custom.CustomerSearch";
    static props = {
        onSelectCustomer: Function,
        selectedCustomerId: { type: Number, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        
        this.state = useState({
            searchTerm: '',
            customers: [],
            selectedCustomer: null,
            showDropdown: false,
            loading: false,
            selectedIndex: 0,  // For keyboard navigation
        });
        
        this.searchInputRef = useRef("searchInput");
        this.searchTimer = null;
        
        onMounted(async () => {
            // Load initial customer if provided
            if (this.props.selectedCustomerId) {
                await this.loadCustomer(this.props.selectedCustomerId);
            }
            
            // Load recent customers for quick access
            await this.loadRecentCustomers();
        });
        
        // Update customer when selectedCustomerId prop changes
        onWillUpdateProps(async (nextProps) => {
            if (nextProps.selectedCustomerId !== this.props.selectedCustomerId) {
                if (nextProps.selectedCustomerId) {
                    await this.loadCustomer(nextProps.selectedCustomerId);
                } else {
                    // Clear selection if customer ID is removed
                    this.state.selectedCustomer = null;
                    this.state.searchTerm = '';
                }
            }
        });
    }
    
    /**
     * Handle input event
     */
    onSearchInput(ev) {
        const value = ev.target.value;
        
        // Clear selection if user is typing
        if (this.state.selectedCustomer) {
            this.state.selectedCustomer = null;
            this.props.onSelectCustomer(null);
        }
        
        // Update search term immediately
        this.state.searchTerm = value;
        this.state.selectedIndex = 0;  // Reset selection index
        
        // Clear existing timer
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        
        // Debounce search
        this.searchTimer = setTimeout(() => {
            this.searchCustomers(value);
        }, 300);
    }
    
    /**
     * البحث عن العملاء
     * Search for customers
     */
    async searchCustomers(term) {
        if (!term || term.length < 2) {
            this.state.customers = [];
            this.state.showDropdown = false;
            return;
        }
        
        this.state.loading = true;
        this.state.showDropdown = true;
        
        try {
            const customers = await this.orm.searchRead(
                'res.partner',
                [
                    ['customer_rank', '>', 0],
                    '|', '|',
                    ['name', 'ilike', term],
                    ['phone', 'ilike', term],
                    ['email', 'ilike', term],
                ],
                ['id', 'name', 'phone', 'email', 'property_product_pricelist'],
                { limit: 20, order: 'name' }
            );
            
            this.state.customers = customers;
        } catch (error) {
            console.error('Error searching customers:', error);
            this.notification.add(
                _t('Error searching customers'),
                { type: 'danger' }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * Load recent customers
     */
    async loadRecentCustomers() {
        try {
            const customers = await this.orm.searchRead(
                'res.partner',
                [['customer_rank', '>', 0]],
                ['id', 'name', 'phone', 'email', 'property_product_pricelist'],
                { limit: 10, order: 'write_date DESC' }
            );
            
            if (!this.state.searchTerm) {
                this.state.customers = customers;
            }
        } catch (error) {
            console.error('Error loading recent customers:', error);
        }
    }
    
    /**
     * Load specific customer by ID
     */
    async loadCustomer(customerId) {
        try {
            const customers = await this.orm.searchRead(
                'res.partner',
                [['id', '=', customerId]],
                ['id', 'name', 'phone', 'email', 'property_product_pricelist'],
                { limit: 1 }
            );
            
            if (customers.length > 0) {
                this.state.selectedCustomer = customers[0];
                this.state.searchTerm = customers[0].name;
            }
        } catch (error) {
            console.error('Error loading customer:', error);
        }
    }
    
    /**
     * اختيار عميل
     * Select a customer
     */
    selectCustomer(customer) {
        this.state.selectedCustomer = customer;
        this.state.searchTerm = customer.name;
        this.state.showDropdown = false;
        
        // Notify parent component
        this.props.onSelectCustomer({
            id: customer.id,
            name: customer.name,
            phone: customer.phone,
            email: customer.email,
            pricelist_id: customer.property_product_pricelist ? customer.property_product_pricelist[0] : null,
        });
        
        this.notification.add(
            _t('Customer selected: ') + customer.name,
            { type: 'success' }
        );
    }
    
    /**
     * Clear selection
     */
    clearSelection() {
        this.state.selectedCustomer = null;
        this.state.searchTerm = '';
        this.state.customers = [];
        this.state.showDropdown = false;
        
        this.props.onSelectCustomer(null);
        
        if (this.searchInputRef.el) {
            this.searchInputRef.el.focus();
        }
    }
    
    /**
     * Handle input focus
     */
    onFocus() {
        this.state.showDropdown = true;
        if (this.state.customers.length === 0) {
            this.loadRecentCustomers();
        }
        this.state.selectedIndex = 0;  // Reset selection on focus
    }
    
    /**
     * Handle input blur (with delay for click)
     */
    onBlur() {
        setTimeout(() => {
            this.state.showDropdown = false;
        }, 200);
    }
    
    /**
     * Handle keyboard navigation
     */
    onKeydown(ev) {
        if (!this.state.showDropdown || !this.state.customers.length) {
            if (ev.key === 'Escape') {
                this.state.showDropdown = false;
            }
            return;
        }
        
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            this.state.selectedIndex = Math.min(
                this.state.selectedIndex + 1,
                this.state.customers.length - 1
            );
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            this.state.selectedIndex = Math.max(this.state.selectedIndex - 1, 0);
        } else if (ev.key === 'Enter') {
            ev.preventDefault();
            if (this.state.customers[this.state.selectedIndex]) {
                this.selectCustomer(this.state.customers[this.state.selectedIndex]);
            }
        } else if (ev.key === 'Escape') {
            this.state.showDropdown = false;
        }
    }
    
    /**
     * Check if customer is selected (for highlighting)
     */
    isCustomerSelected(customer) {
        const index = this.state.customers.findIndex(c => c.id === customer.id);
        return index === this.state.selectedIndex;
    }
    
    /**
     * Get customer display info
     */
    getCustomerInfo(customer) {
        const parts = [];
        
        if (customer.phone) {
            parts.push('📞 ' + customer.phone);
        }
        
        if (customer.email) {
            parts.push('✉️ ' + customer.email);
        }
        
        return parts.join(' | ');
    }
    
    /**
     * Open customer popup/form view
     */
    async openCustomerPopup() {
        if (!this.state.selectedCustomer) {
            return;
        }
        
        try {
            await this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                res_id: this.state.selectedCustomer.id,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    default_id: this.state.selectedCustomer.id,
                }
            });
        } catch (error) {
            console.error("Error opening customer popup:", error);
            this.notification.add(_t("Failed to open customer details"), { type: "danger" });
        }
    }
}

