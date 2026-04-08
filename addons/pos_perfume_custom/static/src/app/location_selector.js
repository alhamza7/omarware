/** @odoo-module */

import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Location Selector Component
 * Component لاختيار المستودع والموقع
 */
export class LocationSelector extends Component {
    static template = "pos_perfume_custom.LocationSelector";
    static props = {
        productId: { type: Number, optional: true },
        onSelectWarehouse: Function,
        onSelectLocation: { type: Function, optional: true },
        selectedWarehouseId: { type: Number, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            warehouses: [],
            selectedWarehouse: null,
            locations: [],
            selectedLocation: null,
            stockInfo: null,
            loading: false,
        });
        
        onMounted(async () => {
            await this.loadWarehouses();
            
            // Load selected warehouse if provided
            if (this.props.selectedWarehouseId) {
                const warehouse = this.state.warehouses.find(w => w.id === this.props.selectedWarehouseId);
                if (warehouse) {
                    await this.selectWarehouse(warehouse);
                }
            }
        });
    }
    
    /**
     * تحميل المستودعات
     * Load warehouses
     */
    async loadWarehouses() {
        this.state.loading = true;
        
        try {
            const warehouses = await this.orm.searchRead(
                'stock.warehouse',
                [],
                ['id', 'name', 'code', 'lot_stock_id'],
                { order: 'name' }
            );
            
            this.state.warehouses = warehouses;
            
            // Select first warehouse by default if none selected
            if (!this.state.selectedWarehouse && warehouses.length > 0) {
                await this.selectWarehouse(warehouses[0]);
            }
        } catch (error) {
            console.error('Error loading warehouses:', error);
            this.notification.add(
                _t('Error loading warehouses'),
                { type: 'danger' }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * اختيار مستودع
     * Select a warehouse
     */
    async selectWarehouse(warehouse) {
        this.state.selectedWarehouse = warehouse;
        this.state.loading = true;
        
        try {
            // Load locations for this warehouse
            if (warehouse.lot_stock_id && warehouse.lot_stock_id[0]) {
                const locations = await this.orm.searchRead(
                    'stock.location',
                    [['id', 'child_of', warehouse.lot_stock_id[0]]],
                    ['id', 'name', 'complete_name'],
                    { order: 'complete_name' }
                );
                
                this.state.locations = locations;
                
                // Select main location by default
                if (locations.length > 0) {
                    const mainLocation = locations.find(l => l.id === warehouse.lot_stock_id[0]) || locations[0];
                    this.state.selectedLocation = mainLocation;
                }
            }
            
            // Load stock info if product provided
            if (this.props.productId && warehouse.code) {
                await this.loadStockInfo(this.props.productId, warehouse.code);
            }
            
            // Notify parent
            this.props.onSelectWarehouse({
                id: warehouse.id,
                name: warehouse.name,
                code: warehouse.code,
                location_id: this.state.selectedLocation ? this.state.selectedLocation.id : null,
            });
            
        } catch (error) {
            console.error('Error selecting warehouse:', error);
            this.notification.add(
                _t('Error loading warehouse details'),
                { type: 'danger' }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * اختيار موقع
     * Select a location
     */
    selectLocation(location) {
        this.state.selectedLocation = location;
        
        // Notify parent if callback provided
        if (this.props.onSelectLocation) {
            this.props.onSelectLocation({
                id: location.id,
                name: location.name,
                complete_name: location.complete_name,
            });
        }
    }
    
    /**
     * تحميل معلومات المخزون
     * Load stock information from SAP
     */
    async loadStockInfo(productId, warehouseCode) {
        try {
            // Try to get stock info from SAP integration
            const stockInfo = await this.orm.searchRead(
                'sap.product.warehouse.info',
                [
                    ['product_id', '=', productId],
                    ['warehouse_code', '=', warehouseCode],
                ],
                ['on_hand', 'committed', 'available', 'warehouse_name'],
                { limit: 1 }
            );
            
            if (stockInfo.length > 0) {
                this.state.stockInfo = stockInfo[0];
            } else {
                // Fallback to Odoo stock
                await this.loadOdooStock(productId);
            }
        } catch (error) {
            console.error('Error loading stock info:', error);
            this.state.stockInfo = null;
        }
    }
    
    /**
     * Load stock from Odoo (fallback)
     */
    async loadOdooStock(productId) {
        try {
            if (!this.state.selectedLocation) {
                return;
            }
            
            const quants = await this.orm.searchRead(
                'stock.quant',
                [
                    ['product_id', '=', productId],
                    ['location_id', '=', this.state.selectedLocation.id],
                ],
                ['quantity', 'reserved_quantity']
            );
            
            const totalQty = quants.reduce((sum, q) => sum + q.quantity, 0);
            const reservedQty = quants.reduce((sum, q) => sum + q.reserved_quantity, 0);
            
            this.state.stockInfo = {
                on_hand: totalQty,
                committed: reservedQty,
                available: totalQty - reservedQty,
                source: 'Odoo',
            };
        } catch (error) {
            console.error('Error loading Odoo stock:', error);
        }
    }
    
    /**
     * Format quantity for display
     */
    formatQty(qty) {
        return qty ? qty.toFixed(2) : '0.00';
    }
    
    /**
     * Get stock status color
     */
    getStockStatusClass() {
        if (!this.state.stockInfo) {
            return '';
        }
        
        const available = this.state.stockInfo.available || 0;
        
        if (available <= 0) {
            return 'text-danger';
        } else if (available < 10) {
            return 'text-warning';
        } else {
            return 'text-success';
        }
    }
}

