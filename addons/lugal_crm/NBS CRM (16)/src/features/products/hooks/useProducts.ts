import { useCallback, useEffect } from 'react';
import { useProductStore } from '../store/productStore';
import { productService } from '../services/productService';
import type { CreateInvoicePayload } from '../services/productService';

export function useProducts(branchId?: number) {
  const store = useProductStore();

  const fetchProducts = useCallback(async () => {
    store.setLoading(true);
    const [prodRes, priceRes] = await Promise.all([
      productService.listProducts({ search: store.search || undefined, category: store.category ?? undefined }),
      productService.getPriceList(branchId),
    ]);
    if (prodRes.success && prodRes.data)   store.setProducts(prodRes.data.items ?? [], prodRes.data.total ?? 0);
    /** pricelist returns { data: { items: [] } } — extract the array */
    if (priceRes.success && priceRes.data) store.setPriceList(priceRes.data.items ?? []);
    if (!prodRes.success) store.setError(prodRes.error ?? 'Failed to load products');
    else store.setLoading(false);
  }, [store.search, store.category, branchId]);

  const createInvoice = useCallback(async (callId: number, payload: CreateInvoicePayload) => {
    return productService.createInvoiceFromCall(callId, payload);
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return {
    products:    store.products,
    priceList:   store.priceList,
    total:       store.total,
    isLoading:   store.isLoading,
    error:       store.error,
    setSearch:   store.setSearch,
    setCategory: store.setCategory,
    fetchProducts,
    createInvoice,
  };
}
