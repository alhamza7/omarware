# خطة تطبيق نظام الفلترة في POS Perfume

## نظرة عامة
تطبيق نظام فلترة متعدد المستويات على قائمة المنتجات في واجهة POS Perfume بناءً على:
- العلامات التجارية (Brands)
- الوحدات (Units)
- نوع المنتج (فل بلاستك)

---

## 1. التعديلات على State (pos_perfume_screen.js)

### إضافة المتغيرات التالية في `this.state`:

```javascript
// Filter state
activeFilters: [],                      // Array of active brand filters
activeUnitFilter: null,                 // Active unit filter object or null
fullPlasticFilterActive: null,          // true/false/null for full plastic filter
rightSearchResultsOriginal: [],         // Original search results before filtering
```

---

## 2. التعديلات على XML (pos_perfume_screen.xml)

### إضافة قسم الفلاتر أعلى جدول البحث (بعد Search Bar):

```xml
<!-- Filters Section - Above Products Table -->
<div style="padding: 12px 16px; background: #f9fafb; border-bottom: 1px solid #e5e7eb;">
    <!-- Brand Filters -->
    <div style="margin-bottom: 12px;">
        <label style="font-size: 12px; font-weight: 600; color: #4b5563; margin-bottom: 6px; display: block;">
            Brands:
        </label>
        <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <button t-foreach="['ADF', 'ROYAL', 'GIVAUDAN', 'EURO']" t-as="brand"
                    t-on-click="toggleBrandFilter(brand)"
                    t-att-class="this.isBrandFilterActive(brand) ? 'filter-btn active' : 'filter-btn'"
                    style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer; font-size: 12px; transition: all 0.2s;">
                <t t-esc="brand"/>
            </button>
        </div>
    </div>
    
    <!-- Unit Filters -->
    <div style="margin-bottom: 12px;">
        <label style="font-size: 12px; font-weight: 600; color: #4b5563; margin-bottom: 6px; display: block;">
            Units:
        </label>
        <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <button t-foreach="[{filter: '1KG', name: '1KG'}, {filter: '0.5', name: '0.5KG'}, {filter: '50', name: '50g'}, {filter: '100', name: '100g'}, {filter: '125', name: '125g'}, {filter: '0.25', name: '0.25KG'}]" t-as="unit"
                    t-on-click="toggleUnitFilter(unit)"
                    t-att-class="this.isUnitFilterActive(unit.filter) ? 'filter-btn active' : 'filter-btn'"
                    style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer; font-size: 12px; transition: all 0.2s;">
                <t t-esc="unit.name"/>
            </button>
        </div>
    </div>
    
    <!-- Full Plastic Filter -->
    <div>
        <label style="font-size: 12px; font-weight: 600; color: #4b5563; margin-bottom: 6px; display: block;">
            Full Plastic:
        </label>
        <div style="display: flex; gap: 6px;">
            <button t-on-click="togglePlasticFilter(true)"
                    t-att-class="state.fullPlasticFilterActive === true ? 'filter-btn active' : 'filter-btn'"
                    style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer; font-size: 12px; transition: all 0.2s;">
                Show All
            </button>
            <button t-on-click="togglePlasticFilter(false)"
                    t-att-class="state.fullPlasticFilterActive === false ? 'filter-btn active' : 'filter-btn'"
                    style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer; font-size: 12px; transition: all 0.2s;">
                Hide Full Plastic
            </button>
            <button t-on-click="togglePlasticFilter(null)"
                    t-att-class="state.fullPlasticFilterActive === null ? 'filter-btn active' : 'filter-btn'"
                    style="padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; background: white; cursor: pointer; font-size: 12px; transition: all 0.2s;">
                Reset
            </button>
        </div>
    </div>
</div>
```

---

## 3. الدوال المطلوبة في JS

### 3.1 دوال UI للفلاتر:

