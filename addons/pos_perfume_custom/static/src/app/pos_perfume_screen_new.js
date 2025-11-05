/** @odoo-module */

import { Component, useState, useRef, onMounted, useEnv } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { CustomerSearch } from "./customer_search";

/**
 * Main POS Perfume Screen Component - Enhanced like Sale Order
 * Dynamic product search, UoM selection, real warehouse stock
 */
export class PosPerfumeScreen extends Component {
    static template = "pos_perfume_custom.PosPerfumeScreen";
    static components = { CustomerSearch };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.env = useEnv();
        
        this.state = useState({
            // UI Header state
            userName: 'Cashier',
            currentDate: new Date().toLocaleDateString(),
            currentTime: new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'}),
            
            // Pricelists
            pricelists: [],
            
            // Order state
            currentOrder: {
                partner: null,
                partner_id: null,
                pricelist_id: 1,
                orderNumber: 'New Order',
                lines: this.createEmptyLines(10),
                totals: {
                    subtotal: 0,
                    discount: 0,
                    tax: 0,
                    total_usd: 0,
                    total_iqd: 0,
                }
            },
            
            // UI state
            exchangeRate: 1300,
        });
        
        // Debounce timer for search
        this.searchTimers = {};
        
        onMounted(async () => {
            // Set user name
            if (window.odoo && window.odoo.session_info) {
                this.state.userName = window.odoo.session_info.name || window.odoo.session_info.username || 'Cashier';
            }
            
            // Update time every minute
            setInterval(() => {
                this.state.currentTime = new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'});
                this.state.currentDate = new Date().toLocaleString();
            }, 60000);
            
            // Load pricelists
            await this.loadPricelists();
        });
    }
    
    /**
     * Load available pricelists
     */
    async loadPricelists() {
        try {
            const pricelists = await this.orm.searchRead(
                'product.pricelist',
                [],
                ['id', 'name', 'currency_id'],
                { limit: 100, order: 'name' }
            );
            
            this.state.pricelists = pricelists;
            
            // Set default pricelist
            if (pricelists.length > 0 && !this.state.currentOrder.pricelist_id) {
                this.state.currentOrder.pricelist_id = pricelists[0].id;
            }
        } catch (error) {
            console.error('Error loading pricelists:', error);
        }
    }
    
    /**
     * Create empty order lines
     */
    createEmptyLines(count) {
        const lines = [];
        for (let i = 0; i < count; i++) {
            lines.push(this.createEmptyLine(i + 1));
        }
        return lines;
    }
    
    /**
     * Create single empty line
     */
    createEmptyLine(rowNumber) {
        return {
            id: `line_${Date.now()}_${Math.random()}`,
            rowNumber: rowNumber,
            product_id: null,
            productName: '',
            searchResults: [],
            searchingProducts: false,
            showProductDropdown: false,
            selectedProductIndex: 0,
            uom_id: null,
            availableUoms: [],
            warehouse_id: null,
            availableWarehouses: [],
            availableQty: null,
            quantity: 1,
            unitPrice: 0,
            discountPercent: 0,
            priceAfterDiscount: 0,
            total: 0,
        };
    }
    
    /**
     * Handle product search input (dynamic search)
     */
    async onProductSearch(ev, lineIndex) {
        const searchTerm = ev.target.value;
        const line = this.state.currentOrder.lines[lineIndex];
        
        line.productName = searchTerm;
        
        // Clear existing timer
        if (this.searchTimers[lineIndex]) {
            clearTimeout(this.searchTimers[lineIndex]);
        }
        
        if (!searchTerm || searchTerm.length < 2) {
            line.searchResults = [];
            line.showProductDropdown = false;
            return;
        }
        
        // Debounce search
        this.searchTimers[lineIndex] = setTimeout(async () => {
            line.searchingProducts = true;
            line.showProductDropdown = true;
            
            try {
                const products = await this.orm.searchRead(
                    'product.product',
                    [
                        ['sale_ok', '=', true],
                        '|', '|',
                        ['name', 'ilike', searchTerm],
                        ['default_code', 'ilike', searchTerm],
                        ['barcode', 'ilike', searchTerm],
                    ],
                    ['id', 'name', 'default_code', 'list_price', 'uom_id'],
                    { limit: 20 }
                );
                
                // Add uom_name for display
                products.forEach(p => {
                    p.uom_name = p.uom_id ? p.uom_id[1] : '-';
                });
                
                line.searchResults = products;
                line.selectedProductIndex = 0;
            } catch (error) {
                console.error('Error searching products:', error);
                this.notification.add(_t('Error searching products'), { type: 'danger' });
            } finally {
                line.searchingProducts = false;
            }
        }, 300);
    }
    
    /**
     * Handle product focus
     */
    onProductFocus(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        if (line.searchResults.length > 0) {
            line.showProductDropdown = true;
        }
    }
    
    /**
     * Handle product blur
     */
    onProductBlur(ev, lineIndex) {
        setTimeout(() => {
            const line = this.state.currentOrder.lines[lineIndex];
            line.showProductDropdown = false;
        }, 200);
    }
    
    /**
     * Handle keyboard navigation in product search
     */
    handleProductKeyDown(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        if (!line.showProductDropdown || !line.searchResults.length) {
            return;
        }
        
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            line.selectedProductIndex = Math.min(
                line.selectedProductIndex + 1,
                line.searchResults.length - 1
            );
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            line.selectedProductIndex = Math.max(line.selectedProductIndex - 1, 0);
        } else if (ev.key === 'Enter') {
            ev.preventDefault();
            if (line.searchResults[line.selectedProductIndex]) {
                this.selectProduct(lineIndex, line.searchResults[line.selectedProductIndex]);
            }
        } else if (ev.key === 'Escape') {
            line.showProductDropdown = false;
        }
    }
    
    /**
     * Select product from dropdown
     */
    async selectProduct(lineIndex, product) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        line.product_id = product.id;
        line.productName = product.name;
        line.showProductDropdown = false;
        line.searchResults = [];
        
        // Load available UoMs and warehouses
        await Promise.all([
            this.loadAvailableUoms(lineIndex, product.id),
            this.loadAvailableWarehouses(lineIndex, product.id)
        ]);
        
        this.notification.add(
            _t('Product selected: ') + product.name,
            { type: 'success' }
        );
    }
    
    /**
     * Load available UoMs with prices from pricelist
     */
    async loadAvailableUoms(lineIndex, productId) {
        const line = this.state.currentOrder.lines[lineIndex];
        const pricelistId = this.state.currentOrder.pricelist_id || 1;
        
        try {
            // Call backend method to get UoMs with prices
            const uoms = await this.orm.call(
                'product.product',
                'get_available_uoms_with_prices',
                [productId, pricelistId]
            );
            
            line.availableUoms = uoms;
            
            // Set default UoM (first one)
            if (uoms.length > 0) {
                line.uom_id = uoms[0].id;
                line.unitPrice = uoms[0].price;
                this.calculateLine(line);
            }
        } catch (error) {
            console.error('Error loading UoMs:', error);
            this.notification.add(
                _t('Error loading units of measure'),
                { type: 'danger' }
            );
        }
    }
    
    /**
     * Load available warehouses with stock
     */
    async loadAvailableWarehouses(lineIndex, productId) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        try {
            // Get stock by warehouse
            const quants = await this.orm.searchRead(
                'stock.quant',
                [
                    ['product_id', '=', productId],
                    ['location_id.usage', '=', 'internal'],
                ],
                ['quantity', 'reserved_quantity', 'location_id'],
                { limit: 100 }
            );
            
            // Get warehouse information
            const warehouses = await this.orm.searchRead(
                'stock.warehouse',
                [],
                ['id', 'name', 'code'],
                { limit: 50 }
            );
            
            // Map warehouse stock
            const warehouseStock = {};
            for (const quant of quants) {
                const available = quant.quantity - quant.reserved_quantity;
                
                // Try to find warehouse from location name
                const locationName = quant.location_id[1];
                const warehouse = warehouses.find(wh => 
                    locationName.includes(wh.code) || locationName.includes(wh.name)
                );
                
                if (warehouse) {
                    if (!warehouseStock[warehouse.id]) {
                        warehouseStock[warehouse.id] = {
                            id: warehouse.id,
                            name: warehouse.name,
                            code: warehouse.code,
                            quantity: 0
                        };
                    }
                    warehouseStock[warehouse.id].quantity += available;
                }
            }
            
            line.availableWarehouses = Object.values(warehouseStock).filter(wh => wh.quantity > 0);
            
            // Set default warehouse
            if (line.availableWarehouses.length > 0) {
                line.warehouse_id = line.availableWarehouses[0].id;
                line.availableQty = line.availableWarehouses[0].quantity;
            }
        } catch (error) {
            console.error('Error loading warehouses:', error);
        }
    }
    
    /**
     * Handle UoM change
     */
    onUomChange(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const selectedUom = line.availableUoms.find(uom => uom.id === parseInt(line.uom_id));
        
        if (selectedUom) {
            line.unitPrice = selectedUom.price;
            this.calculateLine(line);
            this.calculateTotals();
        }
    }
    
    /**
     * Handle warehouse change
     */
    onWarehouseChange(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const selectedWh = line.availableWarehouses.find(wh => wh.id === parseInt(line.warehouse_id));
        
        if (selectedWh) {
            line.availableQty = selectedWh.quantity;
        }
    }
    
    /**
     * Handle pricelist change
     */
    async onPricelistChange() {
        // Reload prices for all lines that have products
        for (let i = 0; i < this.state.currentOrder.lines.length; i++) {
            const line = this.state.currentOrder.lines[i];
            if (line.product_id) {
                await this.loadAvailableUoms(i, line.product_id);
            }
        }
        
        this.notification.add(
            _t('Pricelist changed - prices updated'),
            { type: 'success' }
        );
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
            if (line.product_id) {
                const qty = parseFloat(line.quantity) || 0;
                const price = parseFloat(line.unitPrice) || 0;
                const discountPercent = parseFloat(line.discountPercent) || 0;
                
                subtotal += qty * price;
                discount += (qty * price * discountPercent / 100);
            }
        }
        
        const tax = 0;
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
        this.state.currentOrder.lines[lineIndex] = this.createEmptyLine(lineIndex + 1);
        this.calculateTotals();
    }
    
    /**
     * Handle customer selection
     */
    onSelectCustomer(customer) {
        if (customer) {
            this.state.currentOrder.partner = customer.name;
            this.state.currentOrder.partner_id = customer.id;
            
            // Set customer's pricelist if available
            if (customer.pricelist_id) {
                this.state.currentOrder.pricelist_id = customer.pricelist_id;
                this.onPricelistChange();
            }
            
            this.notification.add(
                _t(`Customer selected: ${customer.name}`),
                { type: "success" }
            );
        } else {
            this.state.currentOrder.partner = null;
            this.state.currentOrder.partner_id = null;
        }
    }
    
    /**
     * Open customer dialog
     */
    async openCustomerDialog() {
        try {
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
        } catch (e) {
            console.error("Failed to open customer dialog:", e);
        }
    }
    
    /**
     * Save order
     */
    async saveOrder(state) {
        if (!this.state.currentOrder.partner_id) {
            this.notification.add(_t("Please select a customer"), { type: "warning" });
            return false;
        }
        
        const lines = this.state.currentOrder.lines.filter(l => l.product_id);
        if (lines.length === 0) {
            this.notification.add(_t("Please add at least one product"), { type: "warning" });
            return false;
        }
        
        try {
            const orderLines = lines.map((line, index) => [0, 0, {
                sequence: (index + 1) * 10,
                product_id: line.product_id,
                product_uom: line.uom_id,
                warehouse_id: line.warehouse_id,
                quantity: line.quantity,
                unit_price: line.unitPrice,
                discount_percent: line.discountPercent,
            }]);
            
            const orderId = await this.orm.create('pos.perfume.order', [{
                partner_id: this.state.currentOrder.partner_id,
                pricelist_id: this.state.currentOrder.pricelist_id,
                exchange_rate: this.state.exchangeRate,
                order_line_ids: orderLines,
                state: state,
            }]);
            
            this.notification.add(_t("Order saved successfully!"), { type: "success" });
            return orderId;
        } catch (error) {
            console.error("Error saving order:", error);
            this.notification.add(_t("Failed to save order: ") + error.message, { type: "danger" });
            return false;
        }
    }
    
    /**
     * Create quotation
     */
    async createQuotation() {
        await this.saveOrder('draft');
    }
    
    /**
     * Confirm sale order
     */
    async confirmSaleOrder() {
        const orderId = await this.saveOrder('draft');
        if (orderId) {
            await this.orm.call('pos.perfume.order', 'action_confirm', [[orderId]]);
            this.notification.add(_t("Sale order created successfully!"), { type: "success" });
            this.resetOrder();
        }
    }
    
    /**
     * Save draft
     */
    async saveOrderDraft() {
        await this.saveOrder('draft');
    }
    
    /**
     * Cancel order
     */
    cancelOrder() {
        if (confirm(_t("Are you sure you want to cancel the current order?"))) {
            this.resetOrder();
        }
    }
    
    /**
     * Reset order
     */
    resetOrder() {
        this.state.currentOrder.partner = null;
        this.state.currentOrder.partner_id = null;
        this.state.currentOrder.orderNumber = 'New Order';
        this.state.currentOrder.lines = this.createEmptyLines(10);
        this.calculateTotals();
    }
    
    /**
     * Send via WhatsApp
     */
    async sendWhatsApp() {
        this.notification.add(_t("WhatsApp integration - to be implemented"), { type: "info" });
    }
}

