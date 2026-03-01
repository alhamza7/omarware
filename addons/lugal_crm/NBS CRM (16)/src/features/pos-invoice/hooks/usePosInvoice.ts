import { useState, useRef, useCallback } from 'react';
import { posInvoiceService } from '../services/posInvoiceService';
import type {
  ApiInvoiceContext,
  ApiProduct,
  ApiProductDetail,
  CreateOrderPayload,
  CreatedOrder,
} from '../types';

/** All state + actions for the invoice creation flow. */
export function usePosInvoice() {
  const [context, setContext]               = useState<ApiInvoiceContext | null>(null);
  const [products, setProducts]             = useState<ApiProduct[]>([]);
  const [isLoadingContext, setLoadingCtx]   = useState(false);
  const [isSearchingProducts, setSearching] = useState(false);
  const [isSubmitting, setSubmitting]       = useState(false);
  const [createdOrder, setCreatedOrder]     = useState<CreatedOrder | null>(null);
  const [error, setError]                   = useState<string | null>(null);
  const [selectedPricelistId, setPricelist] = useState<number | null>(null);

  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Load context data (warehouses, pricelists, partner_id) for a CRM customer. */
  const loadContext = useCallback(async (customerId: number) => {
    setLoadingCtx(true);
    setError(null);
    setCreatedOrder(null);

    const result = await posInvoiceService.fetchInvoiceContext(customerId);

    if (result.success && result.data) {
      setContext(result.data);
      const defaultId = result.data.default_pricelist_id ?? result.data.pricelists[0]?.id ?? null;
      setPricelist(defaultId);

      // Pre-load first page of products so the selector isn't empty
      const prodResult = await posInvoiceService.searchProducts('', defaultId ?? undefined, 80);
      if (prodResult.success && prodResult.data) {
        setProducts(prodResult.data.items);
      }
    } else {
      setError(result.error ?? 'فشل تحميل بيانات الفاتورة');
    }

    setLoadingCtx(false);
  }, []);

  /** Debounced product search triggered from the dialog's search input. */
  const searchProducts = useCallback((query: string) => {
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);

    searchDebounceRef.current = setTimeout(async () => {
      setSearching(true);
      const result = await posInvoiceService.searchProducts(
        query,
        selectedPricelistId ?? undefined,
        80,
      );
      if (result.success && result.data) {
        setProducts(result.data.items);
      }
      setSearching(false);
    }, 350);
  }, [selectedPricelistId]);

  /** Fetch full product detail (price per pricelist, stock per warehouse). */
  const fetchProductDetail = useCallback(
    async (productId: number): Promise<ApiProductDetail | null> => {
      const result = await posInvoiceService.fetchProductDetail(
        productId,
        selectedPricelistId ?? undefined,
      );
      return result.success && result.data ? result.data : null;
    },
    [selectedPricelistId],
  );

  /** Submit the order to the backend. */
  const submitOrder = useCallback(async (payload: CreateOrderPayload): Promise<CreatedOrder | null> => {
    setSubmitting(true);
    setError(null);

    const result = await posInvoiceService.createOrder(payload);

    if (result.success && result.data) {
      setCreatedOrder(result.data);
      setSubmitting(false);
      return result.data;
    }

    setError(result.error ?? 'فشل إنشاء الفاتورة');
    setSubmitting(false);
    return null;
  }, []);

  /** Reset all state when dialog is closed. */
  const reset = useCallback(() => {
    setContext(null);
    setProducts([]);
    setCreatedOrder(null);
    setError(null);
    setPricelist(null);
    setLoadingCtx(false);
    setSubmitting(false);
  }, []);

  return {
    // State
    context,
    products,
    isLoadingContext,
    isSearchingProducts,
    isSubmitting,
    createdOrder,
    error,
    selectedPricelistId,
    // Derived
    warehouses: context?.warehouses ?? [],
    pricelists: context?.pricelists ?? [],
    invoiceTypes: context?.invoiceTypes ?? [],
    partnerId: context?.partner_id ?? null,
    exchangeRate: context?.exchange_rate ?? null,
    // Actions
    loadContext,
    searchProducts,
    fetchProductDetail,
    submitOrder,
    setPricelist,
    reset,
  };
}