```javascript
// Toggle brand filter
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

// Toggle unit filter
toggleUnitFilter(unit) {
    if (this.state.activeUnitFilter && this.state.activeUnitFilter.filter === unit.filter) {
        this.state.activeUnitFilter = null;
    } else {
        this.state.activeUnitFilter = unit;
    }
    this.applyFiltersToResults();
}

// Toggle plastic filter
togglePlasticFilter(value) {
    this.state.fullPlasticFilterActive = value;
    this.applyFiltersToResults();
}

// Check if brand filter is active
isBrandFilterActive(brand) {
    return this.state.activeFilters.some(f => f.prefix === brand);
}

// Check if unit filter is active
isUnitFilterActive(filter) {
    return this.state.activeUnitFilter && this.state.activeUnitFilter.filter === filter;
}
```

### 3.2 دوال الفلترة:

```javascript
// Apply all filters to search results
applyFiltersToResults() {
    // Use original results if available, otherwise use current results
    const sourceProducts = this.state.rightSearchResultsOriginal || this.state.rightSearchResults || [];
    
    if (sourceProducts.length === 0) {
        this.state.rightSearchResults = [];
        return;
    }
    
    let filtered = [...sourceProducts];
    
    // 1. Filter by brands
    filtered = this.filterProductsByBrand(filtered);
    
    // 2. Filter by plastic
    filtered = this.filterProductsByPlastic(filtered);
    
    // 3. Filter by units (1KG, 0.5, 50, 100, 125 special case)
    filtered = this.filterProductsBy025KgUnit(filtered);
    
    // Update results
    this.state.rightSearchResults = filtered;
}

// Filter products by brand
// عند اختيار براند واحد: إظهار منتجات هذا البراند فقط
// عند اختيار عدة براندات: إظهار منتجات أي من البراندات المختارة (OR logic)
// إذا لم يتم اختيار أي براند: إظهار جميع المنتجات
filterProductsByBrand(products) {
    if (!this.state.activeFilters || this.state.activeFilters.length === 0) {
        return products; // لا توجد فلاتر نشطة، إرجاع جميع المنتجات
    }
    
    return products.filter(product => {
        const sku = product.sub_sku || product.default_code || '';
        const name = product.name || '';
        
        // التحقق من مطابقة المنتج مع أي من البراندات النشطة (OR logic)
        return this.state.activeFilters.some(filter => {
            // حالات خاصة
            if (filter.prefix === 'EURO') {
                // EURO: التحقق من وجود "EURO" في الاسم أو "N1" في SKU
                return name.includes('EURO') || sku.includes('N1');
            }
            if (filter.prefix === 'FL') {
                // FL: التحقق من وجود "FLOR" في الاسم
                return name.includes('FLOR');
            }
            
            // الحالة الافتراضية: التحقق من أن SKU يبدأ ببادئة البراند
            // ADF -> SKU يبدأ بـ "ADF"
            // ROYAL -> SKU يبدأ بـ "R"
            // GIVAUDAN -> SKU يبدأ بـ "G"
            return sku.startsWith(filter.prefix);
        });
    });
}

// Filter products by plastic
filterProductsByPlastic(products) {
    if (this.state.fullPlasticFilterActive === false) {
        return products.filter(product => !this.isFullPlasticProduct(product));
    }
    return products;
}

// Check if product is full plastic
isFullPlasticProduct(product) {
    const keywords = ['فل بلاستك', 'فل بلاستيك', 'full plastic', 'fl plastic'];
    
    // Check unit
    if (product.unit) {
        const unitName = typeof product.unit === 'string' ? product.unit : product.unit.name || '';
        if (keywords.some(kw => unitName.toLowerCase().includes(kw.toLowerCase()))) {
            return true;
        }
    }
    
    // Check processed_units, units, sub_units
    const allUnits = [
        ...(product.processed_units || []),
        ...(product.units || []),
        ...(product.sub_units || [])
    ];
    
    for (const unit of allUnits) {
        const unitName = typeof unit === 'string' ? unit : unit.name || '';
        if (keywords.some(kw => unitName.toLowerCase().includes(kw.toLowerCase()))) {
            return true;
        }
    }
    
    // Check name and description
    const name = (product.name || '').toLowerCase();
    const desc = (product.description || '').toLowerCase();
    if (keywords.some(kw => name.includes(kw.toLowerCase()) || desc.includes(kw.toLowerCase()))) {
        return true;
    }
    
    return false;
}

// Filter products by 0.25KG unit
filterProductsBy025KgUnit(products) {
    if (!this.state.activeUnitFilter) {
        return products;
    }
    
    const specialFilters = ['1KG', '0.5', '50', '100', '125'];
    if (!specialFilters.includes(this.state.activeUnitFilter.filter)) {
        return products;
    }
    
    return products.filter(product => {
        if (this.shouldHideProduct(product)) {
            return false;
        }
        return true;
    });
}

// Check if product should be hidden
shouldHideProduct(product) {
    // Get UOM name from product (check sap_uom_group_name, uom_name, or unit)
    let uomName = '';
    if (product.sap_uom_group_name) {
        uomName = product.sap_uom_group_name;
    } else if (product.uom_name) {
        uomName = product.uom_name;
    } else if (product.unit) {
        uomName = typeof product.unit === 'string' ? product.unit : product.unit.name || '';
    } else if (product.units && product.units.length > 0) {
        uomName = typeof product.units[0] === 'string' ? product.units[0] : product.units[0].name || '';
    }
    
    const uomNameLower = uomName.toLowerCase();
    
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
```

