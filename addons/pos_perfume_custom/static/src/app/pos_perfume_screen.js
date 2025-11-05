/** @odoo-module */

import { Component, useState, useRef, onMounted, useEnv } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
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
                order_id: null,  // ID of loaded order if editing
                partner: null,
                partner_id: null,
                pricelist_id: null,
                orderNumber: 'New Order',
                lines: [],
                totals: {
                    subtotal: 0,
                    discount: 0,
                    tax: 0,
                    total_usd: 0,
                    total_iqd: 0,
                }
            },
            
            // Right panel search
            rightSearchTerm: '',
            rightSearchResults: [],
            rightSearchLoading: false,
            selectedRightProduct: null,
            selectedRightProductIndex: 0,
            
            // UI state
            exchangeRate: 1300,
            
            // Navigation state for keyboard controls
            focusedCell: {
                row: 0,  // Current row index
                col: 0,  // Current column index (0=Product, 1=Quantity, 2=UoM, 3=Warehouse, 4=Disc%)
            },
        });
        
        // Initialize lines after state is created
        this.state.currentOrder.lines = this.createEmptyLines(10);
        
        // Debounce timer for search
        this.searchTimers = {};
        this.rightSearchTimer = null;
        
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
            
            // Set default pricelist to "Price list 1" (fixed)
            if (pricelists.length > 0 && !this.state.currentOrder.pricelist_id) {
                // Try to find "Price list 1" - case insensitive and flexible search
                let defaultPricelist = pricelists.find(p => 
                    p.name && (
                        p.name.toLowerCase() === 'price list 1' ||
                        p.name.toLowerCase().includes('price list 1') ||
                        p.name.toLowerCase() === 'list 1' ||
                        p.name.toLowerCase().includes('list 1')
                    )
                );
                
                // If not found, try "Public Pricelist" or "Default"
                if (!defaultPricelist) {
                    defaultPricelist = pricelists.find(p => 
                        p.name && (
                            p.name.toLowerCase() === 'public pricelist' ||
                            p.name.toLowerCase().includes('public') ||
                            p.name.toLowerCase() === 'default'
                        )
                    );
                }
                
                // If still not found, use first one
                if (!defaultPricelist) {
                    defaultPricelist = pricelists[0];
                }
                
                this.state.currentOrder.pricelist_id = defaultPricelist.id;
                
                console.log(`Default pricelist fixed to: ${defaultPricelist.name} (ID: ${defaultPricelist.id})`);
                
                // Log all available pricelists for debugging
                console.log('Available pricelists:', pricelists.map(p => `${p.name} (ID: ${p.id})`));
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
            uomName: '',  // Store UoM name for display
            uomValid: false,  // Validation flag
            selectedUomIndex: 0,  // For keyboard navigation
            availableUoms: [],
            showUomDropdown: false,
            filteredUoms: [],
            warehouse_id: null,
            warehouseCode: '',  // Store warehouse code for display
            warehouseValid: false,  // Validation flag
            selectedWarehouseIndex: 0,  // For keyboard navigation
            availableWarehouses: [],
            showWarehouseDropdown: false,
            filteredWarehouses: [],
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
     * Check if Product is selected
     */
    isProductSelected(lineIndex, product, line) {
        const searchResults = line.searchResults || [];
        const selectedIndex = line.selectedProductIndex || 0;
        const productIndex = searchResults.findIndex(p => p.id === product.id);
        return productIndex === selectedIndex;
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
        
        // Load complete product info (UoMs + Warehouses + Prices)
        await this.loadProductInfo(lineIndex, product.id);
        
        // Focus on quantity field (column 1) after product is selected
        setTimeout(() => {
            this.focusCell(lineIndex, 1);
        }, 100);
        
        this.notification.add(
            _t('Product selected: ') + product.name,
            { type: 'success' }
        );
    }
    
    /**
     * Load complete product info using onchange controller (like Sale Order)
     */
    async loadProductInfo(lineIndex, productId) {
        const line = this.state.currentOrder.lines[lineIndex];
        const pricelistId = this.state.currentOrder.pricelist_id;
        const uomId = line.uom_id || null;
        const warehouseId = line.warehouse_id || null;
        
        try {
            console.log(`🔍 Loading product ${productId} with pricelist ${pricelistId}`);
            
            // Call controller that uses onchange (exactly like sale.order.line)
            const result = await rpc('/pos_perfume/get_product_data', {
                product_id: productId,
                pricelist_id: pricelistId,
                uom_id: uomId,
                warehouse_id: warehouseId,
            });
            
            console.log('📦 Product data received:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to load product data');
            }
            
            const data = result.data;
            
            // Set UoMs
            line.availableUoms = data.available_uoms || [];
            
            // Set warehouses
            line.availableWarehouses = data.warehouses || [];
            
            // Set default values from onchange
            line.uom_id = data.product_uom_id;
            line.unitPrice = data.price_unit || 0;
            
            // Set UoM name and validate
            if (data.product_uom_name) {
                line.uomName = data.product_uom_name;
                line.uomValid = true;
            } else if (line.availableUoms.length > 0) {
                const defaultUom = line.availableUoms.find(u => u.id === data.product_uom_id || u.uom_id === data.product_uom_id);
                if (defaultUom) {
                    line.uomName = defaultUom.name;
                    line.uomValid = true;
                }
            }
            
            // Set default warehouse and validate
            if (line.availableWarehouses.length > 0) {
                line.warehouse_id = line.availableWarehouses[0].id;
                line.availableQty = line.availableWarehouses[0].quantity;
                line.warehouseCode = line.availableWarehouses[0].code || (line.availableWarehouses[0].name ? line.availableWarehouses[0].name.split(' ')[0] : '');
                line.warehouseValid = true;
            } else {
                line.warehouse_id = null;
                line.warehouseCode = '';
                line.warehouseValid = false;
                line.availableQty = data.available_qty || 0;
            }
            
            // Calculate line
            this.calculateLine(line);
            
            console.log('✅ Line updated successfully:', {
                uom: `${line.uom_id} - ${data.product_uom_name}`,
                price: line.unitPrice,
                warehouse: line.warehouse_id,
                qty: line.availableQty,
                uoms_count: line.availableUoms.length,
                warehouses_count: line.availableWarehouses.length
            });
            
        } catch (error) {
            console.error('❌ Error loading product info:', error);
            this.notification.add(
                _t('Error loading product: ') + error.message,
                { type: 'danger' }
            );
            
            // Set defaults
            line.availableUoms = [];
            line.availableWarehouses = [];
            line.unitPrice = 0;
        }
    }
    
    /**
     * Load available UoMs with prices from pricelist (DEPRECATED - use loadProductInfo)
     */
    async loadAvailableUoms(lineIndex, productId) {
        console.warn('loadAvailableUoms is deprecated, use loadProductInfo instead');
        return this.loadProductInfo(lineIndex, productId);
    }
    
    /**
     * Load available warehouses with stock (DEPRECATED - use loadProductInfo)
     */
    async loadAvailableWarehouses(lineIndex, productId) {
        console.warn('loadAvailableWarehouses is deprecated, use loadProductInfo instead');
        // Already loaded by loadProductInfo
        return Promise.resolve();
    }
    
    /**
     * Handle UoM change - recalculate price using onchange
     */
    async onUomChange(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const selectedUomId = parseInt(line.uom_id);
        
        console.log(`[UoM Change] Line ${lineIndex}: UoM changed to ${selectedUomId}`);
        console.log(`[UoM Change] Available UoMs:`, line.availableUoms);
        
        // First, check if we have the price in availableUoms
        const selectedUom = line.availableUoms.find(uom => uom.id === selectedUomId);
        
        if (selectedUom) {
            console.log(`[UoM Change] Found in cache: ${selectedUom.name} = $${selectedUom.price}`);
            line.unitPrice = selectedUom.price;
            line.uomName = selectedUom.name; // Store UoM name
            this.calculateLine(line);
            this.calculateTotals();
        } else {
            // Call controller to get price using onchange
            console.log(`[UoM Change] Not in cache, calling RPC...`);
            try {
                const result = await rpc('/pos_perfume/onchange_uom', {
                    product_id: line.product_id,
                    pricelist_id: this.state.currentOrder.pricelist_id,
                    uom_id: selectedUomId,
                });
                
                console.log(`[UoM Change] RPC result:`, result);
                
                if (result.success) {
                    line.unitPrice = result.price_unit;
                    this.calculateLine(line);
                    this.calculateTotals();
                }
            } catch (error) {
                console.error('[UoM Change] Error:', error);
            }
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
            line.warehouseCode = selectedWh.code || (selectedWh.name ? selectedWh.name.split(' ')[0] : ''); // Store warehouse code
        }
    }
    
    /**
     * Handle pricelist change - DISABLED: Keep fixed to "Price list 1"
     */
    async onPricelistChange() {
        // DISABLED: Keep pricelist fixed to "Price list 1"
        // Reset to "Price list 1" if user tries to change it
        const priceList1 = this.state.pricelists.find(p => 
            p.name && (
                p.name.toLowerCase() === 'price list 1' ||
                p.name.toLowerCase().includes('price list 1') ||
                p.name.toLowerCase() === 'list 1' ||
                p.name.toLowerCase().includes('list 1')
            )
        );
        if (priceList1 && this.state.currentOrder.pricelist_id !== priceList1.id) {
            this.state.currentOrder.pricelist_id = priceList1.id;
            this.notification.add(
                _t(`Pricelist is fixed to "${priceList1.name}"`),
                { type: 'info' }
            );
            return;
        }
        // Reload product info for all lines that have products
        for (let i = 0; i < this.state.currentOrder.lines.length; i++) {
            const line = this.state.currentOrder.lines[i];
            if (line.product_id) {
                await this.loadProductInfo(i, line.product_id);
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
     * Handle Price IQD input - convert IQD to USD
     */
    onPriceIqdInput(ev, lineIndex) {
        const iqdValue = parseFloat(ev.target.value) || 0;
        const usdValue = iqdValue / this.state.exchangeRate;
        this.updateLine(lineIndex, 'unitPrice', usdValue);
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
     * Delete order line - Remove completely and renumber rows
     */
    deleteLine(lineIndex) {
        // Remove the line completely
        this.state.currentOrder.lines.splice(lineIndex, 1);
        
        // Renumber all rows
        this.state.currentOrder.lines.forEach((line, index) => {
            line.rowNumber = index + 1;
        });
        
        // If we deleted the last line, add a new empty line
        if (this.state.currentOrder.lines.length < 10) {
            const newLine = this.createEmptyLine(this.state.currentOrder.lines.length + 1);
            this.state.currentOrder.lines.push(newLine);
        }
        
        this.calculateTotals();
        this.notification.add(_t("Line deleted"), { type: "info" });
    }
    
    /**
     * Get UoM name from ID
     */
    getUomName(uomId, availableUoms) {
        if (!uomId || !availableUoms) return '';
        const uom = availableUoms.find(u => u.id === uomId || u.uom_id === uomId);
        return uom ? uom.name : '';
    }
    
    /**
     * Get warehouse code from ID
     */
    getWarehouseCode(warehouseId, availableWarehouses) {
        if (!warehouseId || !availableWarehouses) return '';
        const wh = availableWarehouses.find(w => w.id === warehouseId);
        if (!wh) return '';
        // Return code if available, otherwise extract code from name
        return wh.code || (wh.name ? wh.name.split(' ')[0] : '');
    }
    
    /**
     * Handle UoM input with autocomplete
     */
    async onUomInput(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const searchTerm = ev.target.value;
        
        // Reset selected index
        line.selectedUomIndex = 0;
        
        // Update uomName temporarily
        line.uomName = searchTerm;
        line.uomValid = false; // Mark as invalid until validated
        
        if (!searchTerm || !searchTerm.trim()) {
            line.showUomDropdown = false;
            line.uom_id = null;
            return;
        }
        
        // Show dropdown if there are available UoMs
        if (line.availableUoms && line.availableUoms.length > 0) {
            line.showUomDropdown = true;
            // Filter UoMs based on search term
            line.filteredUoms = line.availableUoms.filter(uom => 
                uom.name.toLowerCase().includes(searchTerm.toLowerCase())
            );
            
            // Auto-select if exact match
            const exactMatch = line.availableUoms.find(uom => 
                uom.name.toLowerCase() === searchTerm.toLowerCase()
            );
            if (exactMatch) {
                line.uom_id = exactMatch.id || exactMatch.uom_id;
                line.uomName = exactMatch.name;
                line.uomValid = true;
            }
        }
    }
    
    /**
     * Handle UoM keyboard navigation
     */
    handleUomKeyDown(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        if (!line.showUomDropdown || !line.filteredUoms || line.filteredUoms.length === 0) {
            // If no dropdown, handle table navigation
            this.handleTableKeyDown(ev, lineIndex, 2);
            return;
        }
        
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            line.selectedUomIndex = Math.min(
                (line.selectedUomIndex || 0) + 1,
                line.filteredUoms.length - 1
            );
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            line.selectedUomIndex = Math.max((line.selectedUomIndex || 0) - 1, 0);
        } else if (ev.key === 'Enter') {
            ev.preventDefault();
            if (line.filteredUoms[line.selectedUomIndex || 0]) {
                this.selectUom(lineIndex, line.filteredUoms[line.selectedUomIndex || 0]);
            }
        } else if (ev.key === 'Escape') {
            line.showUomDropdown = false;
        } else {
            // For other keys, handle table navigation
            this.handleTableKeyDown(ev, lineIndex, 2);
        }
    }
    
    /**
     * Validate UoM on blur
     */
    validateUom(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const inputValue = ev.target.value.trim();
        
        if (!inputValue) {
            line.uomName = '';
            line.uom_id = null;
            line.uomValid = false;
            return;
        }
        
        // Check if the value matches any available UoM
        const availableUoms = line.filteredUoms || line.availableUoms || [];
        const matchedUom = availableUoms.find(uom => 
            uom.name.toLowerCase() === inputValue.toLowerCase()
        );
        
        if (matchedUom) {
            line.uom_id = matchedUom.id || matchedUom.uom_id;
            line.uomName = matchedUom.name;
            line.uomValid = true;
            // Update price if needed
            this.onUomChange(lineIndex);
        } else {
            // Invalid value - show error or revert to last valid
            if (line.uomValid && line.uomName) {
                ev.target.value = line.uomName; // Revert to last valid
            } else {
                line.uomName = '';
                line.uom_id = null;
                ev.target.value = '';
                this.notification.add(_t("Invalid UoM. Please select from dropdown."), { type: "warning" });
            }
            line.uomValid = false;
        }
        
        line.showUomDropdown = false;
    }
    
    /**
     * Handle UoM focus
     */
    onUomFocus(ev, lineIndex) {
        ev.target.select();
        this.setFocusedCell(lineIndex, 2);
        const line = this.state.currentOrder.lines[lineIndex];
        if (line.product_id) {
            this.showUomDropdown(lineIndex);
        }
    }
    
    /**
     * Show UoM dropdown
     */
    showUomDropdown(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        if (line.availableUoms && line.availableUoms.length > 0) {
            line.showUomDropdown = true;
            line.filteredUoms = line.availableUoms;
        }
    }
    
    /**
     * Hide UoM dropdown
     */
    hideUomDropdown(lineIndex) {
        setTimeout(() => {
            const line = this.state.currentOrder.lines[lineIndex];
            if (line) {
                line.showUomDropdown = false;
            }
        }, 200);
    }
    
    /**
     * Check if UoM is selected
     */
    isUomSelected(lineIndex, uom, line) {
        const filteredUoms = line.filteredUoms || line.availableUoms || [];
        const selectedIndex = line.selectedUomIndex || 0;
        const uomIndex = filteredUoms.findIndex(u => (u.id || u.uom_id) === (uom.id || uom.uom_id));
        return uomIndex === selectedIndex;
    }
    
    /**
     * Select UoM from dropdown
     */
    async selectUom(lineIndex, uom) {
        const line = this.state.currentOrder.lines[lineIndex];
        line.uom_id = uom.id || uom.uom_id;
        line.uomName = uom.name;
        line.uomValid = true;
        line.showUomDropdown = false;
        line.selectedUomIndex = 0;
        
        // Update price and recalculate
        await this.onUomChange(lineIndex);
    }
    
    /**
     * Handle Warehouse input with autocomplete
     */
    async onWarehouseInput(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const searchTerm = ev.target.value;
        
        // Reset selected index
        line.selectedWarehouseIndex = 0;
        
        // Update warehouseCode temporarily
        line.warehouseCode = searchTerm;
        line.warehouseValid = false; // Mark as invalid until validated
        
        if (!searchTerm || !searchTerm.trim()) {
            line.showWarehouseDropdown = false;
            line.warehouse_id = null;
            return;
        }
        
        // Show dropdown if there are available warehouses
        if (line.availableWarehouses && line.availableWarehouses.length > 0) {
            line.showWarehouseDropdown = true;
            // Filter warehouses based on search term
            line.filteredWarehouses = line.availableWarehouses.filter(wh => {
                const code = wh.code || (wh.name ? wh.name.split(' ')[0] : '');
                const name = wh.name || '';
                return code.toLowerCase().includes(searchTerm.toLowerCase()) || 
                       name.toLowerCase().includes(searchTerm.toLowerCase());
            });
            
            // Auto-select if exact match by code
            const exactMatch = line.availableWarehouses.find(wh => {
                const code = wh.code || (wh.name ? wh.name.split(' ')[0] : '');
                return code.toLowerCase() === searchTerm.toLowerCase();
            });
            if (exactMatch) {
                line.warehouse_id = exactMatch.id;
                line.warehouseCode = exactMatch.code || (exactMatch.name ? exactMatch.name.split(' ')[0] : '');
                line.warehouseValid = true;
                this.onWarehouseChange(lineIndex);
            }
        }
    }
    
    /**
     * Handle Warehouse keyboard navigation
     */
    handleWarehouseKeyDown(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        if (!line.showWarehouseDropdown || !line.filteredWarehouses || line.filteredWarehouses.length === 0) {
            // If no dropdown, handle table navigation
            this.handleTableKeyDown(ev, lineIndex, 3);
            return;
        }
        
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            line.selectedWarehouseIndex = Math.min(
                (line.selectedWarehouseIndex || 0) + 1,
                line.filteredWarehouses.length - 1
            );
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            line.selectedWarehouseIndex = Math.max((line.selectedWarehouseIndex || 0) - 1, 0);
        } else if (ev.key === 'Enter') {
            ev.preventDefault();
            if (line.filteredWarehouses[line.selectedWarehouseIndex || 0]) {
                this.selectWarehouse(lineIndex, line.filteredWarehouses[line.selectedWarehouseIndex || 0]);
            }
        } else if (ev.key === 'Escape') {
            line.showWarehouseDropdown = false;
        } else {
            // For other keys, handle table navigation
            this.handleTableKeyDown(ev, lineIndex, 3);
        }
    }
    
    /**
     * Validate Warehouse on blur
     */
    validateWarehouse(ev, lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const inputValue = ev.target.value.trim();
        
        if (!inputValue) {
            line.warehouseCode = '';
            line.warehouse_id = null;
            line.warehouseValid = false;
            return;
        }
        
        // Check if the value matches any available warehouse
        const availableWarehouses = line.filteredWarehouses || line.availableWarehouses || [];
        const matchedWh = availableWarehouses.find(wh => {
            const code = wh.code || (wh.name ? wh.name.split(' ')[0] : '');
            return code.toLowerCase() === inputValue.toLowerCase();
        });
        
        if (matchedWh) {
            line.warehouse_id = matchedWh.id;
            line.warehouseCode = matchedWh.code || (matchedWh.name ? matchedWh.name.split(' ')[0] : '');
            line.warehouseValid = true;
            this.onWarehouseChange(lineIndex);
        } else {
            // Invalid value - show error or revert to last valid
            if (line.warehouseValid && line.warehouseCode) {
                ev.target.value = line.warehouseCode; // Revert to last valid
            } else {
                line.warehouseCode = '';
                line.warehouse_id = null;
                ev.target.value = '';
                this.notification.add(_t("Invalid Warehouse. Please select from dropdown."), { type: "warning" });
            }
            line.warehouseValid = false;
        }
        
        line.showWarehouseDropdown = false;
    }
    
    /**
     * Handle Warehouse focus
     */
    onWarehouseFocus(ev, lineIndex) {
        ev.target.select();
        this.setFocusedCell(lineIndex, 3);
        const line = this.state.currentOrder.lines[lineIndex];
        if (line.product_id) {
            this.showWarehouseDropdown(lineIndex);
        }
    }
    
    /**
     * Show Warehouse dropdown
     */
    showWarehouseDropdown(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        if (line.availableWarehouses && line.availableWarehouses.length > 0) {
            line.showWarehouseDropdown = true;
            line.filteredWarehouses = line.availableWarehouses;
        }
    }
    
    /**
     * Hide Warehouse dropdown
     */
    hideWarehouseDropdown(lineIndex) {
        setTimeout(() => {
            const line = this.state.currentOrder.lines[lineIndex];
            if (line) {
                line.showWarehouseDropdown = false;
            }
        }, 200);
    }
    
    /**
     * Check if Warehouse is selected
     */
    isWarehouseSelected(lineIndex, warehouse, line) {
        const filteredWarehouses = line.filteredWarehouses || line.availableWarehouses || [];
        const selectedIndex = line.selectedWarehouseIndex || 0;
        const whIndex = filteredWarehouses.findIndex(wh => wh.id === warehouse.id);
        return whIndex === selectedIndex;
    }
    
    /**
     * Select Warehouse from dropdown
     */
    async selectWarehouse(lineIndex, warehouse) {
        const line = this.state.currentOrder.lines[lineIndex];
        line.warehouse_id = warehouse.id;
        line.warehouseCode = warehouse.code || (warehouse.name ? warehouse.name.split(' ')[0] : '');
        line.warehouseValid = true;
        line.showWarehouseDropdown = false;
        line.selectedWarehouseIndex = 0;
        
        // Update available quantity
        await this.onWarehouseChange(lineIndex);
    }
    
    /**
     * Set focused cell for navigation
     */
    setFocusedCell(row, col) {
        this.state.focusedCell.row = row;
        this.state.focusedCell.col = col;
    }
    
    /**
     * Handle table keyboard navigation
     */
    handleTableKeyDown(ev, rowIndex, colIndex) {
        const lines = this.state.currentOrder.lines;
        const maxRow = lines.length - 1;
        const maxCol = 7; // 0=Product, 1=Quantity, 2=UoM, 3=Warehouse, 4=Available, 5=Price USD, 6=Price IQD, 7=Disc%
        
        // Arrow keys for navigation
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            const nextRow = Math.min(rowIndex + 1, maxRow);
            this.focusCell(nextRow, colIndex);
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            const nextRow = Math.max(rowIndex - 1, 0);
            this.focusCell(nextRow, colIndex);
        } else if (ev.key === 'ArrowRight') {
            ev.preventDefault();
            const nextCol = Math.min(colIndex + 1, maxCol);
            this.focusCell(rowIndex, nextCol);
        } else if (ev.key === 'ArrowLeft') {
            ev.preventDefault();
            const nextCol = Math.max(colIndex - 1, 0);
            this.focusCell(rowIndex, nextCol);
        } else if (ev.key === '+' || ev.key === '=') {
            ev.preventDefault();
            // Focus on main search (right panel)
            const rightSearchInput = document.getElementById('right-search-input') || 
                                     document.querySelector('input[t-model="state.rightSearchTerm"]');
            if (rightSearchInput) {
                rightSearchInput.focus();
                rightSearchInput.select();
            }
        } else if (ev.key === 'Delete') {
            // Delete key to delete line (when focused on a cell)
            ev.preventDefault();
            this.deleteLine(rowIndex);
        }
    }
    
    /**
     * Focus on specific cell
     */
    focusCell(rowIndex, colIndex) {
        // Use setTimeout to ensure DOM is updated
        setTimeout(() => {
            // Find the input element for this cell using data attributes
            const cellSelectors = {
                0: `input[data-row="${rowIndex}"][data-col="0"]`,  // Product
                1: `input[data-row="${rowIndex}"][data-col="1"]`,  // Quantity
                2: `input[data-row="${rowIndex}"][data-col="2"]`,  // UoM
                3: `input[data-row="${rowIndex}"][data-col="3"]`,  // Warehouse
                5: `input[data-row="${rowIndex}"][data-col="5"]`,  // Price USD
                6: `input[data-row="${rowIndex}"][data-col="6"]`,  // Price IQD
                7: `input[data-row="${rowIndex}"][data-col="7"]`,  // Disc%
            };
            
            const selector = cellSelectors[colIndex];
            if (selector) {
                const cell = document.querySelector(selector);
                if (cell) {
                    cell.focus();
                    if (cell.select && typeof cell.select === 'function') {
                        cell.select();
                    }
                    this.setFocusedCell(rowIndex, colIndex);
                }
            }
        }, 10);
    }
    
    /**
     * Handle delete key down for delete button
     */
    handleDeleteKeyDown(ev, lineIndex) {
        if (ev.key === 'Delete') {
            ev.preventDefault();
            this.deleteLine(lineIndex);
        }
    }
    
    /**
     * Handle right search input keydown with navigation
     */
    handleRightSearchKeyDown(ev) {
        const results = this.state.rightSearchResults || [];
        
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            this.state.selectedRightProductIndex = Math.min(
                (this.state.selectedRightProductIndex || 0) + 1,
                results.length - 1
            );
            if (results[this.state.selectedRightProductIndex]) {
                this.state.selectedRightProduct = results[this.state.selectedRightProductIndex].id;
                // Scroll to selected item
                this.scrollToSelectedProduct();
            }
        } else if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            this.state.selectedRightProductIndex = Math.max((this.state.selectedRightProductIndex || 0) - 1, 0);
            if (results[this.state.selectedRightProductIndex]) {
                this.state.selectedRightProduct = results[this.state.selectedRightProductIndex].id;
                // Scroll to selected item
                this.scrollToSelectedProduct();
            }
        } else if (ev.key === 'Enter') {
            ev.preventDefault();
            if (results[this.state.selectedRightProductIndex || 0]) {
                this.addProductFromRightPanel(results[this.state.selectedRightProductIndex || 0]);
            }
        } else if (ev.key === 'Escape') {
            ev.target.blur();
        }
    }
    
    /**
     * Scroll to selected product in right panel
     */
    scrollToSelectedProduct() {
        setTimeout(() => {
            const selectedElement = document.querySelector(`tr[data-product-id="${this.state.selectedRightProduct}"]`);
            if (selectedElement) {
                selectedElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }, 10);
    }
    
    /**
     * Handle global keyboard events for table
     */
    handleGlobalKeyDown(ev) {
        // Handle + key to focus on main search
        if ((ev.key === '+' || ev.key === '=') && !ev.target.matches('input, textarea, select')) {
            ev.preventDefault();
            const rightSearchInput = document.getElementById('right-search-input') || 
                                     document.querySelector('input[t-model="state.rightSearchTerm"]');
            if (rightSearchInput) {
                rightSearchInput.focus();
                rightSearchInput.select();
            }
        }
    }
    
    /**
     * Handle customer selection
     */
    onSelectCustomer(customer) {
        if (customer) {
            this.state.currentOrder.partner = customer.name;
            this.state.currentOrder.partner_id = customer.id;
            
            // DISABLED: Keep pricelist fixed to "Price list 1" - don't change when customer changes
            // if (customer.pricelist_id) {
            //     this.state.currentOrder.pricelist_id = customer.pricelist_id;
            //     this.onPricelistChange();
            // }
            
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
                product_uom_id: line.uom_id,
                warehouse_id: line.warehouse_id,
                quantity: line.quantity,
                unit_price: line.unitPrice,
                discount_percent: line.discountPercent,
            }]);
            
            const targetOrderId = this.state.currentOrder.order_id;
            let orderId;
            
            if (targetOrderId) {
                // Update existing order - ensure targetOrderId is in array
                const orderIds = Array.isArray(targetOrderId) ? targetOrderId : [targetOrderId];
                await this.orm.write('pos.perfume.order', orderIds, {
                    partner_id: this.state.currentOrder.partner_id,
                    pricelist_id: this.state.currentOrder.pricelist_id,
                    exchange_rate: this.state.exchangeRate,
                    order_line_ids: [[5, 0, 0], ...orderLines], // Clear existing lines and add new ones
                    state: state,
                });
                orderId = orderIds[0];
                this.notification.add(_t("Order updated successfully!"), { type: "success" });
            } else {
                // Create new order
                const result = await this.orm.create('pos.perfume.order', [{
                    partner_id: this.state.currentOrder.partner_id,
                    pricelist_id: this.state.currentOrder.pricelist_id,
                    exchange_rate: this.state.exchangeRate,
                    order_line_ids: orderLines,
                    state: state,
                }]);
                // orm.create returns array of IDs
                orderId = Array.isArray(result) ? result[0] : result;
                this.state.currentOrder.order_id = orderId;
                this.notification.add(_t("Order saved successfully!"), { type: "success" });
            }
            
            // Update order number - ensure orderId is in array
            if (orderId) {
                const orderIds = Array.isArray(orderId) ? orderId : [orderId];
                const savedOrder = await this.orm.read('pos.perfume.order', orderIds, ['name']);
                if (savedOrder.length > 0) {
                    this.state.currentOrder.orderNumber = savedOrder[0].name;
                }
            }
            
            return orderId;
        } catch (error) {
            console.error("Error saving order:", error);
            this.notification.add(_t("Failed to save order: ") + error.message, { type: "danger" });
            return false;
        }
    }
    
    /**
     * Create quotation - Creates sale.order in draft state
     */
    async createQuotation() {
        // First save as draft, then update to quotation state
        let orderId = await this.saveOrder('draft');
        console.log('[Quotation] POS Order ID:', orderId);
        
        // Ensure orderId is a number, not array
        if (Array.isArray(orderId)) {
            orderId = orderId[0];
        }
        
        if (orderId) {
            // Update order state to quotation
            try {
                await this.orm.write('pos.perfume.order', [orderId], {
                    state: 'quotation'
                });
            } catch (e) {
                console.warn('Failed to update order state to quotation:', e);
            }
            try {
                // Call action_confirm to create sale.order
                console.log('[Quotation] Calling action_confirm...');
                const result = await this.orm.call('pos.perfume.order', 'action_confirm', [[orderId]]);
                
                console.log('[Quotation] action_confirm result:', result);
                
                if (result && result.res_id) {
                    this.notification.add(_t("Quotation created! Opening sale order..."), { type: "success" });
                    
                    // Open the created sale order - ensure action is properly formatted
                    try {
                        const action = {
                            type: result.type || 'ir.actions.act_window',
                            res_model: result.res_model || 'sale.order',
                            res_id: result.res_id,
                            view_mode: result.view_mode || 'form',
                            views: result.views || [[false, 'form']],
                            target: result.target || 'current',
                        };
                        await this.action.doAction(action);
                    } catch (actionError) {
                        console.error('[Quotation] Error opening sale order:', actionError);
                        // Fallback: open in new window
                        window.open(`/web#id=${result.res_id}&model=sale.order&view_type=form`, '_blank');
                    }
                    
                    this.resetOrder();
                } else {
                    console.warn('[Quotation] No res_id in result:', result);
                    this.notification.add(_t("Quotation created but could not open"), { type: "info" });
                    this.resetOrder();
                }
            } catch (error) {
                console.error('[Quotation] Error:', error);
                this.notification.add(_t("Saved but failed to create sale order: ") + error.message, { type: "warning" });
            }
        }
    }
    
    /**
     * Confirm sale order - Creates and confirms sale.order
     */
    async confirmSaleOrder() {
        const orderId = await this.saveOrder('draft');
        if (orderId) {
            try {
                // Create sale order
                const result = await this.orm.call('pos.perfume.order', 'action_confirm', [[orderId]]);
                
                if (result && result.res_id) {
                    // Confirm the sale order
                    await this.orm.call('sale.order', 'action_confirm', [[result.res_id]]);
                    
                    this.notification.add(_t("Sale order confirmed! Opening..."), { type: "success" });
                    
                    // Open the confirmed sale order - ensure action is properly formatted
                    try {
                        const action = {
                            type: result.type || 'ir.actions.act_window',
                            res_model: result.res_model || 'sale.order',
                            res_id: result.res_id,
                            view_mode: result.view_mode || 'form',
                            views: result.views || [[false, 'form']],
                            target: result.target || 'current',
                        };
                        await this.action.doAction(action);
                    } catch (actionError) {
                        console.error('[Sale Order] Error opening sale order:', actionError);
                        // Fallback: open in new window
                        window.open(`/web#id=${result.res_id}&model=sale.order&view_type=form`, '_blank');
                    }
                    
                    this.resetOrder();
                }
            } catch (error) {
                console.error('Error confirming sale order:', error);
                this.notification.add(_t("Failed to confirm sale order: ") + error.message, { type: "danger" });
            }
        }
    }
    
    /**
     * Save draft - Save in POS Perfume only
     */
    async saveOrderDraft() {
        const orderId = await this.saveOrder('draft');
        if (orderId) {
            this.notification.add(_t("Draft saved in POS Perfume"), { type: "info" });
        }
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
        if (confirm(_t("Are you sure you want to create a new order? Current order will be lost."))) {
            this.state.currentOrder.partner = null;
            this.state.currentOrder.partner_id = null;
            this.state.currentOrder.orderNumber = 'New Order';
            this.state.currentOrder.order_id = null;
            this.state.currentOrder.lines = this.createEmptyLines(10);
            this.calculateTotals();
            this.notification.add(_t("New order created"), { type: "success" });
        }
    }
    
    /**
     * Open previous orders dialog
     */
    async openPreviousOrders() {
        try {
            // Search for recent orders
            const orders = await this.orm.searchRead(
                'pos.perfume.order',
                [
                    ['state', 'in', ['draft', 'quotation']]
                ],
                ['id', 'name', 'partner_id', 'date', 'amount_total', 'state'],
                { 
                    limit: 50, 
                    order: 'date DESC, id DESC' 
                }
            );
            
            if (orders.length === 0) {
                this.notification.add(_t("No previous orders found"), { type: "info" });
                return;
            }
            
            // Show a simple selection dialog
            const orderList = orders.map(o => 
                `${o.name} - ${o.partner_id ? o.partner_id[1] : 'No Customer'} - ${o.date ? new Date(o.date).toLocaleDateString() : ''}`
            ).join('\n');
            
            // Prompt user to enter order ID or name
            const orderInput = prompt(
                _t("Enter order number or name to load:\n\nRecent orders:\n") + 
                orders.slice(0, 10).map((o, i) => `${i + 1}. ${o.name} (${o.id})`).join('\n') +
                '\n\nOr enter the order number:'
            );
            
            if (!orderInput) {
                return;
            }
            
            // Try to find order by name or ID
            let selectedOrder = null;
            
            // Check if input is a number (order ID)
            const orderId = parseInt(orderInput);
            if (!isNaN(orderId)) {
                selectedOrder = orders.find(o => o.id === orderId);
            } else {
                // Search by name
                selectedOrder = orders.find(o => 
                    o.name.toLowerCase().includes(orderInput.toLowerCase()) ||
                    (o.partner_id && o.partner_id[1].toLowerCase().includes(orderInput.toLowerCase()))
                );
            }
            
            if (selectedOrder) {
                await this.loadOrder(selectedOrder.id);
            } else {
                this.notification.add(_t("Order not found"), { type: "warning" });
            }
            
        } catch (error) {
            console.error('Error loading previous orders:', error);
            this.notification.add(_t("Error loading previous orders"), { type: "danger" });
        }
    }
    
    /**
     * Load order by ID
     */
    async loadOrder(orderId) {
        try {
            // Ensure orderId is in array format
            const orderIds = Array.isArray(orderId) ? orderId : [orderId];
            
            const orders = await this.orm.read(
                'pos.perfume.order',
                orderIds,
                ['id', 'name', 'partner_id', 'pricelist_id', 'order_line_ids', 'state', 'amount_total']
            );
            
            if (orders.length === 0) {
                this.notification.add(_t("Order not found"), { type: "warning" });
                return;
            }
            
            const order = orders[0];
            
            // Load order lines - ensure order_line_ids is array
            const lineIds = Array.isArray(order.order_line_ids) ? order.order_line_ids : [];
            const lines = lineIds.length > 0 ? await this.orm.read(
                'pos.perfume.order.line',
                lineIds,
                ['product_id', 'product_uom_id', 'warehouse_id', 'quantity', 'unit_price', 'discount_percent']
            ) : [];
            
            // Update state
            this.state.currentOrder.order_id = order.id;
            this.state.currentOrder.orderNumber = order.name;
            this.state.currentOrder.partner_id = order.partner_id ? order.partner_id[0] : null;
            this.state.currentOrder.pricelist_id = order.pricelist_id ? order.pricelist_id[0] : null;
            
            // Load partner info and update customer search
            if (order.partner_id) {
                const partnerIds = Array.isArray(order.partner_id) ? [order.partner_id[0]] : [order.partner_id];
                const partners = await this.orm.read(
                    'res.partner',
                    partnerIds,
                    ['name', 'phone']
                );
                if (partners.length > 0) {
                    this.state.currentOrder.partner = partners[0].name;
                    // Trigger customer selection callback to update UI
                    this.onSelectCustomer({
                        id: partners[0].id,
                        name: partners[0].name,
                        phone: partners[0].phone,
                    });
                }
            }
            
            // Clear and populate lines
            this.state.currentOrder.lines = this.createEmptyLines(Math.max(lines.length, 10));
            
            // Load lines in parallel for better performance
            const loadPromises = [];
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const uiLine = this.state.currentOrder.lines[i];
                
                if (line.product_id) {
                    const productId = Array.isArray(line.product_id) ? line.product_id[0] : line.product_id;
                    uiLine.product_id = productId;
                    uiLine.productName = Array.isArray(line.product_id) ? line.product_id[1] : '';
                    uiLine.uom_id = line.product_uom_id ? (Array.isArray(line.product_uom_id) ? line.product_uom_id[0] : line.product_uom_id) : null;
                    uiLine.warehouse_id = line.warehouse_id ? (Array.isArray(line.warehouse_id) ? line.warehouse_id[0] : line.warehouse_id) : null;
                    uiLine.quantity = line.quantity;
                    uiLine.unitPrice = line.unit_price;
                    uiLine.discountPercent = line.discount_percent || 0;
                    
                    // Load product info
                    loadPromises.push(this.loadProductInfo(i, productId));
                }
            }
            
            // Wait for all product info to load
            await Promise.all(loadPromises);
            
            this.calculateTotals();
            this.notification.add(_t(`Order ${order.name} loaded successfully`), { type: "success" });
            
        } catch (error) {
            console.error('Error loading order:', error);
            this.notification.add(_t("Error loading order: ") + error.message, { type: "danger" });
        }
    }
    
    /**
     * Send via WhatsApp
     */
    async sendWhatsApp() {
        this.notification.add(_t("WhatsApp integration - to be implemented"), { type: "info" });
    }
    
    /**
     * Search products in right panel
     */
    async searchRightPanel() {
        const searchTerm = this.state.rightSearchTerm;
        
        // Clear timer
        if (this.rightSearchTimer) {
            clearTimeout(this.rightSearchTimer);
        }
        
        if (!searchTerm || searchTerm.length < 2) {
            this.state.rightSearchResults = [];
            return;
        }
        
        // Debounce
        this.rightSearchTimer = setTimeout(async () => {
            this.state.rightSearchLoading = true;
            
            try {
                const pricelistId = this.state.currentOrder.pricelist_id || null;
                
                const products = await this.orm.call(
                    'product.product',
                    'search_products_for_pos',
                    [searchTerm, 50, pricelistId]
                );
                
                console.log(`[Right Panel] Found ${products.length} products with prices and stock`);
                
                this.state.rightSearchResults = products;
                // Reset selection when new results arrive
                this.state.selectedRightProductIndex = 0;
                if (products.length > 0) {
                    this.state.selectedRightProduct = products[0].id;
                } else {
                    this.state.selectedRightProduct = null;
                }
            } catch (error) {
                console.error('Error searching products:', error);
                this.notification.add(_t('Error searching products'), { type: 'danger' });
            } finally {
                this.state.rightSearchLoading = false;
            }
        }, 300);
    }
    
    /**
     * Check if right panel product is selected
     */
    isRightProductSelected(product) {
        return this.state.selectedRightProduct === product.id;
    }
    
    /**
     * Add product from right panel
     */
    async addProductFromRightPanel(product) {
        // Find empty line
        let line = this.state.currentOrder.lines.find(l => !l.product_id);
        
        if (!line) {
            // Add new line
            const newLine = this.createEmptyLine(this.state.currentOrder.lines.length + 1);
            this.state.currentOrder.lines.push(newLine);
            line = newLine;
        }
        
        // Set product
        line.product_id = product.id;
        line.productName = product.name;
        
        const lineIndex = this.state.currentOrder.lines.indexOf(line);
        
        // Load UoMs and warehouses
        await Promise.all([
            this.loadAvailableUoms(lineIndex, product.id),
            this.loadAvailableWarehousesFromProduct(lineIndex, product)
        ]);
        
        // Load product info
        await this.loadProductInfo(lineIndex, product.id);
        
        // Clear search and reset selection
        this.state.rightSearchTerm = '';
        this.state.rightSearchResults = [];
        this.state.selectedRightProduct = null;
        this.state.selectedRightProductIndex = 0;
        
        // Focus on the product line (Quantity field)
        setTimeout(() => {
            this.focusCell(lineIndex, 1); // Focus on Quantity field (column 1)
        }, 100);
        
        this.notification.add(
            _t('Product added: ') + product.name,
            { type: 'success' }
        );
    }
    
    /**
     * Load warehouses from product data (from right panel)
     */
    async loadAvailableWarehousesFromProduct(lineIndex, product) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        line.availableWarehouses = product.warehouses || [];
        
        // Set default warehouse
        if (line.availableWarehouses.length > 0) {
            line.warehouse_id = line.availableWarehouses[0].id;
            line.availableQty = line.availableWarehouses[0].quantity;
        }
    }
}

