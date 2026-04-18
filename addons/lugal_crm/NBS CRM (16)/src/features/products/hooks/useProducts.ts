import { useCallback, useEffect } from 'react';
import { useProductStore } from '../store/productStore';
import { productService } from '../services/productService';
import type { CreateInvoicePayload } from '../services/productService';

export function useProducts(branchId?: number) {
  const store = useProductStore();

  const fetchProducts = useCallback(async () => {
    store.setLoading(true);
    const rawCat = store.category?.trim();
    const categoryId =
      rawCat && /^\d+$/.test(rawCat) ? Number(rawCat) : undefined;
    const q = store.search?.trim() || undefined;
    const [prodRes, priceRes] = await Promise.all([
      productService.listProducts({
        search: q,
        category_id: categoryId ?? null,
        fetch_all: true,
      }),
      productService.getPriceList({
        branchId,
        search: q,
        categoryId,
        fetchAll: true,
      }),
    ]);
    if (prodRes.success) {
      const d = prodRes.data;
      store.setProducts(d?.items ?? [], d?.total ?? 0);
    }
    if (priceRes.success) {
      store.setPriceList(priceRes.data?.items ?? []);
    }
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
