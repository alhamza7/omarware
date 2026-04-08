/** @odoo-module */

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Product Search with UoM Selection Component
 * Component للبحث عن المنتجات واختيار وحدة القياس
 */
export class ProductSearchWithUoM extends Component {
    static template = "pos_perfume_custom.ProductSearchWithUoM";
    static props = {
        pricelistId: { type: Number, optional: true },
        warehouseCode: { type: String, optional: true },
        onAddProduct: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            searchTerm: '',
            products: [],
            selectedProduct: null,
            availableUoms: [],
            selectedUom: null,
            priceInfo: null,
            loading: false,
            searchFocused: false,
        });
        
        this.searchInputRef = useRef("searchInput");
    }
    
    /**
     * البحث عن المنتجات
     * Search for products
     */
    async searchProducts(term) {
        if (!term || term.length < 2) {
            this.state.products = [];
            return;
        }
        
        this.state.loading = true;
        
        try {
            // استخدام Method المخصص من Backend
            const products = await this.orm.call(
                'product.product',
                'search_products_for_pos',
                [term, 50]
            );
            
            this.state.products = products;
        } catch (error) {
            console.error('Error searching products:', error);
            this.notification.add(
                _t('Error searching products'),
                { type: 'danger' }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * اختيار منتج
     * Select a product
     */
    async selectProduct(product) {
        this.state.selectedProduct = product;
        this.state.loading = true;
        
        try {
            // جلب وحدات القياس المتاحة مع الأسعار
            const pricelistId = this.props.pricelistId || 1;
            const warehouseCode = this.props.warehouseCode || null;
            
            const uoms = await this.orm.call(
                'product.product',
                'get_available_uoms_with_prices',
                [product.id, pricelistId, warehouseCode]
            );
            
            this.state.availableUoms = uoms;
            
            // اختيار أول وحدة تلقائياً
            if (uoms.length > 0) {
                await this.selectUom(uoms[0]);
            }
        } catch (error) {
            console.error('Error loading UoMs:', error);
            this.notification.add(
                _t('Error loading units of measure'),
                { type: 'danger' }
            );
        } finally {
            this.state.loading = false;
        }
    }
    
    /**
     * اختيار وحدة قياس
     * Select a UoM
     */
    async selectUom(uom) {
        this.state.selectedUom = uom;
        this.state.priceInfo = {
            price: uom.price,
            price_iqd: uom.price_iqd,
            uom_name: uom.name,
            quantity_info: uom.quantity_info,
            stock_info: uom.stock_info || null,
        };
    }
    
    /**
     * إضافة المنتج إلى الطلب
     * Add product to order
     */
    addToOrder() {
        if (!this.state.selectedProduct || !this.state.selectedUom) {
            this.notification.add(
                _t('Please select a product and unit of measure'),
                { type: 'warning' }
            );
            return;
        }
        
        // إرسال البيانات إلى الكومبوننت الأب
        this.props.onAddProduct({
            product_id: this.state.selectedProduct.id,
            product_name: this.state.selectedProduct.name,
            product_code: this.state.selectedProduct.default_code,
            foreign_name: this.state.selectedProduct.foreign_name,
            uom_id: this.state.selectedUom.id,
            uom_name: this.state.selectedUom.name,
            price: this.state.priceInfo.price,
            price_iqd: this.state.priceInfo.price_iqd,
            quantity: 1,
        });
        
        // إعادة تعيين
        this.resetSearch();
        
        this.notification.add(
            _t('Product added to order'),
            { type: 'success' }
        );
    }
    
    /**
     * إعادة تعيين البحث
     * Reset search
     */
    resetSearch() {
        this.state.searchTerm = '';
        this.state.products = [];
        this.state.selectedProduct = null;
        this.state.availableUoms = [];
        this.state.selectedUom = null;
        this.state.priceInfo = null;
        
        // Focus on search input
        if (this.searchInputRef.el) {
            this.searchInputRef.el.focus();
        }
    }
    
    /**
     * Format price for display
     */
    formatPrice(price) {
        return price ? price.toFixed(2) : '0.00';
    }
    
    /**
     * Format IQD price for display
     */
    formatPriceIQD(price) {
        return price ? Math.round(price).toLocaleString() : '0';
    }
}

