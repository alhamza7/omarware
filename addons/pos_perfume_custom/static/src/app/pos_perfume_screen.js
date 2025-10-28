/** @odoo-module */

import { Component, useState, useRef, onMounted, useEnv } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Main POS Perfume Screen Component
 * 50/50 Split Layout: Order Table (left) | Product Search (right)
 */
export class PosPerfumeScreen extends Component {
    static template = "pos_perfume_custom.PosPerfumeScreen";

    setup() {
        this.pos = window.pos || { partners: [], get_cashier: () => ({ name: "Cashier" }) };
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.env = useEnv();
        
        this.state = useState({
            // UI Header state
            userName: 'Cashier',
            currentDate: new Date().toLocaleDateString(),
            currentTime: new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'}),
            
            // Order state
            currentOrder: {
                partner: null,
                orderNumber: 'New Order',
                lines: this.createEmptyLines(5),
                totals: {
                    subtotal: 0,
                    discount: 0,
                    tax: 0,
                    total_usd: 0,
                    total_iqd: 0,
                }
            },
            
            // Customer search state
            customerSearch: '',
            filteredCustomers: [],
            showCustomerDropdown: false,
            
            // Products state
            products: [],
            filteredProducts: [],
            searchTerm: '',
            activeFilter: 'all',
            selectedProductIndex: -1,
            
            // UI state
            loading: false,
            exchangeRate: 1300,
        });
        
        this.searchInputRef = useRef("searchInput");
        
        onMounted(async () => {
            // Set user name from session
            if (window.odoo && window.odoo.session_info) {
                this.state.userName = window.odoo.session_info.name || window.odoo.session_info.username || 'Cashier';
            }
            
            // Update time every minute
            setInterval(() => {
                this.state.currentTime = new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'});
                this.state.currentDate = new Date().toLocaleDateString();
            }, 60000);
            
            // Wait for pos data if not available
            let retries = 0;
            while ((!window.pos || !window.pos.partners || window.pos.partners.length === 0) && retries < 50) {
                await new Promise(resolve => setTimeout(resolve, 100));
                retries++;
            }
            
            if (window.pos && window.pos.partners) {
                this.pos = window.pos;
                console.log(`✅ Loaded ${this.pos.partners.length} partners`);
            }
            
            await this.loadProducts();
            
            // Initialize filtered customers with first 20
            if (this.pos.partners && this.pos.partners.length > 0) {
                this.state.filteredCustomers = this.pos.partners.slice(0, 20);
            }
        });
    }
    
    /**
     * Create empty order lines
     */
    createEmptyLines(count) {
        const lines = [];
        for (let i = 0; i < count; i++) {
            lines.push({
                id: `line_${i}`,
                rowNumber: i + 1,
                product: null,
                productName: '',
                warehouse: 'WH1',
                quantity: 1,
                unitPrice: 0,
                discountPercent: 0,
                priceAfterDiscount: 0,
                total: 0,
                availableQty: 0,
            });
        }
        return lines;
    }
    
