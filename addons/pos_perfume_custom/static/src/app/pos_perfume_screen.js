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
        
        // Create handler cache for template
        this._handlerCache = new Map();
        
        this.state = useState({
            // UI Header state
            userName: 'Cashier',
            currentDate: new Date().toLocaleDateString(),
            currentTime: new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'}),
            
            // Pricelists
            pricelists: [],
            pricelistSearchTerm: '',
            showPricelistDropdown: false,
            
            // Order state
            currentOrder: {
                order_id: null,  // ID of loaded order if editing
                partner: null,
                partner_id: null,
                pricelist_id: null,
                orderNumber: 'New Order',
                sap_doc_num: null,
                sap_doc_entry: null,
                sap_synced: false,
                invoice_type: null,  // Invoice type for SAP
                note: '',  // Notes field
                lines: [],
                totals: {
                    subtotal: 0,
                    discount: 0,
                    tax: 0,
                    total_usd: 0,
                    total_iqd: 0,
                }
            },
            
            // Previous orders navigation
            previousOrders: [],
            currentOrderIndex: -1,
            showPreviousOrdersDialog: false,
            previousOrdersSearchTerm: '',
            filteredPreviousOrders: [],
            orderNumberSearch: '',
            sapDocSearch: '',
            
            // Right panel search
            rightSearchTerm: '',
            rightSearchResults: [],
            rightSearchResultsOriginal: [],  // Original results before filtering
            rightSearchLoading: false,
            selectedRightProduct: null,
            selectedRightProductIndex: 0,
            
            // Filter state
            activeFilters: [],              // Array of active brand filters
            activeUnitFilter: null,         // Active unit filter object or null
            fullPlasticFilterActive: null,  // true/false/null for full plastic filter
            csLocFilterActive: false,  // true to show CS/LOC products, false to hide them
            
            // UI state
            exchangeRate: 1300,
            
            // Navigation state for keyboard controls
            focusedCell: {
                row: 0,  // Current row index
                col: 0,  // Current column index (0=Product, 1=Quantity, 2=UoM, 3=Warehouse, 4=Disc%)
            },
            
            // Custom notifications (top center, accumulating)
            customNotifications: [],
        });
        
        // Initialize lines after state is created
        this.state.currentOrder.lines = this.createEmptyLines(10);
        
        // Add computed property for customer ID (for CustomerSearch component)
        // Initialize as null, will be updated when partner_id changes
        this.state.currentOrder.customerIdForSearch = null;
        
        // Helper to update customerIdForSearch when partner_id changes
        this._updateCustomerIdForSearch = () => {
            const partnerId = this.state.currentOrder.partner_id;
            if (!partnerId) {
                this.state.currentOrder.customerIdForSearch = null;
            } else if (typeof partnerId === 'number') {
                this.state.currentOrder.customerIdForSearch = partnerId;
            } else if (Array.isArray(partnerId)) {
                this.state.currentOrder.customerIdForSearch = partnerId[0] ? Number(partnerId[0]) : null;
            } else {
                this.state.currentOrder.customerIdForSearch = Number(partnerId) || null;
            }
        };
        
        // Debounce timer for search
        this.searchTimers = {};
        this.rightSearchTimer = null;
        
        // Notification counter for unique IDs
        this.notificationCounter = 0;
        
        // Override notification.add to use custom notifications (after state is created)
        const originalNotificationAdd = this.notification.add.bind(this.notification);
        this.notification.add = (message, options = {}) => {
            const type = options.type || 'info';
            this.addCustomNotification(message, type);
            // Optionally keep original notification too
            // originalNotificationAdd(message, options);
        };
        
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
            customProductName: null,  // Custom product name for invoice/report
            showEditProductNamePopup: false,  // Show edit product name popup
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
     * Get display name for product (merge with foreign_name if code starts with S)
     */
    getProductDisplayName(productName, foreignName, defaultCode) {
        // If code starts with S, merge name with foreign_name
        if (defaultCode && defaultCode.toUpperCase().startsWith('S')) {
            if (foreignName && foreignName.trim()) {
                return `${productName} ${foreignName}`;
            }
        }
        return productName;
    }
    
    /**
     * Check if a field can be edited based on validation rules
     * Fields are enabled sequentially - each field requires previous field to be completed
     * Sequential order: Product → Quantity → UoM → Warehouse → Price/Discount
     * Also: Next line's product field is disabled until current line is fully completed
     */
    isFieldEnabled(line, fieldName) {
        const lines = this.state.currentOrder.lines;
        const currentIndex = lines.findIndex(l => l.id === line.id);
        
        // STRICT SEQUENTIAL MODE: Only ONE line can be active at a time
        // Check if previous line is complete before enabling ANY field in current line
        
        // First, check if this is NOT the first line
        if (currentIndex > 0) {
            const previousLine = lines[currentIndex - 1];
            
            if (!previousLine) {
                return false; // Safety check
            }
            
            // Previous line must be FULLY complete before ANY field in current line is enabled
            const isPreviousComplete = !!(
                previousLine.product_id && 
                previousLine.quantity && 
                previousLine.quantity > 0 &&
                previousLine.uom_id && 
                previousLine.uomValid !== false &&
                previousLine.warehouse_id && 
                previousLine.warehouseValid !== false
            );
            
            // If previous line is NOT complete, ALL fields in current line are disabled
            if (!isPreviousComplete) {
                if (fieldName === 'product') {
                    console.log(`🔒 Line ${currentIndex + 1} LOCKED. Previous line ${currentIndex} must be completed first.`, {
                        previousLine: {
                            product_id: previousLine.product_id,
                            quantity: previousLine.quantity,
                            uom_id: previousLine.uom_id,
                            uomValid: previousLine.uomValid,
                            warehouse_id: previousLine.warehouse_id,
                            warehouseValid: previousLine.warehouseValid
                        }
                    });
                }
                return false; // Block ALL fields in this line
            }
        }
        
        // Now check field-specific requirements within the CURRENT line
        
        // Product field: If we reached here, previous line is complete (or this is line 1)
        if (fieldName === 'product') {
            return true;
        }
        
        // Quantity requires product to be selected in CURRENT line
        if (fieldName === 'quantity') {
            return !!line.product_id;
        }
        
        // UoM requires product AND quantity to be entered
        if (fieldName === 'uom') {
            return !!(line.product_id && line.quantity && line.quantity > 0);
        }
        
        // Warehouse requires product, quantity, AND valid UoM to be selected
        if (fieldName === 'warehouse') {
            return !!(line.product_id && line.quantity && line.quantity > 0 && 
                      line.uom_id && line.uomValid);
        }
        
        // Price (USD) requires product, quantity, valid UoM, AND valid warehouse
        if (fieldName === 'price_usd') {
            return !!(line.product_id && line.quantity && line.quantity > 0 && 
                      line.uom_id && line.uomValid && 
                      line.warehouse_id && line.warehouseValid);
        }
        
        // Price (IQD) requires product, quantity, valid UoM, AND valid warehouse
        if (fieldName === 'price_iqd') {
            return !!(line.product_id && line.quantity && line.quantity > 0 && 
                      line.uom_id && line.uomValid && 
                      line.warehouse_id && line.warehouseValid);
        }
        
        // Discount requires product, quantity, valid UoM, AND valid warehouse
        if (fieldName === 'discount') {
            return !!(line.product_id && line.quantity && line.quantity > 0 && 
                      line.uom_id && line.uomValid && 
                      line.warehouse_id && line.warehouseValid);
        }
        
        return true;
    }
    
    /**
     * Get default warehouse from available warehouses list
     * Priority: Warehouse ID 18 > Warehouse with highest quantity > First warehouse
     */
    getDefaultWarehouse(availableWarehouses) {
        if (!availableWarehouses || availableWarehouses.length === 0) {
            console.warn('⚠️ No warehouses available');
            return null;
        }
        
        // Log all available warehouses to debug
        console.log('🏭 Available warehouses for selection:', availableWarehouses.map(w => ({
            id: w.id,
            code: w.code,
            name: w.name,
            quantity: w.quantity || w.qty || 0
        })));
        
        // Priority 1: Try to find Warehouse ID 18
        const wh18 = availableWarehouses.find(w => w.id === 18);
        
        if (wh18) {
            console.log('✅ Found Warehouse ID 18! Selecting it as default:', {
                id: wh18.id,
                code: wh18.code,
                name: wh18.name,
                quantity: wh18.quantity || wh18.qty || 0
            });
            return wh18;
        } else {
            console.warn('⚠️ Warehouse ID 18 NOT found in available warehouses');
        }
        
        // Priority 2: Find warehouse with highest quantity
        const sortedByQuantity = [...availableWarehouses].sort((a, b) => {
            const qtyA = a.quantity || a.qty || 0;
            const qtyB = b.quantity || b.qty || 0;
            return qtyB - qtyA; // Descending order
        });
            
        if (sortedByQuantity.length > 0 && (sortedByQuantity[0].quantity || sortedByQuantity[0].qty || 0) > 0) {
            console.log('✅ Selected warehouse with highest quantity:', {
                id: sortedByQuantity[0].id,
                code: sortedByQuantity[0].code,
                name: sortedByQuantity[0].name,
                quantity: sortedByQuantity[0].quantity || sortedByQuantity[0].qty || 0
            });
            return sortedByQuantity[0];
        }
        
        // Fallback to first warehouse
        console.log('ℹ️ Using first warehouse as fallback:', {
            id: availableWarehouses[0].id,
            code: availableWarehouses[0].code,
            name: availableWarehouses[0].name,
            quantity: availableWarehouses[0].quantity || availableWarehouses[0].qty || 0
        });
        return availableWarehouses[0];
    }
    
    /**
     * Select product from dropdown
     */
    async selectProduct(lineIndex, product) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        line.product_id = product.id;
        
        // Save color and badge info
        line.color_class = product.color_class || '';
        line.badge_text = product.badge_text || '';
        line.default_code = product.default_code || '';
        line.foreign_name = product.foreign_name || '';
        
        // Get display name (merge with foreign_name if code starts with S)
        line.productName = this.getProductDisplayName(
            product.name, 
            product.foreign_name, 
            product.default_code
        );
        
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
     * Load product info with saved values (preserve UoM, Warehouse, Price)
     */
    async loadProductInfoWithSavedValues(lineIndex, productId, savedUomId, savedWarehouseId, savedPrice) {
        const line = this.state.currentOrder.lines[lineIndex];
        const pricelistId = this.state.currentOrder.pricelist_id;
        
        try {
            // Call controller to get available UoMs and Warehouses
            const result = await rpc('/pos_perfume/get_product_data', {
                product_id: productId,
                pricelist_id: pricelistId,
                uom_id: savedUomId,  // Use saved UoM
                warehouse_id: savedWarehouseId,  // Use saved Warehouse
            });
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to load product data');
            }
            
            const data = result.data;
            
            // Set available UoMs and Warehouses
            line.availableUoms = data.available_uoms || [];
            line.availableWarehouses = data.warehouses || [];
            
            // Save color and badge info from product data
            line.color_class = data.color_class || '';
            line.badge_text = data.badge_text || '';
            line.default_code = data.default_code || '';
            line.foreign_name = data.foreign_name || '';
            
            // Update productName to merge with foreign_name if code starts with S
            if (line.productName && line.default_code) {
                line.productName = this.getProductDisplayName(
                    data.product_name || line.productName,
                    line.foreign_name,
                    line.default_code
                );
            }
            
            // Set UoM name from saved UoM
            if (savedUomId && line.availableUoms.length > 0) {
                const savedUom = line.availableUoms.find(u => u.id === savedUomId || u.uom_id === savedUomId);
                if (savedUom) {
                    line.uomName = savedUom.name;
                    line.uomValid = true;
                } else if (data.product_uom_name) {
                    line.uomName = data.product_uom_name;
                    line.uomValid = true;
                }
            } else if (data.product_uom_name) {
                line.uomName = data.product_uom_name;
                line.uomValid = true;
            }
            
            // Set Warehouse code from saved Warehouse
            if (savedWarehouseId && line.availableWarehouses.length > 0) {
                const savedWarehouse = line.availableWarehouses.find(w => w.id === savedWarehouseId);
                if (savedWarehouse) {
                    line.warehouseCode = savedWarehouse.code || (savedWarehouse.name ? savedWarehouse.name.split(' ')[0] : '');
                    line.availableQty = savedWarehouse.quantity;
                    line.warehouseValid = true;
                }
            } else if (line.availableWarehouses.length > 0) {
                // Use default warehouse (WH 18 if available, otherwise first)
                const defaultWarehouse = this.getDefaultWarehouse(line.availableWarehouses);
                if (defaultWarehouse) {
                    line.warehouse_id = defaultWarehouse.id;
                    line.warehouseCode = defaultWarehouse.code || (defaultWarehouse.name ? defaultWarehouse.name.split(' ')[0] : '');
                    line.availableQty = defaultWarehouse.quantity;
                    line.warehouseValid = true;
                }
            } else {
                line.warehouse_id = null;
                line.warehouseCode = '';
                line.warehouseValid = false;
                line.availableQty = data.available_qty || 0;
            }
            
            // Preserve saved price (don't override)
            if (savedPrice && savedPrice > 0) {
                line.unitPrice = savedPrice;
            } else if (data.price_unit) {
                line.unitPrice = data.price_unit;
            }
            
            // Calculate line
            this.calculateLine(line);
            
        } catch (error) {
            console.error('❌ Error loading product info with saved values:', error);
            this.notification.add(
                _t('Error loading product: ') + error.message,
                { type: 'danger' }
            );
            
            // Set defaults
            line.availableUoms = [];
            line.availableWarehouses = [];
            if (!line.unitPrice || line.unitPrice === 0) {
                line.unitPrice = 0;
            }
        }
    }
    
    /**
     * Load complete product info using onchange controller (like Sale Order)
     * With retry logic and timeout handling
     */
    async loadProductInfo(lineIndex, productId, retryCount = 0) {
        const line = this.state.currentOrder.lines[lineIndex];
        const pricelistId = this.state.currentOrder.pricelist_id;
        const uomId = line.uom_id || null;
        const warehouseId = line.warehouse_id || null;
        
        const MAX_RETRIES = 3;
        const TIMEOUT = 30000; // 30 seconds
        
        try {
            console.log(`🔍 Loading product ${productId} with pricelist ${pricelistId} (attempt ${retryCount + 1}/${MAX_RETRIES + 1})`);
            
            // Create a promise with timeout
            const rpcPromise = rpc('/pos_perfume/get_product_data', {
                product_id: productId,
                pricelist_id: pricelistId,
                uom_id: uomId,
                warehouse_id: warehouseId,
            });
            
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Request timeout')), TIMEOUT);
            });
            
            // Call controller with timeout
            const result = await Promise.race([rpcPromise, timeoutPromise]);
            
            console.log('📦 Product data received:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to load product data');
            }
            
            const data = result.data;
            
            // Set UoMs
            line.availableUoms = data.available_uoms || [];
            
            // Set warehouses
            line.availableWarehouses = data.warehouses || [];
            
            // Save color and badge info from product data
            line.color_class = data.color_class || '';
            line.badge_text = data.badge_text || '';
            line.default_code = data.default_code || '';
            line.foreign_name = data.foreign_name || '';
            
            // Update productName to merge with foreign_name if code starts with S
            if (line.productName && line.default_code) {
                line.productName = this.getProductDisplayName(
                    data.product_name || line.productName,
                    line.foreign_name,
                    line.default_code
                );
            }
            
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
            
            // Set default warehouse and validate (WH 18 if available, otherwise first)
            if (line.availableWarehouses.length > 0) {
                const defaultWarehouse = this.getDefaultWarehouse(line.availableWarehouses);
                if (defaultWarehouse) {
                    line.warehouse_id = defaultWarehouse.id;
                    line.availableQty = defaultWarehouse.quantity;
                    line.warehouseCode = defaultWarehouse.code || (defaultWarehouse.name ? defaultWarehouse.name.split(' ')[0] : '');
                line.warehouseValid = true;
                }
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
            
            // Retry logic
            if (retryCount < MAX_RETRIES && (error.message.includes('timeout') || error.message.includes('Connection') || error.message.includes('interrupted'))) {
                console.log(`🔄 Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
                await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))); // Exponential backoff
                return this.loadProductInfo(lineIndex, productId, retryCount + 1);
            }
            
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
     * Get pricelist name by ID
     */
    getPricelistName(pricelistId) {
        if (!pricelistId || !this.state.pricelists) return '';
        const pricelist = this.state.pricelists.find(p => p.id === pricelistId);
        return pricelist ? pricelist.name : '';
    }
    
    /**
     * Handle pricelist search input
     */
    onPricelistSearch(ev) {
        // Pricelist is fixed, so this is just for display
        this.state.pricelistSearchTerm = ev.target.value;
    }
    
    /**
     * Handle pricelist focus
     */
    onPricelistFocus(ev) {
        // Pricelist is fixed, so dropdown is disabled
        this.state.showPricelistDropdown = false;
    }
    
    /**
     * Handle pricelist blur
     */
    onPricelistBlur(ev) {
        setTimeout(() => {
            this.state.showPricelistDropdown = false;
        }, 200);
    }
    
    /**
     * Handle pricelist keyboard navigation
     */
    handlePricelistKeyDown(ev) {
        // Pricelist is fixed, so navigation is disabled
        if (ev.key === 'Escape') {
            this.state.showPricelistDropdown = false;
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
     * Update line field value with validation
     */
    updateLine(lineIndex, field, value) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        // Validate based on field type
        if (field === 'quantity') {
            const qty = parseFloat(value) || 0;
            if (qty <= 0) {
                this.notification.add(
                    _t("Quantity must be greater than 0"),
                    { type: "warning" }
                );
                return;
            }
            line.quantity = qty;
        } else if (field === 'unitPrice') {
            const price = parseFloat(value) || 0;
            if (price < 0) {
                this.notification.add(
                    _t("Price cannot be negative"),
                    { type: "warning" }
                );
                return;
            }
            line.unitPrice = price;
        } else if (field === 'discountPercent') {
            const discount = parseFloat(value) || 0;
            if (discount < 0 || discount > 100) {
                this.notification.add(
                    _t("Discount must be between 0 and 100"),
                    { type: "warning" }
                );
                return;
            }
            line.discountPercent = discount;
        } else {
            // For other fields, just update
        line[field] = value;
        }
        
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
     * Validate a line to ensure all required fields are filled
     */
    validateLine(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        const errors = [];
        
        // Check if product is selected
        if (!line.product_id) {
            errors.push(_t("Product is required"));
        }
        
        // Check if quantity is valid
        const qty = parseFloat(line.quantity) || 0;
        if (qty <= 0) {
            errors.push(_t("Quantity must be greater than 0"));
        }
        
        // Check if UoM is valid
        if (!line.uom_id || !line.uomValid) {
            errors.push(_t("Valid UoM is required"));
        }
        
        // Check if warehouse is valid (if warehouses are available)
        if (line.availableWarehouses && line.availableWarehouses.length > 0) {
            if (!line.warehouse_id || !line.warehouseValid) {
                errors.push(_t("Valid Warehouse is required"));
            }
        }
        
        // Check if price is valid
        const price = parseFloat(line.unitPrice) || 0;
        if (price <= 0) {
            errors.push(_t("Price must be greater than 0"));
        }
        
        // Check if discount is valid (0-100)
        const discount = parseFloat(line.discountPercent) || 0;
        if (discount < 0 || discount > 100) {
            errors.push(_t("Discount must be between 0 and 100"));
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
    
    /**
     * Check if line is complete (has product and all required fields)
     */
    isLineComplete(lineIndex) {
        const validation = this.validateLine(lineIndex);
        return validation.isValid;
    }
    
    /**
     * Handle table keyboard navigation with validation
     */
    handleTableKeyDown(ev, rowIndex, colIndex) {
        const lines = this.state.currentOrder.lines;
        const maxRow = lines.length - 1;
        const maxCol = 7; // 0=Product, 1=Quantity, 2=UoM, 3=Warehouse, 4=Available, 5=Price USD, 6=Price IQD, 7=Disc%
        
        // Arrow keys for navigation
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            const nextRow = Math.min(rowIndex + 1, maxRow);
            
            // Check if current line is complete before moving to next
            if (nextRow > rowIndex) {
                const currentLine = lines[rowIndex];
                // Only validate if current line has a product (not empty)
                if (currentLine.product_id) {
                    const validation = this.validateLine(rowIndex);
                    if (!validation.isValid) {
                        this.notification.add(
                            _t("Please complete current line: ") + validation.errors.join(", "),
                            { type: "warning" }
                        );
                        return; // Don't move to next row
                    }
                } else {
                    // Current line is empty, don't allow moving to next empty line
                    this.notification.add(
                        _t("Please select a product first"),
                        { type: "warning" }
                    );
                    return;
                }
            }
            
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
        } else if (ev.key === 'Tab') {
            // Tab key - validate current line before moving
            ev.preventDefault();
            const currentLine = lines[rowIndex];
            
            // If line has product, validate it
            if (currentLine.product_id) {
                const validation = this.validateLine(rowIndex);
                if (!validation.isValid) {
                    this.notification.add(
                        _t("Please complete current line: ") + validation.errors.join(", "),
                        { type: "warning" }
                    );
                    return;
                }
            }
            
            // Move to next column or next row
            if (colIndex < maxCol) {
                this.focusCell(rowIndex, colIndex + 1);
            } else if (rowIndex < maxRow) {
                // Check if we can move to next row
                if (currentLine.product_id) {
                    // Current line has product, validate before moving
                    const validation = this.validateLine(rowIndex);
                    if (validation.isValid) {
                        this.focusCell(rowIndex + 1, 0);
                    }
                } else {
                    // Current line is empty, don't allow moving to next
                    this.notification.add(
                        _t("Please select a product first"),
                        { type: "warning" }
                    );
                }
            }
        } else if (ev.key === 'Enter') {
            // Enter key - validate and move to next row if valid
            ev.preventDefault();
            const currentLine = lines[rowIndex];
            
            if (currentLine.product_id) {
                const validation = this.validateLine(rowIndex);
                if (validation.isValid) {
                    // Move to next row, first column
                    if (rowIndex < maxRow) {
                        this.focusCell(rowIndex + 1, 0);
                    }
                } else {
                    this.notification.add(
                        _t("Please complete current line: ") + validation.errors.join(", "),
                        { type: "warning" }
                    );
                }
            } else {
                this.notification.add(
                    _t("Please select a product first"),
                    { type: "warning" }
                );
            }
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
     * Focus on specific cell with validation
     */
    focusCell(rowIndex, colIndex, skipValidation = false) {
        // Validate before moving to a different row (only if moving down)
        if (!skipValidation && rowIndex > 0) {
            const previousRowIndex = rowIndex - 1;
            const previousLine = this.state.currentOrder.lines[previousRowIndex];
            
            // Check if we're trying to move to a row that's after an incomplete line
            if (previousLine && previousLine.product_id) {
                const validation = this.validateLine(previousRowIndex);
                if (!validation.isValid) {
                    this.notification.add(
                        _t("Please complete line ") + (previousRowIndex + 1) + ": " + validation.errors.join(", "),
                        { type: "warning" }
                    );
                    // Focus back on the previous row
                    setTimeout(() => {
                        this.focusCell(previousRowIndex, colIndex, true);
                    }, 100);
                    return;
                }
            } else if (previousLine && !previousLine.product_id) {
                // Previous line is empty, don't allow moving to next
                this.notification.add(
                    _t("Please select a product in line ") + (previousRowIndex + 1) + " first",
                    { type: "warning" }
                );
                // Focus back on the previous row
                setTimeout(() => {
                    this.focusCell(previousRowIndex, 0, true);
                }, 100);
                return;
            }
        }
        
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
            // Ensure partner_id is always a number
            this.state.currentOrder.partner_id = customer.id ? Number(customer.id) : null;
            // Update customerIdForSearch
            this._updateCustomerIdForSearch();
            
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
            this._updateCustomerIdForSearch();
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
     * Get customer display name
     */
    getCustomerDisplayName(partnerId) {
        if (!partnerId) return '';
        if (Array.isArray(partnerId)) {
            return partnerId[1] || '';
        }
        return this.state.currentOrder.partner || '';
    }
    
    /**
     * Handle customer search input
     */
    onCustomerSearchInput(ev) {
        // Use CustomerSearch component functionality
        // This will be handled by opening the customer search
    }
    
    /**
     * Handle customer search focus
     */
    onCustomerSearchFocus(ev) {
        // Open customer search dropdown
        this.openCustomerSearch();
    }
    
    /**
     * Handle customer search blur
     */
    onCustomerSearchBlur(ev) {
        // Close dropdown after delay
        setTimeout(() => {
            // Dropdown will close automatically
        }, 200);
    }
    
    /**
     * Handle customer search keydown
     */
    handleCustomerSearchKeyDown(ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            this.openCustomerSearch();
        }
    }
    
    /**
     * Open customer search (use CustomerSearch component)
     */
    openCustomerSearch() {
        // Trigger customer search - we'll use the existing CustomerSearch component
        // For now, open customer dialog
        this.openCustomerDialog();
    }
    
    /**
     * Save order
     * Returns orderId if successful, false otherwise
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
            const orderLines = lines.map((line, index) => {
                const lineData = {
                    sequence: (index + 1) * 10,
                    product_id: line.product_id,
                    product_uom_id: line.uom_id,
                    warehouse_id: line.warehouse_id,
                    quantity: line.quantity,
                    unit_price: line.unitPrice,
                    discount_percent: line.discountPercent,
                };
                // Add custom product name if set
                if (line.customProductName && line.customProductName.trim()) {
                    lineData.custom_product_name = line.customProductName.trim();
                }
                return [0, 0, lineData];
            });
            
            const targetOrderId = this.state.currentOrder.order_id;
            let orderId;
            
            if (targetOrderId) {
                // Update existing order - ensure targetOrderId is in array
                const orderIds = Array.isArray(targetOrderId) ? targetOrderId : [targetOrderId];
                await this.orm.write('pos.perfume.order', orderIds, {
                    partner_id: this.state.currentOrder.partner_id,
                    pricelist_id: this.state.currentOrder.pricelist_id,
                    exchange_rate: this.state.exchangeRate,
                    invoice_type: this.state.currentOrder.invoice_type || false,
                    note: this.state.currentOrder.note || '',
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
                    invoice_type: this.state.currentOrder.invoice_type || false,
                    note: this.state.currentOrder.note || '',
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
     * Create quotation - Save as quotation, create sale.order, send to SAP, and reload
     */
    async createQuotation() {
        // Save order as quotation first
        const saved = await this.saveOrder('quotation');
        if (!saved) {
            return;
        }
        
        // Ensure orderId is a number, not array
        let orderId = this.state.currentOrder.order_id;
        if (Array.isArray(orderId)) {
            orderId = orderId[0];
        }
        
        if (!orderId) {
            this.notification.add(_t("Failed to get order ID"), { type: "danger" });
            return;
        }
        
        try {
            // Call action_confirm to create sale.order (which will send to SAP automatically)
            console.log('[Quotation] Calling action_confirm for order:', orderId);
            const result = await this.orm.call('pos.perfume.order', 'action_confirm', [[orderId]]);
            
            console.log('[Quotation] action_confirm result:', result);
            
            if (result && result.res_id) {
                // Reload the order to get SAP document numbers
                await this.loadOrder(orderId);
                this.notification.add(_t("Quotation created and sent to SAP successfully!"), { type: "success" });
            } else {
                // Still reload even if no result
                await this.loadOrder(orderId);
                this.notification.add(_t("Quotation saved successfully!"), { type: "success" });
            }
        } catch (error) {
            console.error('[Quotation] Error in action_confirm:', error);
            // Still reload the order
            await this.loadOrder(orderId);
            this.notification.add(_t("Quotation saved, but error creating sale order: ") + error.message, { type: "warning" });
        }
    }
    
    /**
     * Print order
     */
    async printOrder() {
        if (!this.state.currentOrder.order_id) {
            this.notification.add(_t("Please save the order first"), { type: "warning" });
            return;
        }
        
        try {
            const orderId = this.state.currentOrder.order_id;
            
            console.log('=== Print Order Debug ===');
            console.log('Order ID:', orderId);
            
            // First, verify the order exists
            const orderExists = await this.orm.call(
                'pos.perfume.order',
                'search_read',
                [[['id', '=', orderId]]],
                { fields: ['id', 'name', 'state'], limit: 1 }
            );
            
            console.log('Order data:', orderExists);
            
            if (!orderExists || orderExists.length === 0) {
                throw new Error('Order not found');
            }
            
            // Check if report exists
            const reportExists = await this.orm.call(
                'ir.actions.report',
                'search_read',
                [[['report_name', '=', 'pos_perfume_custom.report_pos_perfume_order']]],
                { fields: ['id', 'name', 'model', 'report_name'], limit: 1 }
            );
            
            console.log('Report exists:', reportExists);
            
            if (!reportExists || reportExists.length === 0) {
                throw new Error('Report template not found');
            }
            
            console.log('Attempting to render report via action.doAction...');
            
            // Use action.doAction to print the report
                await this.action.doAction({
                    type: 'ir.actions.report',
                    report_type: 'qweb-pdf',
                report_name: 'pos_perfume_custom.report_pos_perfume_order',
                report_file: 'pos_perfume_custom.report_pos_perfume_order',
                    context: {
                    active_ids: [orderId],
                }
            });
            
            console.log('Report action completed');
            this.notification.add(_t("Report sent to printer"), { type: "success" });
            
        } catch (error) {
            console.error('=== Print Order Error ===');
            console.error('Error object:', error);
            console.error('Error message:', error.message);
            console.error('Error data:', error.data);
            console.error('Error stack:', error.stack);
            
            let errorMessage = _t("Error printing order: ");
            
            if (error.data && error.data.message) {
                errorMessage += error.data.message;
                console.error('Server message:', error.data.message);
                
                if (error.data.debug) {
                    console.error('Server debug:', error.data.debug);
                    }
            } else if (error.message) {
                errorMessage += error.message;
            } else {
                errorMessage += String(error);
            }
            
            this.notification.add(errorMessage, { 
                type: "danger",
                sticky: true,
                title: _t("Print Error")
            });
        }
    }
    
    /**
     * Create quotation (old method - kept for reference)
     */
    async createQuotationOld() {
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
     * Save order with SAP sync - Save and sync to SAP if there are changes
     */
    async saveOrderWithSync() {
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
            // Get current order state
            let currentState = 'draft';
            let saleOrderId = null;
            if (this.state.currentOrder.order_id) {
                const orderIds = Array.isArray(this.state.currentOrder.order_id) 
                    ? [this.state.currentOrder.order_id[0]] 
                    : [this.state.currentOrder.order_id];
                const orders = await this.orm.read('pos.perfume.order', orderIds, ['state', 'sale_order_id']);
                if (orders.length > 0) {
                    currentState = orders[0].state;
                    saleOrderId = orders[0].sale_order_id ? (Array.isArray(orders[0].sale_order_id) ? orders[0].sale_order_id[0] : orders[0].sale_order_id) : null;
                }
            }
            
            // Save the POS order
            const orderId = await this.saveOrder(currentState);
            if (!orderId) {
                return false;
            }
            
            // If there's a sale order, update it and sync to SAP
            if (saleOrderId) {
                try {
                    // First, check the sale order state
                    const saleOrders = await this.orm.read('sale.order', [saleOrderId], ['state', 'order_line']);
                    if (saleOrders.length === 0) {
                        throw new Error('Sale order not found');
                    }
                    
                    const saleOrder = saleOrders[0];
                    const isConfirmed = saleOrder.state === 'sale';
                    
                    if (isConfirmed) {
                        // For confirmed sale orders, we can't delete lines
                        // Instead, we'll update existing lines or add new ones
                        const existingLineIds = saleOrder.order_line || [];
                        const orderLines = [];
                        
                        // Update existing lines or add new ones
                        lines.forEach((line, index) => {
                            if (index < existingLineIds.length) {
                                // Update existing line
                                const lineId = Array.isArray(existingLineIds[index]) 
                                    ? existingLineIds[index][0] 
                                    : existingLineIds[index];
                                orderLines.push([1, lineId, {
                                    product_uom_qty: line.quantity,
                                    product_uom_id: line.uom_id,
                                    price_unit: line.unitPrice,
                                    discount: line.discountPercent,
                                    product_warehouse_id: line.warehouse_id,
                                }]);
                            } else {
                                // Add new line
                                orderLines.push([0, 0, {
                                    product_id: line.product_id,
                                    product_uom_qty: line.quantity,
                                    product_uom_id: line.uom_id,
                                    price_unit: line.unitPrice,
                                    discount: line.discountPercent,
                                    product_warehouse_id: line.warehouse_id,
                                }]);
                            }
                        });
                        
                        // Set quantity to 0 for lines that are no longer in the POS order
                        for (let i = lines.length; i < existingLineIds.length; i++) {
                            const lineId = Array.isArray(existingLineIds[i]) 
                                ? existingLineIds[i][0] 
                                : existingLineIds[i];
                            orderLines.push([1, lineId, {
                                product_uom_qty: 0,
                            }]);
                        }
                        
                        await this.orm.write('sale.order', [saleOrderId], {
                            order_line: orderLines,
                        });
                    } else {
                        // For draft/quotation orders, we can clear and add new lines
                        const orderLines = lines.map((line, index) => [0, 0, {
                            product_id: line.product_id,
                            product_uom_qty: line.quantity,
                            product_uom_id: line.uom_id,
                            price_unit: line.unitPrice,
                            discount: line.discountPercent,
                            product_warehouse_id: line.warehouse_id,
                        }]);
                        
                        await this.orm.write('sale.order', [saleOrderId], {
                            order_line: [[5, 0, 0], ...orderLines], // Clear and add new lines
                        });
                    }
                    
                    // Trigger SAP sync by calling action_manual_sync_to_sap
                    // This ensures sync happens even if write() doesn't trigger it
                    try {
                        await this.orm.call('sale.order', 'action_manual_sync_to_sap', [[saleOrderId]]);
                        console.log('SAP sync successful for order:', saleOrderId);
                        this.notification.add(_t("Order saved and synced to SAP!"), { type: "success" });
                    } catch (syncError) {
                        console.error('SAP sync error:', syncError);
                        // The write() method should trigger automatic sync, but log the error
                        let syncErrorMsg = syncError.message || 'Unknown error';
                        if (syncError.data && syncError.data.message) {
                            syncErrorMsg = syncError.data.message;
                        }
                        console.warn('SAP sync failed, but order was saved. Error:', syncErrorMsg);
                        this.notification.add(_t("Order saved! SAP sync attempted but may have failed. Check logs."), { type: "warning" });
                    }
                    
                    // Reload order to get updated SAP info
                    await this.loadOrder(orderId);
                } catch (error) {
                    console.error('Error updating sale order:', error);
                    let errorMessage = error.message || 'Unknown error';
                    if (error.data && error.data.message) {
                        errorMessage = error.data.message;
                    } else if (error.args && error.args[0]) {
                        errorMessage = error.args[0];
                    }
                    this.notification.add(_t("Order saved, but error updating sale order: ") + errorMessage, { type: "warning" });
                }
            } else {
                this.notification.add(_t("Order saved successfully!"), { type: "success" });
            }
            
            return orderId;
        } catch (error) {
            console.error("Error saving order:", error);
            this.notification.add(_t("Failed to save order: ") + error.message, { type: "danger" });
            return false;
        }
    }
    
    /**
     * Confirm sale order - Creates and confirms sale.order, or converts quotation to sale order
     */
    async confirmSaleOrder() {
        // If order is already a quotation, convert it to sale order
        if (this.state.currentOrder.order_id) {
            const orderIds = Array.isArray(this.state.currentOrder.order_id) 
                ? [this.state.currentOrder.order_id[0]] 
                : [this.state.currentOrder.order_id];
            const orders = await this.orm.read('pos.perfume.order', orderIds, ['state', 'sale_order_id']);
            
            if (orders.length > 0 && orders[0].state === 'quotation' && orders[0].sale_order_id) {
                // Convert quotation to sale order
                const saleOrderId = Array.isArray(orders[0].sale_order_id) 
                    ? orders[0].sale_order_id[0] 
                    : orders[0].sale_order_id;
                
                try {
                    // First save any changes
                    await this.saveOrderWithSync();
                    
                    // Read sale order to check its state
                    const saleOrders = await this.orm.read('sale.order', [saleOrderId], ['state', 'name']);
                    if (saleOrders.length === 0) {
                        throw new Error('Sale order not found');
                    }
                    
                    const saleOrder = saleOrders[0];
                    console.log('[ConfirmSaleOrder] Sale order state:', saleOrder.state, 'Name:', saleOrder.name);
                    
                    // Confirm the sale order (this will change state from quotation to sale)
                    try {
                        await this.orm.call('sale.order', 'action_confirm', [[saleOrderId]]);
                    } catch (confirmError) {
                        console.error('[ConfirmSaleOrder] Error confirming sale order:', confirmError);
                        // Try to get more details about the error
                        let errorMsg = confirmError.message || 'Unknown error';
                        if (confirmError.data && confirmError.data.message) {
                            errorMsg = confirmError.data.message;
                        } else if (confirmError.args && confirmError.args[0]) {
                            errorMsg = confirmError.args[0];
                        }
                        throw new Error(`Cannot confirm sale order: ${errorMsg}`);
                    }
                    
                    // Update POS order state to 'sale'
                    await this.orm.write('pos.perfume.order', orderIds, { state: 'sale' });
                    
                    // Reload order to get updated state and SAP info
                    await this.loadOrder(orderIds[0]);
                    
                    this.notification.add(_t("Quotation converted to Sale Order and synced to SAP!"), { type: "success" });
                    return;
                } catch (error) {
                    console.error('Error converting quotation to sale order:', error);
                    let errorMessage = error.message || 'Unknown error';
                    if (error.data && error.data.message) {
                        errorMessage = error.data.message;
                    } else if (error.args && error.args[0]) {
                        errorMessage = error.args[0];
                    }
                    this.notification.add(_t("Failed to convert quotation: ") + errorMessage, { type: "danger" });
                    return;
                }
            }
        }
        
        // Otherwise, create new sale order
        const orderId = await this.saveOrder('draft');
        if (orderId) {
            try {
                // Create sale order
                const result = await this.orm.call('pos.perfume.order', 'action_confirm', [[orderId]]);
                
                if (result && result.res_id) {
                    // Confirm the sale order
                    await this.orm.call('sale.order', 'action_confirm', [[result.res_id]]);
                    
                    // Update POS order state to 'sale'
                    const orderIds = Array.isArray(orderId) ? [orderId[0]] : [orderId];
                    await this.orm.write('pos.perfume.order', orderIds, { state: 'sale' });
                    
                    // Reload order to get updated state and SAP info
                    await this.loadOrder(orderIds[0]);
                    
                    this.notification.add(_t("Sale Order created and confirmed!"), { type: "success" });
                }
            } catch (error) {
                console.error('Error confirming sale order:', error);
                // Extract detailed error message
                let errorMessage = 'Unknown error';
                if (error.data && error.data.message) {
                    errorMessage = error.data.message;
                } else if (error.data && error.data.debug) {
                    errorMessage = error.data.debug;
                } else if (error.message) {
                    errorMessage = error.message;
                } else if (error.args && error.args[0]) {
                    errorMessage = error.args[0];
                }
                
                console.error('Full error details:', {
                    message: errorMessage,
                    data: error.data,
                    stack: error.stack
                });
                
                this.notification.add(_t("Failed to confirm sale order: ") + errorMessage, { 
                    type: "danger",
                    sticky: true
                });
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
        // Reset order index
        this.state.currentOrderIndex = -1;
        if (confirm(_t("Are you sure you want to create a new order? Current order will be lost."))) {
            this.state.currentOrder.partner = null;
            this.state.currentOrder.partner_id = null;
            this._updateCustomerIdForSearch();
            this.state.currentOrder.orderNumber = 'New Order';
            this.state.currentOrder.order_id = null;
            this.state.currentOrder.state = 'draft';
            this.state.currentOrder.sap_doc_num = null;
            this.state.currentOrder.sap_doc_entry = null;
            this.state.currentOrder.sap_synced = false;
            this.state.currentOrder.invoice_type = null;
            this.state.currentOrder.note = '';
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
            // Search for recent orders with SAP fields
            const orders = await this.orm.searchRead(
                'pos.perfume.order',
                [
                    ['state', 'in', ['draft', 'quotation', 'sale']]
                ],
                ['id', 'name', 'partner_id', 'date', 'amount_total', 'state', 'sap_doc_num', 'sap_doc_entry', 'sap_synced'],
                { 
                    limit: 50, 
                    order: 'date DESC, id DESC' 
                }
            );
            
            if (orders.length === 0) {
                this.notification.add(_t("No previous orders found"), { type: "info" });
                return;
            }
            
            // Store orders and show dialog
            this.state.previousOrders = orders;
            this.state.filteredPreviousOrders = orders;
            this.state.previousOrdersSearchTerm = '';
            this.state.showPreviousOrdersDialog = true;
            
        } catch (error) {
            console.error('Error loading previous orders:', error);
            this.notification.add(_t("Error loading previous orders"), { type: "danger" });
        }
    }
    
    /**
     * Close previous orders dialog
     */
    closePreviousOrdersDialog() {
        this.state.showPreviousOrdersDialog = false;
    }
    
    /**
     * Navigate to previous order - Always available, loads last order if no orders loaded
     */
    async navigateToPreviousOrder() {
        // If no orders loaded, load the last order first
        if (this.state.previousOrders.length === 0) {
            await this.openPreviousOrders();
            // Wait a bit for orders to load
            if (this.state.previousOrders.length > 0) {
                this.state.currentOrderIndex = 0;
                await this.loadOrder(this.state.previousOrders[0].id);
                return;
            }
        }
        
        // If we have orders and we're at the first one, go to the last one (wrap around)
        if (this.state.currentOrderIndex <= 0) {
            this.state.currentOrderIndex = this.state.previousOrders.length - 1;
        } else {
            this.state.currentOrderIndex--;
        }
        
        const order = this.state.previousOrders[this.state.currentOrderIndex];
        if (order) {
            await this.loadOrder(order.id);
            this.state.showPreviousOrdersDialog = false;
        }
    }
    
    /**
     * Navigate to next order - Always available, loads last order if no orders loaded
     */
    async navigateToNextOrder() {
        // If no orders loaded, load the last order first
        if (this.state.previousOrders.length === 0) {
            await this.openPreviousOrders();
            // Wait a bit for orders to load
            if (this.state.previousOrders.length > 0) {
                this.state.currentOrderIndex = 0;
                await this.loadOrder(this.state.previousOrders[0].id);
                return;
            }
        }
        
        // If we have orders and we're at the last one, go to the first one (wrap around)
        if (this.state.currentOrderIndex >= this.state.previousOrders.length - 1) {
            this.state.currentOrderIndex = 0;
            } else {
            this.state.currentOrderIndex++;
        }
        
        const order = this.state.previousOrders[this.state.currentOrderIndex];
        if (order) {
            await this.loadOrder(order.id);
            this.state.showPreviousOrdersDialog = false;
        }
    }
    
    /**
     * Select order from dialog
     */
    async selectOrderFromDialog(orderId) {
        const orderIndex = this.state.previousOrders.findIndex(o => o.id === orderId);
        if (orderIndex >= 0) {
            this.state.currentOrderIndex = orderIndex;
            await this.loadOrder(orderId);
            this.state.showPreviousOrdersDialog = false;
        }
    }
    
    /**
     * Search in previous orders dialog
     */
    onPreviousOrdersSearch(ev) {
        const searchTerm = ev.target.value.toLowerCase();
        this.state.previousOrdersSearchTerm = searchTerm;
        
        if (!searchTerm) {
            this.state.filteredPreviousOrders = this.state.previousOrders;
            return;
        }
        
        this.state.filteredPreviousOrders = this.state.previousOrders.filter(order => {
            const orderName = order.name ? order.name.toLowerCase() : '';
            const customerName = order.partner_id ? order.partner_id[1].toLowerCase() : '';
            const sapDoc = order.sap_doc_num ? order.sap_doc_num.toLowerCase() : '';
            const sapEntry = order.sap_doc_entry ? order.sap_doc_entry.toString() : '';
            
            return orderName.includes(searchTerm) || 
                   customerName.includes(searchTerm) || 
                   sapDoc.includes(searchTerm) ||
                   sapEntry.includes(searchTerm);
        });
    }
    
    /**
     * Handle Order Number input - search and load order
     */
    onOrderNumberInput(ev) {
        this.state.orderNumberSearch = ev.target.value;
    }
    
    /**
     * Handle Order Number keydown - Enter to search
     */
    async onOrderNumberKeyDown(ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            const searchTerm = this.state.orderNumberSearch.trim();
            if (!searchTerm) {
                return;
            }
            
            try {
                // Search for order by name
                const orders = await this.orm.searchRead(
                    'pos.perfume.order',
                    [
                        ['name', 'ilike', searchTerm]
                    ],
                    ['id', 'name'],
                    { limit: 1 }
                );
                
                if (orders.length > 0) {
                    await this.loadOrder(orders[0].id);
                    this.state.orderNumberSearch = '';
                    ev.target.value = '';
            } else {
                this.notification.add(_t("Order not found"), { type: "warning" });
                }
            } catch (error) {
                console.error('Error searching order:', error);
                this.notification.add(_t("Error searching order"), { type: "danger" });
            }
        }
    }
    
    /**
     * Handle SAP Doc input - clear if user starts typing
     */
    onSapDocInput(ev) {
        // If there's a saved SAP doc, clear it when user starts typing
        if (this.state.currentOrder.sap_doc_num) {
            this.state.currentOrder.sap_doc_num = null;
            this.state.currentOrder.sap_doc_entry = null;
            this.state.currentOrder.sap_synced = false;
        }
        this.state.sapDocSearch = ev.target.value;
    }
    
    /**
     * Handle SAP Doc search keydown - Enter to search
     */
    async onSapDocKeyDown(ev) {
        // If field is readonly (showing saved SAP doc), don't allow editing
        if (this.state.currentOrder.sap_doc_num && ev.key !== 'Escape') {
            if (ev.key === 'Enter' || ev.key === 'Delete' || ev.key === 'Backspace') {
                // Clear saved SAP doc on Delete/Backspace/Enter
                this.state.currentOrder.sap_doc_num = null;
                this.state.currentOrder.sap_doc_entry = null;
                this.state.currentOrder.sap_synced = false;
                this.state.sapDocSearch = '';
                ev.target.value = '';
                ev.target.readOnly = false;
                ev.target.placeholder = 'SAP Doc #...';
                ev.target.style.background = '';
                ev.target.style.borderColor = '#ccc';
                return;
            }
        }
        
        if (ev.key === 'Enter') {
            ev.preventDefault();
            const searchTerm = this.state.sapDocSearch.trim();
            if (!searchTerm) {
                return;
            }
            
            try {
                // Search for order by SAP Doc Number
                const orders = await this.orm.searchRead(
                    'pos.perfume.order',
                    [
                        ['sap_doc_num', 'ilike', searchTerm]
                    ],
                    ['id', 'name', 'sap_doc_num'],
                    { limit: 1 }
                );
                
                if (orders.length > 0) {
                    await this.loadOrder(orders[0].id);
                    this.state.sapDocSearch = '';
                    ev.target.value = '';
                } else {
                    this.notification.add(_t("Order with SAP Doc not found"), { type: "warning" });
                }
        } catch (error) {
                console.error('Error searching SAP Doc:', error);
                this.notification.add(_t("Error searching SAP Doc"), { type: "danger" });
            }
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
                ['id', 'name', 'partner_id', 'pricelist_id', 'order_line_ids', 'state', 'amount_total', 'sap_doc_num', 'sap_doc_entry', 'sap_synced', 'invoice_type', 'note']
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
            // Ensure partner_id is a number, not an array
            const partnerId = order.partner_id ? (Array.isArray(order.partner_id) ? order.partner_id[0] : order.partner_id) : null;
            this.state.currentOrder.partner_id = partnerId ? Number(partnerId) : null;
            this._updateCustomerIdForSearch();
            const pricelistId = order.pricelist_id ? (Array.isArray(order.pricelist_id) ? order.pricelist_id[0] : order.pricelist_id) : null;
            this.state.currentOrder.pricelist_id = pricelistId ? Number(pricelistId) : null;
            this.state.currentOrder.state = order.state || 'draft';
            // Update SAP fields
            this.state.currentOrder.sap_doc_num = order.sap_doc_num || null;
            this.state.currentOrder.sap_doc_entry = order.sap_doc_entry || null;
            this.state.currentOrder.sap_synced = order.sap_synced || false;
            // Update invoice type and notes
            this.state.currentOrder.invoice_type = order.invoice_type || null;
            this.state.currentOrder.note = order.note || '';
            
            // Update current order index if in previous orders list
            if (this.state.previousOrders.length > 0) {
                const orderIndex = this.state.previousOrders.findIndex(o => o.id === order.id);
                if (orderIndex >= 0) {
                    this.state.currentOrderIndex = orderIndex;
                }
            }
            
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
            
            // Load lines with saved values (UoM, Warehouse, Price, Discount)
            const loadPromises = [];
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const uiLine = this.state.currentOrder.lines[i];
                
                if (line.product_id) {
                    const productId = Array.isArray(line.product_id) ? line.product_id[0] : line.product_id;
                    const productName = Array.isArray(line.product_id) ? line.product_id[1] : '';
                    
                    // Set product info
                    uiLine.product_id = productId;
                    uiLine.productName = productName;
                    
                    // Set saved values from order line
                    uiLine.quantity = line.quantity || 1;
                    uiLine.unitPrice = line.unit_price || 0;
                    uiLine.discountPercent = line.discount_percent || 0;
                    
                    // Set saved UoM (preserve the selected UoM)
                    const savedUomId = line.product_uom_id ? (Array.isArray(line.product_uom_id) ? line.product_uom_id[0] : line.product_uom_id) : null;
                    uiLine.uom_id = savedUomId;
                    
                    // Set saved Warehouse (preserve the selected warehouse)
                    const savedWarehouseId = line.warehouse_id ? (Array.isArray(line.warehouse_id) ? line.warehouse_id[0] : line.warehouse_id) : null;
                    uiLine.warehouse_id = savedWarehouseId;
                    
                    // Set custom product name if exists
                    if (line.custom_product_name) {
                        uiLine.customProductName = line.custom_product_name;
                    }
                    
                    // Load product info to get available UoMs and Warehouses, but don't override saved values
                    loadPromises.push(this.loadProductInfoWithSavedValues(i, productId, savedUomId, savedWarehouseId, line.unit_price));
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
     * Send via WhatsApp using ULTRAMSG
     */
    async sendWhatsApp() {
        try {
            // Check if order is saved
            if (!this.state.currentOrder.order_id) {
                this.notification.add(
                    _t("Please save the order first before sending via WhatsApp"),
                    { type: "warning" }
                );
                return;
            }
            
            // Check if customer is selected
            if (!this.state.currentOrder.partner_id) {
                this.notification.add(
                    _t("Please select a customer first"),
                    { type: "warning" }
                );
                return;
            }
            
            // Show loading notification
            this.notification.add(
                _t("Generating PDF and sending via WhatsApp..."),
                { type: "info" }
            );
            
            // Call backend to send WhatsApp
            const result = await rpc('/pos_perfume/send_whatsapp', {
                order_id: this.state.currentOrder.order_id,
            });
            
            if (result.success) {
                this.notification.add(
                    _t("✅ Invoice sent successfully via WhatsApp!"),
                    { type: "success" }
                );
            } else {
                this.notification.add(
                    _t("❌ Failed to send: ") + (result.error || 'Unknown error'),
                    { type: "danger" }
                );
            }
            
        } catch (error) {
            console.error('Error sending WhatsApp:', error);
            this.notification.add(
                _t("Error sending WhatsApp: ") + error.message,
                { type: "danger" }
            );
        }
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
                
                // Store original results (before filtering)
                this.state.rightSearchResultsOriginal = products;
                
                // Check if S-200 is in original results
                const s200Products = products.filter(p => {
                    const code = (p.default_code || '').toUpperCase();
                    return code.includes('S-200') || code.startsWith('S-200');
                });
                if (s200Products.length > 0) {
                    console.log(`[Search] Found ${s200Products.length} S-200 products in original results:`, s200Products.map(p => p.default_code));
                } else {
                    console.log(`[Search] No S-200 products found in original results. Total products: ${products.length}`);
                    // Log first 10 product codes for debugging
                    console.log(`[Search] First 10 product codes:`, products.slice(0, 10).map(p => p.default_code));
                }
                
                // Apply filters
                this.state.rightSearchResults = products;
                this.applyFiltersToResults();
                
                // Check if S-200 is still in filtered results
                const s200AfterFilter = this.state.rightSearchResults.filter(p => {
                    const code = (p.default_code || '').toUpperCase();
                    return code.includes('S-200') || code.startsWith('S-200');
                });
                if (s200AfterFilter.length > 0) {
                    console.log(`[Filter] S-200 products after filtering:`, s200AfterFilter.map(p => p.default_code));
                } else if (s200Products.length > 0) {
                    console.warn(`[Filter] S-200 products were filtered out! Original: ${s200Products.length}, After filter: 0`);
                }
                
                // Reset selection when new results arrive
                this.state.selectedRightProductIndex = 0;
                if (this.state.rightSearchResults.length > 0) {
                    this.state.selectedRightProduct = this.state.rightSearchResults[0].id;
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
        let lineIndex;
        
        if (!line) {
            // Add new line
            const newLine = this.createEmptyLine(this.state.currentOrder.lines.length + 1);
            this.state.currentOrder.lines.push(newLine);
            line = newLine;
            lineIndex = this.state.currentOrder.lines.length - 1;
        } else {
            // Get index of existing line
            lineIndex = this.state.currentOrder.lines.findIndex(l => l === line);
            if (lineIndex === -1) {
                // Fallback: use indexOf
                lineIndex = this.state.currentOrder.lines.indexOf(line);
            }
        }
        
        // Verify lineIndex is valid
        if (lineIndex === -1 || lineIndex >= this.state.currentOrder.lines.length) {
            console.error(`Invalid lineIndex: ${lineIndex}, lines length: ${this.state.currentOrder.lines.length}`);
            return;
        }
        
        // Verify line still exists before setting product
        if (!this.state.currentOrder.lines[lineIndex]) {
            console.error(`Line at index ${lineIndex} disappeared before setting product`);
            return;
        }
        
        // Re-get line reference to ensure it's current
        let currentLine = this.state.currentOrder.lines[lineIndex];
        
        // Set product
        currentLine.product_id = product.id;
        currentLine.default_code = product.default_code || '';
        currentLine.foreign_name = product.foreign_name || '';
        currentLine.color_class = product.color_class || '';
        currentLine.badge_text = product.badge_text || '';
        
        // Get display name (merge with foreign_name if code starts with S)
        currentLine.productName = this.getProductDisplayName(
            product.name,
            product.foreign_name,
            product.default_code
        );
        
        // Load UoMs and warehouses
        await Promise.all([
            this.loadAvailableUoms(lineIndex, product.id),
            this.loadAvailableWarehousesFromProduct(lineIndex, product)
        ]);
        
        // Verify line still exists after async operations
        if (!this.state.currentOrder.lines[lineIndex]) {
            console.error(`Line at index ${lineIndex} disappeared after loading UoMs/warehouses`);
            return;
        }
        
        // Re-get line reference again
        currentLine = this.state.currentOrder.lines[lineIndex];
        
        // Load product info
        await this.loadProductInfo(lineIndex, product.id);
        
        // Verify line still exists after loading product info
        if (!this.state.currentOrder.lines[lineIndex]) {
            console.error(`Line at index ${lineIndex} disappeared after loading product info`);
            return;
        }
        
        // Re-get line reference one more time
        currentLine = this.state.currentOrder.lines[lineIndex];
        
        // Auto-select UOM based on active unit filter
        if (this.state.activeUnitFilter && currentLine.availableUoms && currentLine.availableUoms.length > 0) {
            console.log(`[UOM Auto-Select] Filter: ${this.state.activeUnitFilter.filter}, Available UOMs:`, currentLine.availableUoms.map(u => u.name));
            const targetUnit = this.findUomByFilter(currentLine.availableUoms, this.state.activeUnitFilter.filter);
            if (targetUnit) {
                console.log(`[UOM Auto-Select] Selected UOM: ${targetUnit.name} (ID: ${targetUnit.id})`);
                currentLine.uom_id = targetUnit.id;
                currentLine.uomName = targetUnit.name;
                currentLine.uomValid = true;
                
                // Update price if available
                if (targetUnit.price !== undefined) {
                    currentLine.unitPrice = targetUnit.price;
                    console.log(`[UOM Auto-Select] Price from UOM: ${targetUnit.price}`);
                } else {
                    // Call onchange to get price
                    console.log(`[UOM Auto-Select] Calling onUomChange to get price...`);
                    await this.onUomChange(lineIndex);
                }
                
                this.calculateLine(currentLine);
                this.calculateTotals();
            } else {
                console.warn(`[UOM Auto-Select] No matching UOM found for filter: ${this.state.activeUnitFilter.filter}`);
            }
        } else {
            if (!this.state.activeUnitFilter) {
                console.log(`[UOM Auto-Select] No active unit filter`);
            } else if (!currentLine.availableUoms || currentLine.availableUoms.length === 0) {
                console.warn(`[UOM Auto-Select] No available UOMs for product ${product.id}`);
            }
        }
        
        // Add new empty line if we're at the last line
        const isLastLine = lineIndex === this.state.currentOrder.lines.length - 1;
        if (isLastLine) {
            const newEmptyLine = this.createEmptyLine(this.state.currentOrder.lines.length + 1);
            this.state.currentOrder.lines.push(newEmptyLine);
        }
        
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
        // Verify lineIndex is valid first
        if (lineIndex === -1 || lineIndex < 0 || !this.state.currentOrder.lines || lineIndex >= this.state.currentOrder.lines.length) {
            console.error(`Invalid lineIndex: ${lineIndex}, lines length: ${this.state.currentOrder.lines ? this.state.currentOrder.lines.length : 0}`);
            return;
        }
        
        const line = this.state.currentOrder.lines[lineIndex];
        
        // Check if line exists
        if (!line) {
            console.error(`Line at index ${lineIndex} not found`);
            return;
        }
        
        // Initialize availableWarehouses if it doesn't exist
        if (!line.availableWarehouses) {
            line.availableWarehouses = [];
        }
        
        line.availableWarehouses = product.warehouses || [];
        
        // Set default warehouse (WH 18 if available, otherwise first)
        if (line.availableWarehouses.length > 0) {
            const defaultWarehouse = this.getDefaultWarehouse(line.availableWarehouses);
            if (defaultWarehouse) {
                line.warehouse_id = defaultWarehouse.id;
                line.availableQty = defaultWarehouse.quantity;
            }
        }
    }
    
    /**
     * Get cached handler for template
     */
    getHandler(key, factory) {
        if (!this._handlerCache.has(key)) {
            this._handlerCache.set(key, factory());
        }
        return this._handlerCache.get(key);
    }
    
    /**
     * Wrapper methods for template handlers - return cached handlers
     */
    onProductSearchHandler(lineIndex) {
        const key = `onProductSearch_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.onProductSearch(ev, lineIndex));
    }
    
    onProductFocusHandler(lineIndex) {
        const key = `onProductFocus_${lineIndex}`;
        return this.getHandler(key, () => (ev) => {
            this.onProductFocus(ev, lineIndex);
            this.setFocusedCell(lineIndex, 0);
        });
    }
    
    onProductBlurHandler(lineIndex) {
        const key = `onProductBlur_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.onProductBlur(ev, lineIndex));
    }
    
    handleProductKeyDownHandler(lineIndex) {
        const key = `handleProductKeyDown_${lineIndex}`;
        return this.getHandler(key, () => (ev) => {
            this.handleProductKeyDown(ev, lineIndex);
            this.handleTableKeyDown(ev, lineIndex, 0);
        });
    }
    
    selectProductHandler(lineIndex, product) {
        const key = `selectProduct_${lineIndex}_${product.id}`;
        return this.getHandler(key, () => () => this.selectProduct(lineIndex, product));
    }
    
    updateLineHandler(lineIndex, field) {
        const key = `updateLine_${lineIndex}_${field}`;
        return this.getHandler(key, () => (ev) => {
            const value = field === 'quantity' ? (parseFloat(ev.target.value) || 1) :
                         field === 'unitPrice' ? (parseFloat(ev.target.value) || 0) :
                         field === 'discountPercent' ? (parseFloat(ev.target.value) || 0) :
                         ev.target.value;
            this.updateLine(lineIndex, field, value);
        });
    }
    
    focusSelectHandler(lineIndex, col) {
        const key = `focusSelect_${lineIndex}_${col}`;
        return this.getHandler(key, () => (ev) => {
            // Check if we're moving to a different row
            const currentFocusedRow = this.state.focusedCell.row;
            
            // If moving to a row that's after the current one, validate current row first
            if (lineIndex > currentFocusedRow && currentFocusedRow >= 0) {
                const currentLine = this.state.currentOrder.lines[currentFocusedRow];
                
                // Only validate if current line has a product
                if (currentLine && currentLine.product_id) {
                    const validation = this.validateLine(currentFocusedRow);
                    if (!validation.isValid) {
                        ev.preventDefault();
                        ev.stopPropagation();
                        this.notification.add(
                            _t("Please complete line ") + (currentFocusedRow + 1) + ": " + validation.errors.join(", "),
                            { type: "warning" }
                        );
                        // Keep focus on current row
                        setTimeout(() => {
                            this.focusCell(currentFocusedRow, this.state.focusedCell.col, true);
                        }, 100);
                        return;
                    }
                } else if (currentLine && !currentLine.product_id) {
                    // Current line is empty, don't allow moving to next
                    ev.preventDefault();
                    ev.stopPropagation();
                    this.notification.add(
                        _t("Please select a product in line ") + (currentFocusedRow + 1) + " first",
                        { type: "warning" }
                    );
                    // Keep focus on current row
                    setTimeout(() => {
                        this.focusCell(currentFocusedRow, 0, true);
                    }, 100);
                    return;
                }
            }
            
            ev.target.select();
            this.setFocusedCell(lineIndex, col);
        });
    }
    
    handleTableKeyDownHandler(lineIndex, col) {
        const key = `handleTableKeyDown_${lineIndex}_${col}`;
        return this.getHandler(key, () => (ev) => this.handleTableKeyDown(ev, lineIndex, col));
    }
    
    onUomInputHandler(lineIndex) {
        const key = `onUomInput_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.onUomInput(ev, lineIndex));
    }
    
    onUomFocusHandler(lineIndex) {
        const key = `onUomFocus_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.onUomFocus(ev, lineIndex));
    }
    
    validateUomHandler(lineIndex) {
        const key = `validateUom_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.validateUom(ev, lineIndex));
    }
    
    handleUomKeyDownHandler(lineIndex) {
        const key = `handleUomKeyDown_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.handleUomKeyDown(ev, lineIndex));
    }
    
    selectUomHandler(lineIndex, uom) {
        const key = `selectUom_${lineIndex}_${uom.id || uom.uom_id}`;
        return this.getHandler(key, () => () => this.selectUom(lineIndex, uom));
    }
    
    onWarehouseInputHandler(lineIndex) {
        const key = `onWarehouseInput_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.onWarehouseInput(ev, lineIndex));
    }
    
    onWarehouseFocusHandler(lineIndex) {
        const key = `onWarehouseFocus_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.onWarehouseFocus(ev, lineIndex));
    }
    
    validateWarehouseHandler(lineIndex) {
        const key = `validateWarehouse_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.validateWarehouse(ev, lineIndex));
    }
    
    handleWarehouseKeyDownHandler(lineIndex) {
        const key = `handleWarehouseKeyDown_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.handleWarehouseKeyDown(ev, lineIndex));
    }
    
    selectWarehouseHandler(lineIndex, wh) {
        const key = `selectWarehouse_${lineIndex}_${wh.id}`;
        return this.getHandler(key, () => () => this.selectWarehouse(lineIndex, wh));
    }
    
    onPriceIqdInputHandler(lineIndex) {
        const key = `onPriceIqdInput_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.onPriceIqdInput(ev, lineIndex));
    }
    
    deleteLineHandler(lineIndex) {
        const key = `deleteLine_${lineIndex}`;
        return this.getHandler(key, () => () => this.deleteLine(lineIndex));
    }
    
    handleDeleteKeyDownHandler(lineIndex) {
        const key = `handleDeleteKeyDown_${lineIndex}`;
        return this.getHandler(key, () => (ev) => this.handleDeleteKeyDown(ev, lineIndex));
    }
    
    addProductFromRightPanelHandler(product) {
        const key = `addProductFromRightPanel_${product.id}`;
        return this.getHandler(key, () => () => this.addProductFromRightPanel(product));
    }
    
    /**
     * Open product popup/form view
     */
    async openProductPopup(lineIndex) {
        const line = this.state.currentOrder.lines[lineIndex];
        
        if (!line.product_id) {
            this.notification.add(_t("Please select a product first"), { type: "warning" });
            return;
        }
        
        try {
            await this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'product.product',
                res_id: line.product_id,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    default_id: line.product_id,
                }
            });
        } catch (error) {
            console.error("Error opening product popup:", error);
            this.notification.add(_t("Failed to open product details"), { type: "danger" });
        }
    }
    
    // ============================================================
    // FILTER FUNCTIONS - UI Handlers
    // ============================================================
    
    /**
     * Toggle brand filter
     */
    toggleBrandFilter(brand) {
        const index = this.state.activeFilters.findIndex(f => f.prefix === brand);
        if (index >= 0) {
            this.state.activeFilters.splice(index, 1);
        } else {
            this.state.activeFilters.push({
                prefix: brand,
                name: brand,
                type: 'brand'
            });
        }
        this.applyFiltersToResults();
    }
    
    /**
     * Toggle unit filter
     */
    toggleUnitFilter(unit) {
        if (this.state.activeUnitFilter && this.state.activeUnitFilter.filter === unit.filter) {
            this.state.activeUnitFilter = null;
        } else {
            this.state.activeUnitFilter = unit;
        }
        this.applyFiltersToResults();
    }
    
    /**
     * Toggle plastic filter
     */
    togglePlasticFilter(value) {
        this.state.fullPlasticFilterActive = value;
        this.applyFiltersToResults();
    }
    
    /**
     * Toggle CS-LOC filter
     * When active: show only CS and LOC products
     * When inactive: hide CS and LOC products
     */
    toggleCsLocFilter() {
        this.state.csLocFilterActive = !this.state.csLocFilterActive;
        this.applyFiltersToResults();
    }
    
    /**
     * Check if brand filter is active
     */
    isBrandFilterActive(brand) {
        return this.state.activeFilters.some(f => f.prefix === brand);
    }
    
    /**
     * Check if unit filter is active
     */
    isUnitFilterActive(filter) {
        return this.state.activeUnitFilter && this.state.activeUnitFilter.filter === filter;
    }
    
    // ============================================================
    // FILTER FUNCTIONS - Filtering Logic
    // ============================================================
    
    /**
     * Apply all filters to search results
     */
    applyFiltersToResults() {
        // Use original results if available, otherwise use current results
        const sourceProducts = this.state.rightSearchResultsOriginal || this.state.rightSearchResults || [];
        
        if (sourceProducts.length === 0) {
            this.state.rightSearchResults = [];
            return;
        }
        
        console.log(`[Filter] Applying filters to ${sourceProducts.length} products`);
        console.log(`[Filter] Active brand filters: ${this.state.activeFilters?.length || 0}`);
        console.log(`[Filter] Active unit filter: ${this.state.activeUnitFilter ? this.state.activeUnitFilter.filter : 'none'}`);
        console.log(`[Filter] Full plastic filter: ${this.state.fullPlasticFilterActive}`);
        console.log(`[Filter] CS-LOC filter: ${this.state.csLocFilterActive}`);
        
        let filtered = [...sourceProducts];
        
        // 0. Always hide PR products (first, before any other filters)
        const beforePR = filtered.length;
        filtered = this.filterProductsByPR(filtered);
        console.log(`[Filter] After PR filter (always hide): ${filtered.length} products (was ${beforePR})`);
        
        // 1. Filter by brands
        const beforeBrand = filtered.length;
        filtered = this.filterProductsByBrand(filtered);
        console.log(`[Filter] After brand filter: ${filtered.length} products (was ${beforeBrand})`);
        
        // 2. Filter by CS-LOC (hide CS/LOC by default, show only when filter is active)
        const beforeCsLoc = filtered.length;
        filtered = this.filterProductsByCsLoc(filtered);
        console.log(`[Filter] After CS-LOC filter: ${filtered.length} products (was ${beforeCsLoc})`);
        
        // 3. Filter by plastic
        const beforePlastic = filtered.length;
        filtered = this.filterProductsByPlastic(filtered);
        console.log(`[Filter] After plastic filter: ${filtered.length} products (was ${beforePlastic})`);
        
        // 4. Filter by units (1KG, 0.5, 50, 100, 125 special case)
        const beforeUnit = filtered.length;
        filtered = this.filterProductsBy025KgUnit(filtered);
        console.log(`[Filter] After unit filter: ${filtered.length} products (was ${beforeUnit})`);
        
        // Update results
        this.state.rightSearchResults = filtered;
        console.log(`[Filter] Final result: ${filtered.length} products`);
    }
    
    /**
     * Filter products by brand
     * تعتمد فلاتر البراند على الكود (sub_sku أو default_code) فقط
     * عند اختيار براند واحد: إظهار منتجات هذا البراند فقط
     * عند اختيار عدة براندات: إظهار منتجات أي من البراندات المختارة (OR logic)
     * إذا لم يتم اختيار أي براند: إظهار جميع المنتجات
     */
    filterProductsByBrand(products) {
        if (!this.state.activeFilters || this.state.activeFilters.length === 0) {
            // لا توجد فلاتر نشطة، إرجاع جميع المنتجات (بما في ذلك CS, LOC, إلخ)
            console.log('[Filter] No active brand filters - showing all products');
            return products;
        }
        
        const activeBrands = this.state.activeFilters.map(f => f.prefix.toUpperCase());
        console.log('[Filter] Active brands:', activeBrands);
        
        return products.filter(product => {
            // الاعتماد على الكود فقط (sub_sku أو default_code)
            const sku = (product.sub_sku || product.default_code || '').toUpperCase();
            
            if (!sku) {
                console.log(`[Filter] Product ${product.id} has no SKU - hiding`);
                return false; // لا يوجد كود، إخفاء المنتج
            }
            
            // التحقق من مطابقة المنتج مع أي من البراندات النشطة (OR logic)
            const matches = this.state.activeFilters.some(filter => {
                const prefix = filter.prefix.toUpperCase();
                let matches = false;
                
                // حالات خاصة لكل براند
                if (prefix === 'ADF') {
                    // ADF -> الكود يبدأ بـ "ADF"
                    matches = sku.startsWith('ADF');
                }
                else if (prefix === 'ROYAL') {
                    // ROYAL -> الكود يبدأ بـ "R" (لكن ليس "ADF" أو "G" أو "EURO")
                    // أو يبدأ بـ "ROYAL" أو "ROY"
                    matches = (sku.startsWith('R') && !sku.startsWith('ADF') && !sku.startsWith('G') && !sku.startsWith('EURO')) 
                           || sku.startsWith('ROYAL') 
                           || sku.startsWith('ROY');
                }
                else if (prefix === 'GIVAUDAN') {
                    // GIVAUDAN -> الكود يبدأ بـ "G" (لكن ليس "ADF" أو "R" أو "EURO")
                    // أو يبدأ بـ "GIVAUDAN" أو "GIV"
                    matches = (sku.startsWith('G') && !sku.startsWith('ADF') && !sku.startsWith('R') && !sku.startsWith('EURO')) 
                           || sku.startsWith('GIVAUDAN') 
                           || sku.startsWith('GIV');
                }
                else if (prefix === 'EURO') {
                    // EURO: التحقق من وجود "N1" في الكود أو يبدأ بـ "EURO"
                    matches = sku.includes('N1') || sku.startsWith('EURO');
                }
                else {
                    // الحالة الافتراضية: التحقق من أن الكود يبدأ ببادئة البراند
                    matches = sku.startsWith(prefix);
                }
                
                if (matches) {
                    console.log(`[Filter] Product ${sku} matches brand ${prefix}`);
                }
                
                return matches;
            });
            
            if (!matches) {
                console.log(`[Filter] Product ${sku} does not match any active brand - hiding`);
            }
            
            return matches;
        });
    }
    
    /**
     * Always hide PR products (regardless of any filters)
     */
    filterProductsByPR(products) {
        return products.filter(product => {
            const sku = (product.sub_sku || product.default_code || '').toUpperCase();
            if (sku.startsWith('PR') || sku.startsWith('DY')) {
                console.log(`[Filter] Hiding PR/DY product: ${sku}`);
                return false;
            }
            return true;
        });
    }
    
    /**
     * Filter products by CS-LOC
     * When csLocFilterActive is false (default): hide CS and LOC products
     * When csLocFilterActive is true: show only CS and LOC products
     */
    filterProductsByCsLoc(products) {
        return products.filter(product => {
            const sku = (product.sub_sku || product.default_code || '').toUpperCase();
            const isCsLoc = sku.startsWith('CS') || sku.startsWith('LOC');
            
            if (this.state.csLocFilterActive) {
                // Filter is active: show only CS and LOC products
                if (isCsLoc) {
                    console.log(`[Filter] Showing CS-LOC product: ${sku}`);
                    return true;
                } else {
                    console.log(`[Filter] Hiding non-CS-LOC product: ${sku}`);
                    return false;
                }
            } else {
                // Filter is inactive: hide CS and LOC products
                if (isCsLoc) {
                    console.log(`[Filter] Hiding CS-LOC product (filter inactive): ${sku}`);
                    return false;
                } else {
                    return true;
                }
            }
        });
    }
    
    /**
     * Filter products by plastic
     */
    filterProductsByPlastic(products) {
        if (this.state.fullPlasticFilterActive === false) {
            return products.filter(product => !this.isFullPlasticProduct(product));
        }
        return products;
    }
    
    /**
     * Check if product is full plastic
     * تعتمد على UOM فقط (Unit of Measure)
     */
    isFullPlasticProduct(product) {
        const keywords = ['فل بلاستك', 'فل بلاستيك', 'full plastic', 'fl plastic'];
        
        // Get UOM name from product - check multiple possible fields
        let uomName = '';
        
        // Check sap_uom_group_name first
        if (product.sap_uom_group_name) {
            uomName = product.sap_uom_group_name;
        }
        // Check uom_name
        else if (product.uom_name) {
            uomName = product.uom_name;
        }
        // Check unit (if it's a string or object)
        else if (product.unit) {
            uomName = typeof product.unit === 'string' ? product.unit : (product.unit.name || '');
        }
        // Check availableUoms (from line)
        else if (product.availableUoms && product.availableUoms.length > 0) {
            uomName = product.availableUoms[0].name || '';
        }
        // Check processed_units, units, sub_units
        else {
            const allUnits = [
                ...(product.processed_units || []),
                ...(product.units || []),
                ...(product.sub_units || [])
            ];
            
            if (allUnits.length > 0) {
                uomName = typeof allUnits[0] === 'string' ? allUnits[0] : (allUnits[0].name || '');
            }
        }
        
        // Check if UOM name contains any of the keywords
        const uomNameLower = (uomName || '').toLowerCase();
        return keywords.some(kw => uomNameLower.includes(kw.toLowerCase()));
    }
    
    /**
     * Filter products by 0.25KG unit (special case for 1KG, 0.5, 50, 100, 125)
     * Only apply shouldHideProduct when a unit filter is active
     */
    filterProductsBy025KgUnit(products) {
        if (!this.state.activeUnitFilter) {
            // No unit filter active - show all products (don't hide CS, LOC, etc.)
            return products;
        }
        
        const specialFilters = ['1KG', '0.5', '50', '100', '125'];
        if (!specialFilters.includes(this.state.activeUnitFilter.filter)) {
            // Not a special filter - show all products
            return products;
        }
        
        // Only apply shouldHideProduct when a special unit filter is active
        return products.filter(product => {
            if (this.shouldHideProduct(product)) {
                return false;
            }
            return true;
        });
    }
    
    /**
     * Check if product should be hidden
     * تعتمد على UOM فقط (Unit of Measure)
     * عند اختيار فلتر الوحدة (مثلاً 125g):
     * - إظهار فقط منتجات "لك" (دائماً)
     * - إظهار منتجات "فل بلاستك" (فقط إذا كان fullPlasticFilterActive === true)
     * - إخفاء باقي المنتجات
     */
    shouldHideProduct(product) {
        // Get UOM name from product - check multiple possible fields
        let uomName = '';
        
        // Check sap_uom_group_name first
        if (product.sap_uom_group_name) {
            uomName = product.sap_uom_group_name;
        }
        // Check uom_name
        else if (product.uom_name) {
            uomName = product.uom_name;
        }
        // Check unit (if it's a string or object)
        else if (product.unit) {
            uomName = typeof product.unit === 'string' ? product.unit : (product.unit.name || '');
        }
        // Check availableUoms (from line)
        else if (product.availableUoms && product.availableUoms.length > 0) {
            uomName = product.availableUoms[0].name || '';
        }
        // Check processed_units, units, sub_units
        else {
            const allUnits = [
                ...(product.processed_units || []),
                ...(product.units || []),
                ...(product.sub_units || [])
            ];
            
            if (allUnits.length > 0) {
                uomName = typeof allUnits[0] === 'string' ? allUnits[0] : (allUnits[0].name || '');
            }
        }
        
        const uomNameLower = (uomName || '').toLowerCase();
        
        // Check if "لك" product (UOM contains "لك")
        if (uomNameLower.includes('لك')) {
            return false; // Don't hide - always show "لك" products
        }
        
        // Check if "فل بلاستك" product (UOM contains "فل بلاستك")
        if (uomNameLower.includes('فل بلاستك') || uomNameLower.includes('فل بلاستيك')) {
            // Show only if full plastic filter is active (true)
            return this.state.fullPlasticFilterActive !== true;
        }
        
        // Hide all other products (not "لك" and not "فل بلاستك")
        return true;
    }
    
    /**
     * Find UOM by filter value (e.g., "125" -> "125g" or "125 غم")
     */
    findUomByFilter(availableUoms, filterValue) {
        if (!availableUoms || availableUoms.length === 0) {
            console.warn(`[findUomByFilter] No available UOMs provided`);
            return null;
        }
        
        if (!filterValue) {
            console.warn(`[findUomByFilter] No filter value provided`);
            return null;
        }
        
        // Map filter values to search patterns (ordered by priority: most specific first)
        const filterMap = {
            '125': [
                '125g', '125غم', '125 غم', '125 جرام', '125 غرام', '125g', '125غم',
                '125'  // Keep as last to avoid matching "125" in "1250" or similar
            ],
            '100': [
                '100g', '100غم', '100 غم', '100 جرام', '100 غرام', '100g', '100غم',
                '100'  // Keep as last
            ],
            '50': [
                '50g', '50غم', '50 غم', '50 جرام', '50 غرام', '50g', '50غم',
                '50'  // Keep as last
            ],
            '0.5': [
                '0.5kg', '0.5 كغم', '0.5 كيلو',
                '500g', '500غم', '500 غم', '500 جرام', '500 غرام'
                // Removed '0.5' and '500' to avoid false matches with "كغم" or other units
            ],
            '1KG': [
                'كغم', 'كيلو', 'kg', 'كيلوغرام',  // Most specific: Arabic and English "kg"
                '1kg', '1 كغم', '1 كيلو', '1 كغم',
                '1000g', '1000غم', '1000 غم'
                // Removed '1' and '1000' to avoid false matches
            ],
            '0.25': [
                '0.25kg', '0.25 كغم', '0.25 كيلو',
                '250g', '250غم', '250 غم', '250 جرام', '250 غرام'
                // Removed '0.25' and '250' to avoid false matches
            ]
        };
        
        const searchPatterns = filterMap[filterValue] || [filterValue];
        console.log(`[findUomByFilter] Searching for filter: ${filterValue}, patterns:`, searchPatterns);
        
        // Search in UOM names (exact match first, then partial, ordered by priority)
        for (const uom of availableUoms) {
            const uomName = (uom.name || '').toLowerCase().trim();
            console.log(`[findUomByFilter] Checking UOM: "${uom.name}" (normalized: "${uomName}")`);
            
            // Try exact match first (most specific patterns first)
            for (const pattern of searchPatterns) {
                const patternLower = pattern.toLowerCase().trim();
                
                // Exact match
                if (uomName === patternLower) {
                    console.log(`[findUomByFilter] Exact match found: "${uom.name}" for pattern "${pattern}"`);
                    return uom;
                }
                
                // Match with common suffixes
                if (uomName === patternLower + 'g' || 
                    uomName === patternLower + 'غم' || 
                    uomName === patternLower + ' غم' ||
                    uomName === patternLower + 'g' ||
                    uomName === patternLower + 'kg' ||
                    uomName === patternLower + ' كغم' ||
                    uomName === patternLower + ' كيلو') {
                    console.log(`[findUomByFilter] Exact match with suffix found: "${uom.name}" for pattern "${pattern}"`);
                    return uom;
                }
            }
            
            // Try partial match (skip single digits to avoid false matches)
            for (const pattern of searchPatterns) {
                const patternLower = pattern.toLowerCase().trim();
                
                // Skip single digit patterns (like "1") to avoid matching "1" in "125" or "100"
                if (patternLower.length === 1 && /^\d$/.test(patternLower)) {
                    continue;
                }
                
                // For "1KG" filter, be very strict - only match if UOM name contains "kg", "كغم", or "كيلو"
                if (filterValue === '1KG') {
                    // First check: UOM name must NOT contain "0.25", "250", "0.5", "500" to avoid false matches
                    const hasWrongNumbers = uomName.includes('0.25') || 
                                           uomName.includes('250') ||
                                           uomName.includes('0.5') ||
                                           uomName.includes('500') ||
                                           uomName.includes('125') ||
                                           uomName.includes('100') ||
                                           uomName.includes('50');
                    
                    if (hasWrongNumbers) {
                        // Skip this UOM if it contains numbers that indicate it's not 1KG
                        continue;
                    }
                    
                    // Second check: UOM name must contain "kg", "كغم", or "كيلو"
                    const hasKgKeyword = uomName.includes('kg') || 
                                        uomName.includes('كغم') || 
                                        uomName.includes('كيلو') ||
                                        uomName.includes('كيلوغرام');
                    
                    if (!hasKgKeyword) {
                        // Skip this UOM if it doesn't contain kg keywords
                        continue;
                    }
                    
                    // Third check: Pattern must also contain kg keywords
                    const patternHasKg = patternLower.includes('kg') || 
                                        patternLower.includes('كغم') || 
                                        patternLower.includes('كيلو') ||
                                        patternLower.includes('كيلوغرام');
                    
                    if (patternHasKg) {
                        // Check if UOM name matches the pattern
                        if (uomName.includes(patternLower) || patternLower.includes(uomName)) {
                            console.log(`[findUomByFilter] Partial match found: "${uom.name}" for pattern "${pattern}"`);
                            return uom;
                        }
                    }
                } else if (filterValue === '0.5') {
                    // For "0.5" filter, only match if UOM contains "0.5" or "500" (not just "kg" or "كغم")
                    const has05Or500 = uomName.includes('0.5') || 
                                      uomName.includes('500') ||
                                      uomName.includes('0.5kg') ||
                                      uomName.includes('0.5 كغم') ||
                                      uomName.includes('500g') ||
                                      uomName.includes('500غم');
                    
                    if (!has05Or500) {
                        // Skip this UOM if it doesn't contain 0.5 or 500 keywords
                        continue;
                    }
                    
                    // Check if UOM name matches the pattern
                    if (uomName.includes(patternLower) || patternLower.includes(uomName)) {
                        console.log(`[findUomByFilter] Partial match found: "${uom.name}" for pattern "${pattern}"`);
                        return uom;
                    }
                } else if (filterValue === '0.25') {
                    // For "0.25" filter, only match if UOM contains "0.25" or "250" (not just "kg" or "كغم")
                    const has025Or250 = uomName.includes('0.25') || 
                                       uomName.includes('250') ||
                                       uomName.includes('0.25kg') ||
                                       uomName.includes('0.25 كغم') ||
                                       uomName.includes('250g') ||
                                       uomName.includes('250غم');
                    
                    if (!has025Or250) {
                        // Skip this UOM if it doesn't contain 0.25 or 250 keywords
                        continue;
                    }
                    
                    // Check if UOM name matches the pattern
                    if (uomName.includes(patternLower) || patternLower.includes(uomName)) {
                        console.log(`[findUomByFilter] Partial match found: "${uom.name}" for pattern "${pattern}"`);
                        return uom;
                    }
                } else {
                    // For other filters (125, 100, 50), use normal partial match but be careful
                    // Skip if pattern is just a number and UOM contains other numbers
                    if (/^\d+$/.test(patternLower)) {
                        // If pattern is just a number, make sure UOM name contains this exact number
                        // and not as part of another number (e.g., "125" should not match "1250")
                        const numberPattern = new RegExp(`\\b${patternLower}\\b`);
                        if (numberPattern.test(uomName)) {
                            console.log(`[findUomByFilter] Partial match found: "${uom.name}" for pattern "${pattern}"`);
                            return uom;
                        }
                    } else {
                        // For non-numeric patterns, use normal partial match
                        if (uomName.includes(patternLower) || patternLower.includes(uomName)) {
                            console.log(`[findUomByFilter] Partial match found: "${uom.name}" for pattern "${pattern}"`);
                            return uom;
                        }
                    }
                }
            }
        }
        
        // If not found, log warning and return null (don't return first UOM automatically)
        console.warn(`[findUomByFilter] No matching UOM found for filter: ${filterValue}`);
        return null;
    }
    
    openProductPopupHandler(lineIndex) {
        const key = `openProductPopup_${lineIndex}`;
        return this.getHandler(key, () => () => this.openProductPopup(lineIndex));
    }
    
    // Handler methods for filter functions
    toggleBrandFilterHandler(brand) {
        const key = `toggleBrandFilter_${brand}`;
        return this.getHandler(key, () => () => this.toggleBrandFilter(brand));
    }
    
    toggleUnitFilterHandler(unit) {
        const key = `toggleUnitFilter_${unit.filter}`;
        return this.getHandler(key, () => () => this.toggleUnitFilter(unit));
    }
    
    togglePlasticFilterHandler(value) {
        const key = `togglePlasticFilter_${value}`;
        return this.getHandler(key, () => () => this.togglePlasticFilter(value));
    }
    
    isBrandFilterActiveHandler(brand) {
        const key = `isBrandFilterActive_${brand}`;
        return this.getHandler(key, () => () => this.isBrandFilterActive(brand));
    }
    
    isUnitFilterActiveHandler(filter) {
        const key = `isUnitFilterActive_${filter}`;
        return this.getHandler(key, () => () => this.isUnitFilterActive(filter));
    }
    
    /**
     * Open edit product name popup
     */
    openEditProductName(lineIndex) {
        if (lineIndex < 0 || lineIndex >= this.state.currentOrder.lines.length) {
            return;
        }
        const line = this.state.currentOrder.lines[lineIndex];
        if (!line.product_id) {
            return;
        }
        // Initialize customProductName if not set
        if (!line.customProductName) {
            line.customProductName = line.productName || '';
        }
        line.showEditProductNamePopup = true;
    }
    
    /**
     * Handle custom product name input
     */
    onCustomProductNameInput(lineIndex, value) {
        if (lineIndex < 0 || lineIndex >= this.state.currentOrder.lines.length) {
            return;
        }
        const line = this.state.currentOrder.lines[lineIndex];
        line.customProductName = value;
    }
    
    /**
     * Handle custom product name keydown
     */
    handleCustomProductNameKeyDown(lineIndex, event) {
        if (event.key === 'Enter') {
            this.saveCustomProductName(lineIndex);
        } else if (event.key === 'Escape') {
            this.cancelEditProductName(lineIndex);
        }
    }
    
    /**
     * Save custom product name
     */
    saveCustomProductName(lineIndex) {
        if (lineIndex < 0 || lineIndex >= this.state.currentOrder.lines.length) {
            return;
        }
        const line = this.state.currentOrder.lines[lineIndex];
        // Trim and save
        if (line.customProductName && line.customProductName.trim()) {
            line.customProductName = line.customProductName.trim();
        } else {
            line.customProductName = null;
        }
        line.showEditProductNamePopup = false;
    }
    
    /**
     * Cancel edit product name
     */
    cancelEditProductName(lineIndex) {
        if (lineIndex < 0 || lineIndex >= this.state.currentOrder.lines.length) {
            return;
        }
        const line = this.state.currentOrder.lines[lineIndex];
        // Reset to original product name
        line.customProductName = null;
        line.showEditProductNamePopup = false;
    }
    
    /**
     * Handler for openEditProductName
     */
    openEditProductNameHandler(lineIndex) {
        return () => this.openEditProductName(lineIndex);
    }
    
    /**
     * Handler for saveCustomProductName
     */
    saveCustomProductNameHandler(lineIndex) {
        return () => this.saveCustomProductName(lineIndex);
    }
    
    /**
     * Handler for cancelEditProductName
     */
    cancelEditProductNameHandler(lineIndex) {
        return () => this.cancelEditProductName(lineIndex);
    }
    
    /**
     * Handle invoice type change
     */
    onInvoiceTypeChange(ev) {
        this.state.currentOrder.invoice_type = ev.target.value || null;
    }
    
    /**
     * Handle note change
     */
    onNoteChange(ev) {
        this.state.currentOrder.note = ev.target.value || '';
    }
    
    /**
     * Get customer ID as number or null for CustomerSearch component
     */
    getCustomerIdForSearch() {
        const partnerId = this.state.currentOrder.partner_id;
        if (!partnerId) return null;
        if (typeof partnerId === 'number') return partnerId;
        if (Array.isArray(partnerId)) return partnerId[0] ? Number(partnerId[0]) : null;
        return Number(partnerId) || null;
    }
    
    /**
     * Add custom notification (bottom right, auto-hide)
     */
    addCustomNotification(message, type = 'info') {
        // Remove previous notification if exists (only show one at a time)
        if (this.state.customNotifications.length > 0) {
            this.state.customNotifications = [];
        }
        
        const notification = {
            id: `notif_${Date.now()}_${++this.notificationCounter}`,
            message: message,
            type: type, // 'success', 'danger', 'warning', 'info'
            timestamp: Date.now()
        };
        
        this.state.customNotifications.push(notification);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            this.removeCustomNotification(notification.id);
        }, 4000);
    }
    
    /**
     * Remove custom notification with fade out animation
     */
    removeCustomNotification(notificationId) {
        const index = this.state.customNotifications.findIndex(n => n.id === notificationId);
        if (index !== -1) {
            const notification = this.state.customNotifications[index];
            
            // Add slide-out class for animation
            setTimeout(() => {
                const notificationElement = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (notificationElement) {
                    notificationElement.classList.add('slide-out');
                }
                
                // Remove from state after animation
                setTimeout(() => {
                    const idx = this.state.customNotifications.findIndex(n => n.id === notificationId);
                    if (idx !== -1) {
                        this.state.customNotifications.splice(idx, 1);
                    }
                }, 300); // Match animation duration
            }, 0);
        }
    }
    
    /**
     * Override notification.add to use custom notifications
     */
    showNotification(message, options = {}) {
        const type = options.type || 'info';
        this.addCustomNotification(message, type);
        
        // Also show in Odoo notification system (optional - can be removed)
        // this.notification.add(message, options);
    }
}