### 3.3 تعديل searchRightPanel:

```javascript
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
            
            // Apply filters
            this.state.rightSearchResults = products;
            this.applyFiltersToResults();
            
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
```

---

## 4. إضافة CSS للفلاتر (اختياري)

```css
.filter-btn {
    padding: 6px 12px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;
}

.filter-btn:hover {
    background: #f3f4f6;
    border-color: #2563eb;
}

.filter-btn.active {
    background: #2563eb;
    color: white;
    border-color: #2563eb;
}
```

---

### 3.4 تعديل addProductFromRightPanel لاختيار الوحدة تلقائياً:

```javascript
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
    
    // Auto-select UOM based on active unit filter
    if (this.state.activeUnitFilter && line.availableUoms && line.availableUoms.length > 0) {
        const targetUnit = this.findUomByFilter(line.availableUoms, this.state.activeUnitFilter.filter);
        if (targetUnit) {
            line.uom_id = targetUnit.id;
            line.uomName = targetUnit.name;
            line.uomValid = true;
            
            // Update price if available
            if (targetUnit.price !== undefined) {
                line.unitPrice = targetUnit.price;
            } else {
                // Call onchange to get price
                await this.onUomChange(lineIndex);
            }
            
            this.calculateLine(line);
            this.calculateTotals();
        }
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

// Find UOM by filter value (e.g., "125" -> "125g" or "125 غم")
findUomByFilter(availableUoms, filterValue) {
    if (!availableUoms || availableUoms.length === 0) {
        return null;
    }
    
    // Map filter values to search patterns
    const filterMap = {
        '125': ['125', '125g', '125 غم', '125g', '125 جرام'],
        '100': ['100', '100g', '100 غم', '100g', '100 جرام'],
        '50': ['50', '50g', '50 غم', '50g', '50 جرام'],
        '0.5': ['0.5', '0.5kg', '0.5 كغم', '500', '500g', '500 غم'],
        '1KG': ['1', '1kg', '1 كغم', '1000', '1000g', '1000 غم'],
        '0.25': ['0.25', '0.25kg', '0.25 كغم', '250', '250g', '250 غم']
    };
    
    const searchPatterns = filterMap[filterValue] || [filterValue];
    
    // Search in UOM names
    for (const uom of availableUoms) {
        const uomName = (uom.name || '').toLowerCase();
        for (const pattern of searchPatterns) {
            if (uomName.includes(pattern.toLowerCase())) {
                return uom;
            }
        }
    }
    
    // If not found, return first UOM
    return availableUoms[0];
}
```

---

## 5. ترتيب التنفيذ