    /**
     * Load products from database
     */
    async loadProducts() {
        this.state.loading = true;
        try {
            const products = await this.orm.searchRead(
                "product.product",
                [['sale_ok', '=', true]],
                [
                    'id', 'name', 'default_code', 'foreign_name',
                    'list_price', 'uom_id', 'categ_id', 
                    'qty_available', 'virtual_available'
                ],
                { limit: 1000 }
            );
            
            // Get stock by warehouse for each product
            for (const product of products) {
                product.warehouses = await this.getProductStock(product.id);
                product.price_iqd = product.list_price * this.state.exchangeRate;
            }
            
            this.state.products = products;
            this.state.filteredProducts = products;
            
        } catch (error) {
            console.error("Error loading products:", error);
            this.notification.add(
                _t("Failed to load products"),
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * Get product stock by warehouse
     */
    async getProductStock(productId) {
        try {
            const quants = await this.orm.searchRead(
                "stock.quant",
                [
                    ['product_id', '=', productId],
                    ['location_id.usage', '=', 'internal'],
                ],
                ['quantity', 'reserved_quantity', 'location_id'],
                { limit: 100 }
            );
            
            // Group by warehouse
            const warehouseStock = {};
            for (const quant of quants) {
                const available = quant.quantity - quant.reserved_quantity;
                if (available > 0) {
                    // Extract warehouse code from location
                    const whCode = this.extractWarehouseCode(quant.location_id[1]);
                    if (!warehouseStock[whCode]) {
                        warehouseStock[whCode] = 0;
                    }
                    warehouseStock[whCode] += available;
                }
            }
            
            return Object.entries(warehouseStock).map(([code, qty]) => ({
                code: code,
                quantity: qty
            }));
            
        } catch (error) {
            console.error("Error getting stock:", error);
            return [];
        }
    }
    
    /**
     * Extract warehouse code from location name
     */
    extractWarehouseCode(locationName) {
        // Try to extract WH1, WH2, etc. from location name
        const match = locationName.match(/WH\d+/i);
        return match ? match[0].toUpperCase() : 'WH1';
    }
    
    /**
     * Show customer list
     */
    showCustomerList() {
        this.state.showCustomerDropdown = true;
        if (!this.state.customerSearch || this.state.customerSearch.trim() === '') {
            this.state.filteredCustomers = this.pos.partners.slice(0, 20);
        }
    }
    
    /**
     * Hide customer list with delay
     */
    hideCustomerList() {
        setTimeout(() => {
            this.state.showCustomerDropdown = false;
        }, 200);
    }
    
    /**
     * Search customers
     */
    onCustomerSearch(ev) {
        const searchTerm = ev.target.value;
        this.state.customerSearch = searchTerm;
        this.state.showCustomerDropdown = true;
        
        if (!searchTerm || searchTerm.trim() === '') {
            this.state.filteredCustomers = this.pos.partners.slice(0, 20);
        } else {
            const term = searchTerm.toLowerCase();
            this.state.filteredCustomers = this.pos.partners.filter(p =>
                (p.name && p.name.toLowerCase().includes(term)) ||
                (p.phone && String(p.phone).includes(term)) ||
                (p.mobile && String(p.mobile).includes(term)) ||
                (p.email && p.email.toLowerCase().includes(term))
            ).slice(0, 20);
        }
    }
    
    /**
     * Select customer from dropdown
     */
    selectCustomer(partner) {
        this.state.currentOrder.partner = partner;
        this.state.customerSearch = partner.name;
        this.state.showCustomerDropdown = false;
    }
    
    /**
     * Filter products based on search and filter
     */
    filterProducts() {
        let filtered = this.state.products;
        
        // Text search
        if (this.state.searchTerm) {
            const term = this.state.searchTerm.toLowerCase();
            filtered = filtered.filter(p => 
                (p.name && p.name.toLowerCase().includes(term)) ||
                (p.default_code && p.default_code.toLowerCase().includes(term)) ||
                (p.foreign_name && p.foreign_name.includes(term))
            );
        }
        
        // Category/unit filter
        if (this.state.activeFilter !== 'all') {
            const filter = this.state.activeFilter;
            filtered = filtered.filter(p => {
                // You can add more filter logic based on product attributes
                return p.categ_id && p.categ_id[1].toLowerCase().includes(filter.toLowerCase());
            });
        }
        
        this.state.filteredProducts = filtered;
        this.state.selectedProductIndex = filtered.length > 0 ? 0 : -1;
    }
    
    /**
     * Handle search input
     */
    onSearchInput(ev) {
        this.state.searchTerm = ev.target.value;
        this.filterProducts();
    }
    
    /**
     * Handle filter button click
     */
    onFilterClick(filter) {
        this.state.activeFilter = filter;
        this.filterProducts();
    }
    
    /**
     * Handle search keyboard navigation
     */
    onSearchKeyDown(ev) {
        const products = this.state.filteredProducts;
        
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            this.state.selectedProductIndex = Math.min(
                this.state.selectedProductIndex + 1,
                products.length - 1
            );
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            this.state.selectedProductIndex = Math.max(
                this.state.selectedProductIndex - 1,
                0
            );
        } else if (ev.key === 'Enter' && this.state.selectedProductIndex >= 0) {
            ev.preventDefault();
            this.addProductToOrder(products[this.state.selectedProductIndex]);
        }
    }
    
    /**
     * Add product to order (double click or Enter)
     */
    addProductToOrder(product) {
        // Find first empty line
        const emptyLine = this.state.currentOrder.lines.find(l => !l.product);
        
        if (emptyLine) {
            emptyLine.product = product;
            emptyLine.productName = product.name;
            emptyLine.unitPrice = product.list_price;
            emptyLine.availableQty = product.qty_available || 0;
            
            this.calculateLine(emptyLine);
            this.calculateTotals();
            
            this.notification.add(
                _t("Product added: ") + product.name,
                { type: "success" }
            );
        } else {
            // Add new line
            const newLine = {
                id: `line_${this.state.currentOrder.lines.length}`,
                rowNumber: this.state.currentOrder.lines.length + 1,
                product: product,
                productName: product.name,
                warehouse: 'WH1',
                quantity: 1,
                unitPrice: product.list_price,
                discountPercent: 0,
                priceAfterDiscount: product.list_price,
                total: product.list_price,
                availableQty: product.qty_available || 0,
            };
            
            this.state.currentOrder.lines.push(newLine);
            this.calculateTotals();
        }
    }
    
    /**
     * Handle keyboard navigation in cells (Excel-like)
     */
    handleCellKeyDown(ev, rowIndex, colIndex) {
        const key = ev.key;
        const input = ev.target;
        const isNumberInput = input.type === 'number';
        
        // Check if cursor is at start/end for number inputs
        const cursorAtStart = input.selectionStart === 0;
        const cursorAtEnd = input.selectionStart === input.value.length;
        const hasSelection = input.selectionStart !== input.selectionEnd;
        
        let shouldNavigate = false;
        let targetRow = rowIndex;
        let targetCol = colIndex;
        
        // Tab: Move to next cell (Shift+Tab: previous cell)
        if (key === 'Tab') {
            ev.preventDefault();
            shouldNavigate = true;
            targetRow = rowIndex;
            targetCol = ev.shiftKey ? colIndex - 1 : colIndex + 1;
            
            // If we reach end of row, move to next row first cell
            if (!ev.shiftKey && targetCol > 7) { // 7 is the Total column
                targetRow = rowIndex + 1;
                targetCol = 2; // Start at Warehouse column
            }
            // If we reach start of row going back, move to previous row last cell
            else if (ev.shiftKey && targetCol < 1) {
                targetRow = rowIndex - 1;
                targetCol = 5; // Discount column
            }
        }
        // Enter: Move to next row, same column
        else if (key === 'Enter') {
            ev.preventDefault();
            shouldNavigate = true;
            targetRow = rowIndex + 1;
            targetCol = colIndex;
        }
        // Arrow Down: Move to next row, same column (only if not editing)
        else if (key === 'ArrowDown' && (!isNumberInput || hasSelection)) {
            ev.preventDefault();
            shouldNavigate = true;
            targetRow = rowIndex + 1;
            targetCol = colIndex;
        }
        // Arrow Up: Move to previous row, same column (only if not editing)
        else if (key === 'ArrowUp' && (!isNumberInput || hasSelection)) {
            ev.preventDefault();
            shouldNavigate = true;
            targetRow = rowIndex - 1;
            targetCol = colIndex;
        }
        // Arrow Right: Move to next cell (only if cursor at end or select/readonly)
        else if (key === 'ArrowRight' && (input.tagName === 'SELECT' || cursorAtEnd || input.readOnly)) {
            ev.preventDefault();
            shouldNavigate = true;
            targetRow = rowIndex;
            targetCol = colIndex + 1;
        }
        // Arrow Left: Move to previous cell (only if cursor at start or select/readonly)
        else if (key === 'ArrowLeft' && (input.tagName === 'SELECT' || cursorAtStart || input.readOnly)) {
            ev.preventDefault();
            shouldNavigate = true;
            targetRow = rowIndex;
            targetCol = colIndex - 1;
        }
        
        // Navigate if needed
        if (shouldNavigate) {
            this.navigateToCell(targetRow, targetCol, ev.target);
        }
    }
    
    /**
     * Navigate to specific cell
     */
    navigateToCell(rowIndex, colIndex, currentElement) {
        // Bounds check
        if (rowIndex < 0 || rowIndex >= this.state.currentOrder.lines.length) {
            return;
        }
        
        setTimeout(() => {
            const table = currentElement.closest('table');
            const rows = table.querySelectorAll('tbody tr');
            if (rows[rowIndex]) {
                const cells = rows[rowIndex].querySelectorAll('td');
                // Skip row number (0) and delete button (last)
                const maxCol = cells.length - 2;
                const validCol = Math.max(1, Math.min(colIndex, maxCol)); // Between 1 and maxCol
                
                const targetCell = cells[validCol];
                if (targetCell) {
                    const input = targetCell.querySelector('input, select');
                    if (input) {
                        input.focus();
                        // Select text only for editable fields
                        if (input.select && !input.readOnly) {
                            input.select();
                        }
                    }
                }
            }
        }, 0);
    }
    
    /**
     * Update line field value
     */
    updateLine(lineIndex, field, value) {
        const line = this.state.currentOrder.lines[lineIndex];
        line[field] = value;
        
        this.calculateLine(line);
        this.calculateTotals();
    }
    
    /**
     * Calculate single line totals
     */
    calculateLine(line) {
        const qty = parseFloat(line.quantity) || 0;
        const price = parseFloat(line.unitPrice) || 0;
        const discount = parseFloat(line.discountPercent) || 0;
        
        line.priceAfterDiscount = price * (1 - discount / 100);
        line.total = qty * line.priceAfterDiscount;
    }
    
    /**
     * Calculate order totals
     */
    calculateTotals() {
        let subtotal = 0;
        let discount = 0;
        
        for (const line of this.state.currentOrder.lines) {
            if (line.product) {
                const qty = parseFloat(line.quantity) || 0;
                const price = parseFloat(line.unitPrice) || 0;
                const discountPercent = parseFloat(line.discountPercent) || 0;
                
                subtotal += qty * price;
                discount += (qty * price * discountPercent / 100);
            }
        }
        
        const tax = 0; // No tax for now
        const totalUsd = subtotal - discount + tax;
        const totalIqd = totalUsd * this.state.exchangeRate;
        
        this.state.currentOrder.totals = {
            subtotal: subtotal,
            discount: discount,
            tax: tax,
            total_usd: totalUsd,
            total_iqd: totalIqd,
        };
    }
    
    /**
     * Delete order line
     */
    deleteLine(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        // Reset line to empty
        line.product = null;
        line.productName = '';
        line.unitPrice = 0;
        line.quantity = 1;
        line.discountPercent = 0;
        line.priceAfterDiscount = 0;
        line.total = 0;
        line.availableQty = 0;
        
        this.calculateTotals();
    }
    
    /**
     * Save order as draft
     */
    async saveOrderDraft() {
        await this.saveOrder('draft');
    }
    
    /**
     * Create quotation
     */
    async createQuotation() {
        await this.saveOrder('quotation');
    }
    
    /**
     * Confirm sale order
     */
    async confirmSaleOrder() {
        const orderId = await this.saveOrder('draft');
        if (orderId) {
            // Confirm the order
            await this.orm.call(
                'pos.perfume.order',
                'action_confirm',
                [[orderId]]
            );
            
            this.notification.add(
                _t("Sale order created successfully!"),
                { type: "success" }
            );
            
            // Reset order
            this.resetOrder();
        }
    }
    
    /**
     * Save order to database
     */
    async saveOrder(state) {
        // Validate
        if (!this.state.currentOrder.partner) {
            this.notification.add(
                _t("Please select a customer"),
                { type: "warning" }
            );
            return false;
        }
        
        const lines = this.state.currentOrder.lines.filter(l => l.product);
        if (lines.length === 0) {
            this.notification.add(
                _t("Please add at least one product"),
                { type: "warning" }
            );
            return false;
        }
        
        try {
            this.state.loading = true;
            
            // Prepare order lines
            const orderLines = lines.map((line, index) => [0, 0, {
                sequence: (index + 1) * 10,
                product_id: line.product.id,
                warehouse_id: 1, // Default warehouse
                quantity: line.quantity,
                unit_price: line.unitPrice,
                discount_percent: line.discountPercent,
            }]);
            
            // Create order
            const orderId = await this.orm.create('pos.perfume.order', [{
                partner_id: this.state.currentOrder.partner.id,
                exchange_rate: this.state.exchangeRate,
                order_line_ids: orderLines,
                state: state,
            }]);
            
            // Get the created order to fetch the sequence number
            const createdOrder = await this.orm.read('pos.perfume.order', [orderId], ['name']);
            if (createdOrder && createdOrder[0]) {
                this.state.currentOrder.orderNumber = createdOrder[0].name;
            }
            
            this.notification.add(
                _t("Order saved successfully!"),
                { type: "success" }
            );
            
            return orderId;
            
        } catch (error) {
            console.error("Error saving order:", error);
            this.notification.add(
                _t("Failed to save order: ") + error.message,
                { type: "danger" }
            );
            return false;
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * Cancel current order
     */
    cancelOrder() {
        if (confirm(_t("Are you sure you want to cancel the current order?"))) {
            this.resetOrder();
        }
    }
    
    /**
     * Reset order to empty state
     */
    resetOrder() {
        this.state.currentOrder.partner = null;
        this.state.currentOrder.orderNumber = 'New Order';
        this.state.currentOrder.lines = this.createEmptyLines(5);
        this.state.customerSearch = '';
        this.calculateTotals();
    }
    
    /**
     * Open customer creation dialog
     */
    async openCustomerDialog() {
        try {
            // Open the partner form in a dialog
            await this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    default_is_company: false,
                    default_customer_rank: 1,
                }
            });
            
            // Reload partners after dialog closes
            setTimeout(async () => {
                if (window.pos && window.pos.partners) {
                    const newPartners = await this.orm.searchRead(
                        "res.partner",
                        [],
                        ["id", "name", "email", "phone", "mobile"],
                        { limit: 3000, order: "name" }
                    );
                    newPartners.unshift({
                        id: 0,
                        name: "Walk-in Customer",
                        phone: false,
                        mobile: false,
                        email: false
                    });
                    window.pos.partners = newPartners;
                    this.pos = window.pos;
                    this.state.filteredCustomers = newPartners.slice(0, 20);
                    console.log(`🔄 Reloaded ${newPartners.length} partners`);
                }
            }, 1000);
            
        } catch (e) {
            console.error("Failed to open customer dialog:", e);
            this.notification.add(
                _t("Cannot open customer form"),
                { type: "warning" }
            );
        }
    }
    
    /**
     * Send order via WhatsApp
     */
    async sendWhatsApp() {
        // This would open WhatsApp wizard
        this.notification.add(
            _t("WhatsApp integration - to be implemented"),
            { type: "info" }
        );
    }
    
    /**
     * Format currency
     */
    formatCurrency(amount, currency = 'USD') {
        if (currency === 'USD') {
            return `$${amount.toFixed(2)}`;
        } else {
            return `${Math.floor(amount).toLocaleString('en-US')} IQD`;
        }
    }
}

