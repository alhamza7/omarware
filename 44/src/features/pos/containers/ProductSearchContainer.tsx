import { useState, useCallback, useEffect, useMemo } from 'react';
import { usePosStore } from '../store/posStore';
import { useProductSearch } from '../hooks/useProductSearch';
import { useOrder } from '../hooks/useOrder';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Separator } from '../../../components/ui/separator';
import {
  Search, Loader2, Package, ArrowLeft,
  Warehouse, Tag, Hash, AlertCircle,
} from 'lucide-react';
import type { Product } from '../../../types/pos';
import type { ProductDetail } from '../hooks/useProductSearch';

type Step = 'search' | 'config';

interface ProductSearchContainerProps {
  open:         boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Two-step product modal:
 *   Step 1 — search products (lightweight list)
 *   Step 2 — configure: select UoM, warehouse, qty, discount, price → add to order
 */
export function ProductSearchContainer({ open, onOpenChange }: ProductSearchContainerProps) {
  const store = usePosStore();
  const { results, isSearching, searchError, productDetail, isLoadingDetail, search, loadProductDetail, fetchUomPrice, clearResults } = useProductSearch();
  const { addLine } = useOrder();

  // ── Step state ──────────────────────────────────────────────
  const [step,        setStep]        = useState<Step>('search');
  const [searchTerm,  setSearchTerm]  = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // ── Config state (step 2) ───────────────────────────────────
  const [selectedUomId,       setSelectedUomId]       = useState<number | null>(null);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<number | null>(null);
  const [qty,                 setQty]                 = useState<number>(1);
  const [unitPrice,           setUnitPrice]           = useState<number>(0);
  const [discount,            setDiscount]            = useState<number>(0);
  const [isLoadingPrice,      setIsLoadingPrice]      = useState(false);
  const [isAdding,            setIsAdding]            = useState(false);
  const [configError,         setConfigError]         = useState<string | null>(null);

  // ── Reset when modal closes ──────────────────────────────────
  useEffect(() => {
    if (!open) {
      setStep('search');
      setSearchTerm('');
      setSelectedProduct(null);
      setSelectedUomId(null);
      setSelectedWarehouseId(null);
      setQty(1);
      setUnitPrice(0);
      setDiscount(0);
      setConfigError(null);
      clearResults();
    }
  }, [open, clearResults]);

  // ── Auto-populate config when productDetail loads ────────────
  useEffect(() => {
    if (!productDetail) return;

    // Default UoM = first in available_uoms (or base)
    const firstUom = productDetail.available_uoms?.[0];
    const defaultUomId = firstUom?.id ?? productDetail.product_uom_id;
    setSelectedUomId(defaultUomId);
    setUnitPrice(firstUom?.price ?? productDetail.price_unit ?? 0);

    // Default warehouse = store.warehouseId or first warehouse
    const storeWh = store.warehouseId;
    const firstWh = productDetail.warehouses?.[0]?.id;
    setSelectedWarehouseId(storeWh ?? firstWh ?? null);

    setQty(1);
    setDiscount(0);
    setConfigError(null);
  }, [productDetail, store.warehouseId]);

  // ── Derived totals ────────────────────────────────────────────
  const lineSubtotal   = qty * unitPrice;
  const discountAmount = lineSubtotal * (discount / 100);
  const lineTotal      = lineSubtotal - discountAmount;
  const lineTotalIqd   = Math.round(lineTotal * store.exchangeRate);

  /** Stock for the currently selected warehouse */
  const selectedWarehouseQty = useMemo(() => {
    if (!productDetail || !selectedWarehouseId) return null;
    return productDetail.warehouses?.find((w) => w.id === selectedWarehouseId)?.quantity ?? null;
  }, [productDetail, selectedWarehouseId]);

  // ── Handlers ──────────────────────────────────────────────────

  const handleSearchChange = useCallback((val: string) => {
    setSearchTerm(val);
    search(val, store.pricelistId ?? undefined);
  }, [search, store.pricelistId]);

  /** User clicks a product in the list → load full detail */
  const handleSelectProduct = useCallback(async (product: Product) => {
    setSelectedProduct(product);
    setStep('config');
    setConfigError(null);

    const warehouseId = store.warehouseId
      ?? store.setup?.warehouses?.[0]?.id
      ?? undefined;

    await loadProductDetail(
      product.id,
      store.pricelistId ?? undefined,
      warehouseId,
    );
  }, [store, loadProductDetail]);

  /** When UoM changes → fetch updated price */
  const handleUomChange = useCallback(async (uomId: number) => {
    setSelectedUomId(uomId);

    // First try local price from available_uoms
    const localUom = productDetail?.available_uoms?.find((u) => u.id === uomId);
    if (localUom) {
      setUnitPrice(localUom.price);
      return;
    }

    // Fallback: fetch from API
    if (store.pricelistId && selectedProduct) {
      setIsLoadingPrice(true);
      const price = await fetchUomPrice(selectedProduct.id, store.pricelistId, uomId);
      if (price !== null) setUnitPrice(price);
      setIsLoadingPrice(false);
    }
  }, [productDetail, store.pricelistId, selectedProduct, fetchUomPrice]);

  /** Confirm → add line to order */
  const handleAddToOrder = useCallback(async () => {
    if (!selectedProduct) return;

    const warehouseId = selectedWarehouseId
      ?? store.warehouseId
      ?? store.setup?.warehouses?.[0]?.id;

    if (!warehouseId) {
      setConfigError('Select a warehouse first');
      return;
    }
    if (qty <= 0) {
      setConfigError('Quantity must be greater than 0');
      return;
    }

    setIsAdding(true);
    setConfigError(null);
    try {
      await addLine({
        product_id:      selectedProduct.id,
        product_uom_id:  selectedUomId ?? undefined,
        warehouse_id:    warehouseId,
        quantity:        qty,
        unit_price:      unitPrice,
        discount_percent: discount,
      });
      onOpenChange(false);
    } catch (err) {
      setConfigError(err instanceof Error ? err.message : 'Failed to add product');
    } finally {
      setIsAdding(false);
    }
  }, [selectedProduct, selectedWarehouseId, store, qty, selectedUomId, unitPrice, discount, addLine, onOpenChange]);

  // ── Render ─────────────────────────────────────────────────────
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl p-0 gap-0">

        {/* Header */}
        <DialogHeader className="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
          <div className="flex items-center gap-3">
            {step === 'config' && (
              <button
                onClick={() => { setStep('search'); setSelectedProduct(null); }}
                className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
            )}
            <DialogTitle className="text-xl">
              {step === 'search' ? 'Product Search' : 'Configure Product'}
            </DialogTitle>
            {step === 'search' && isSearching && (
              <Loader2 className="w-4 h-4 animate-spin ml-auto" />
            )}
          </div>
        </DialogHeader>

        {/* ── Step 1: Search ───────────────────────────────────── */}
        {step === 'search' && (
          <div className="p-6 space-y-4">
            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                placeholder="Search by code, name, barcode..."
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10 h-11 border-gray-300 focus:border-blue-500"
                autoFocus
              />
            </div>

            {searchError && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {searchError}
              </div>
            )}

            {/* Empty state */}
            {searchTerm.length < 1 && (
              <div className="flex flex-col items-center py-14 text-center">
                <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mb-4">
                  <Package className="w-10 h-10 text-blue-300" />
                </div>
                <p className="text-gray-600 mb-1">Start typing to search products</p>
                <p className="text-sm text-gray-400">Search by product name, code or barcode</p>
              </div>
            )}

            {/* Results table */}
            {searchTerm.length >= 1 && (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="max-h-[440px] overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-blue-50 border-b border-gray-200 sticky top-0">
                      <tr>
                        <th className="text-left px-4 py-2.5 text-gray-600 font-medium">Code</th>
                        <th className="text-left px-4 py-2.5 text-gray-600 font-medium">Product</th>
                        <th className="text-center px-4 py-2.5 text-gray-600 font-medium">UoM</th>
                        <th className="text-center px-4 py-2.5 text-gray-600 font-medium">Price</th>
                        <th className="text-center px-4 py-2.5 text-gray-600 font-medium">Stock</th>
                      </tr>
                    </thead>
                    <tbody>
                      {isSearching && (
                        <tr>
                          <td colSpan={5} className="text-center py-10">
                            <Loader2 className="w-5 h-5 animate-spin mx-auto text-blue-500" />
                          </td>
                        </tr>
                      )}
                      {!isSearching && results.length === 0 && (
                        <tr>
                          <td colSpan={5} className="text-center py-10 text-gray-500">
                            No products found for "{searchTerm}"
                          </td>
                        </tr>
                      )}
                      {results.map((product) => (
                        <tr
                          key={product.id}
                          className="border-b border-gray-100 last:border-0 cursor-pointer hover:bg-blue-50/50 transition-colors"
                          onClick={() => handleSelectProduct(product)}
                        >
                          <td className="px-4 py-3 font-mono text-blue-600 text-xs">
                            {product.default_code || '—'}
                          </td>
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-800 leading-tight">{product.name}</div>
                            {product.foreign_name && (
                              <div className="text-xs text-gray-500 mt-0.5">{product.foreign_name}</div>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center text-gray-600">
                            {product.uom_id?.name ?? '—'}
                          </td>
                          <td className="px-4 py-3 text-center font-mono">
                            ${(product.list_price ?? 0).toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <Badge className={
                              (product.qty_available ?? 0) > 0
                                ? 'bg-green-100 text-green-700 hover:bg-green-100 border-0'
                                : 'bg-red-100 text-red-700 hover:bg-red-100 border-0'
                            }>
                              {product.qty_available ?? 0}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <p className="text-xs text-gray-400 text-center pt-1">
              Click on a product to configure and add it to the order
            </p>
          </div>
        )}

        {/* ── Step 2: Config ───────────────────────────────────── */}
        {step === 'config' && (
          <div className="p-6">
            {/* Loading full product detail */}
            {isLoadingDetail && (
              <div className="flex flex-col items-center justify-center py-16">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-3" />
                <p className="text-gray-500 text-sm">Loading product details…</p>
              </div>
            )}

            {!isLoadingDetail && productDetail && (
              <div className="space-y-5">
                {/* Product header */}
                <div className="bg-blue-50 rounded-lg px-5 py-4 border border-blue-100">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center shrink-0">
                      <Package className="w-5 h-5 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-gray-900">{productDetail.product_name}</h3>
                        {productDetail.badge_text && (
                          <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded">
                            {productDetail.badge_text}
                          </span>
                        )}
                      </div>
                      {productDetail.foreign_name && (
                        <p className="text-sm text-gray-500 mt-0.5">{productDetail.foreign_name}</p>
                      )}
                      {productDetail.default_code && (
                        <p className="text-xs font-mono text-blue-500 mt-0.5">
                          <Hash className="inline w-3 h-3 mr-0.5" />{productDetail.default_code}
                        </p>
                      )}
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs text-gray-500 mb-0.5">Available</div>
                      <div className={`font-bold text-lg ${(productDetail.available_qty ?? 0) > 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {productDetail.available_qty ?? 0}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Config grid */}
                <div className="grid grid-cols-2 gap-4">

                  {/* UoM Selection */}
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
                      <Tag className="w-3.5 h-3.5 text-gray-500" />
                      Unit of Measure
                    </label>
                    {productDetail.available_uoms && productDetail.available_uoms.length > 0 ? (
                      <div className="space-y-2">
                        {productDetail.available_uoms.map((uom) => (
                          <button
                            key={uom.id}
                            onClick={() => handleUomChange(uom.id)}
                            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg border text-sm transition-all ${
                              selectedUomId === uom.id
                                ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium'
                                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            <span>{uom.name}</span>
                            <span className="font-mono text-blue-600">${uom.price.toFixed(2)}</span>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="px-3 py-2.5 border border-gray-200 rounded-lg bg-gray-50 text-sm text-gray-600">
                        {productDetail.product_uom_name}
                      </div>
                    )}
                  </div>

                  {/* Warehouse Selection */}
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-1.5">
                      <Warehouse className="w-3.5 h-3.5 text-gray-500" />
                      Warehouse
                    </label>
                    {productDetail.warehouses && productDetail.warehouses.length > 0 ? (
                      <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {productDetail.warehouses.map((wh) => (
                          <button
                            key={wh.id}
                            onClick={() => setSelectedWarehouseId(wh.id)}
                            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg border text-sm transition-all ${
                              selectedWarehouseId === wh.id
                                ? 'border-green-500 bg-green-50 text-green-700 font-medium'
                                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            <span className="flex items-center gap-1.5">
                              <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">
                                {wh.code}
                              </span>
                              <span className="truncate">{wh.name}</span>
                            </span>
                            <span className={`font-medium text-xs ${wh.quantity > 0 ? 'text-green-600' : 'text-red-500'}`}>
                              {wh.quantity}
                            </span>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="px-3 py-2.5 border border-gray-200 rounded-lg bg-gray-50 text-sm text-gray-500">
                        No warehouse data
                      </div>
                    )}
                  </div>
                </div>

                {/* Qty / Price / Discount */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 block">Quantity</label>
                    <Input
                      type="number"
                      value={qty}
                      min={0.001}
                      step={1}
                      onChange={(e) => setQty(parseFloat(e.target.value) || 1)}
                      className="text-center h-10 border-gray-300 focus:border-blue-500"
                    />
                    {selectedWarehouseQty !== null && (
                      <p className="text-xs text-gray-400 mt-1 text-center">
                        Available: {selectedWarehouseQty}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 flex items-center gap-1">
                      Unit Price (USD)
                      {isLoadingPrice && <Loader2 className="w-3 h-3 animate-spin text-blue-500" />}
                    </label>
                    <Input
                      type="number"
                      value={unitPrice}
                      min={0}
                      step={0.01}
                      onChange={(e) => setUnitPrice(parseFloat(e.target.value) || 0)}
                      className="text-center h-10 border-gray-300 focus:border-blue-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 block">Discount %</label>
                    <Input
                      type="number"
                      value={discount}
                      min={0}
                      max={100}
                      step={0.5}
                      onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                      className="text-center h-10 border-gray-300 focus:border-blue-500"
                    />
                  </div>
                </div>

                {/* Totals preview */}
                <div className="bg-gray-50 rounded-lg px-5 py-4 border border-gray-200">
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Subtotal</div>
                      <div className="font-mono font-medium">${lineSubtotal.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Discount</div>
                      <div className="font-mono font-medium text-red-500">-${discountAmount.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Line Total</div>
                      <div className="font-mono font-semibold text-blue-600">${lineTotal.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Total IQD</div>
                      <div className="font-mono font-semibold text-gray-700">
                        {lineTotalIqd.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Error */}
                {configError && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    {configError}
                  </div>
                )}

                <Separator />

                {/* Actions */}
                <div className="flex justify-end gap-3">
                  <Button
                    variant="outline"
                    onClick={() => { setStep('search'); setSelectedProduct(null); }}
                    className="border-gray-300"
                  >
                    <ArrowLeft className="w-4 h-4 mr-1.5" />
                    Back to Search
                  </Button>
                  <Button
                    onClick={handleAddToOrder}
                    disabled={isAdding || !selectedWarehouseId}
                    className="bg-green-600 hover:bg-green-700 text-white px-8"
                  >
                    {isAdding
                      ? <><Loader2 className="w-4 h-4 mr-1.5 animate-spin" />Adding…</>
                      : '+ Add to Order'
                    }
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
