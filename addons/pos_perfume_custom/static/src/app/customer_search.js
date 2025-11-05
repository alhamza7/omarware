/** @odoo-module */

import { Component, useState, useRef, onMounted } from "@odoo/owl";
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
        
        this.state = useState({
            searchTerm: '',
            customers: [],
            selectedCustomer: null,
            showDropdown: false,
            loading: false,
        });
        
        this.searchInputRef = useRef("searchInput");
        
        onMounted(async () => {
            // Load initial customer if provided
            if (this.props.selectedCustomerId) {
                await this.loadCustomer(this.props.selectedCustomerId);
            }
            
            // Load recent customers for quick access
            await this.loadRecentCustomers();
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
        
        // Search for customers
        this.searchCustomers(value);
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
        // Future: Add arrow key navigation
        if (ev.key === 'Escape') {
            this.state.showDropdown = false;
        }
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
}