1. ✅ إضافة المتغيرات في state (activeFilters, activeUnitFilter, fullPlasticFilterActive, rightSearchResultsOriginal)
2. ✅ إضافة واجهة الفلاتر في XML (أعلى جدول البحث)
3. ✅ إضافة دوال UI (toggleBrandFilter, toggleUnitFilter, togglePlasticFilter, isBrandFilterActive, isUnitFilterActive)
4. ✅ إضافة دوال الفلترة (filterProductsByBrand, filterProductsByPlastic, filterProductsBy025KgUnit, isFullPlasticProduct, shouldHideProduct)
5. ✅ إضافة دالة applyFiltersToResults
6. ✅ تعديل searchRightPanel لتطبيق الفلاتر
7. ✅ تعديل addProductFromRightPanel لاختيار الوحدة تلقائياً
8. ✅ إضافة دالة findUomByFilter
9. ✅ اختبار النظام

---

## ملاحظات مهمة

1. **الأداء**: الفلترة تتم في الذاكرة، لذا يجب الحذر مع قوائم كبيرة
2. **الترتيب**: تطبيق الفلاتر بالترتيب: Brands → Plastic → Units
3. **الحالات الفارغة**: التحقق من وجود البيانات قبل التطبيق
4. **التوافق**: النظام يعمل مع بيانات من API قد تكون بنيات مختلفة

---

## متطلبات خاصة للفلترة

### 1. فلترة حسب البراندات:

**عند اختيار براند واحد (مثلاً ADF):**
- إظهار **فقط** المنتجات التي تبدأ SKU الخاصة بها بـ "ADF"
- إخفاء جميع المنتجات الأخرى

**عند اختيار عدة براندات (مثلاً ADF + ROYAL):**
- إظهار المنتجات التي تبدأ SKU الخاصة بها بـ "ADF" **أو** "R"
- منطق OR: المنتج يظهر إذا طابق أي من البراندات المختارة

**حالات خاصة:**
- **EURO**: التحقق من وجود "EURO" في الاسم أو "N1" في SKU
- **ROYAL**: SKU يبدأ بـ "R"
- **GIVAUDAN**: SKU يبدأ بـ "G"
- **ADF**: SKU يبدأ بـ "ADF"

**مثال:**
- المستخدم يختار براند "ADF"
- يظهر فقط المنتجات التي SKU الخاصة بها يبدأ بـ "ADF"
- عند اختيار "ADF" + "ROYAL": يظهر منتجات ADF و ROYAL معاً

---

### 2. فلترة حسب الوحدات (مثلاً 125g):

**عند اختيار فلتر الوحدة (مثلاً 125g):**

1. **فلترة المنتجات:**
   - إخفاء جميع المنتجات الأخرى
   - إظهار فقط:
     - المنتجات التي UOM = "لك" (دائماً)
     - المنتجات التي UOM = "فل بلاستك" (فقط إذا كان `fullPlasticFilterActive === true`)

2. **عند إضافة المنتج:**
   - إضافة المنتج إلى الجدول
   - **اختيار الوحدة 125g تلقائياً** من قائمة الوحدات المتاحة
   - تحديث السعر حسب الوحدة المختارة

**مثال:**
- المستخدم يختار فلتر "125g"
- يظهر فقط منتجات "لك" و"فل بلاستك" (إذا كان فلتر فل بلاستك مفعلاً)
- عند النقر على منتج، يتم إضافته مع اختيار وحدة "125g" تلقائياً

---

### 3. ترتيب تطبيق الفلاتر:

1. **أولاً**: فلاتر البراندات (تضييق القائمة)
2. **ثانياً**: فلتر فل بلاستك (استبعاد/إضافة)
3. **ثالثاً**: فلتر الوحدات (تضييق إضافي)

**مثال متكامل:**
- براند: ADF
- فل بلاستك: Show All (true)
- وحدة: 125g
- **النتيجة**: منتجات ADF فقط، من نوع "لك" أو "فل بلاستك"، مع اختيار وحدة 125g تلقائياً عند الإضافة

