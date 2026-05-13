import { useState, useCallback, useRef } from 'react';
import type { Product, ProductUom, ProductWarehouse } from '../../../types/pos';
import posPerfumeApi from '../../../services/posPerfumeApi';

/** Full product detail returned by getProductData */
export interface ProductDetail {
  product_id:       number;
  product_name:     string;
  product_uom_id:   number;
  product_uom_name: string;
  price_unit:       number;
  available_qty:    number;
  default_code:     string;
  foreign_name:     string;
  color_class:      string;
  badge_text:       string;
  available_uoms:   ProductUom[];
  warehouses:       ProductWarehouse[];
}

/**
 * Debounced product search + full product detail fetching.
 * Also exposes getUomPrice for live price refresh when UoM changes.
 */
export function useProductSearch() {
  const [results,       setResults]       = useState<Product[]>([]);
  const [isSearching,   setIsSearching]   = useState(false);
  const [searchError,   setSearchError]   = useState<string | null>(null);
  const [productDetail, setProductDetail] = useState<ProductDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Search products with 300 ms debounce */
  const search = useCallback((query: string, pricelistId?: number) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query || query.trim().length < 1) {
      setResults([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      setSearchError(null);
      try {
        const res = await posPerfumeApi.listProducts({
          query:        query.trim(),
          limit:        80,
          pricelist_id: pricelistId,
        });
        if (res.success && res.data) {
          setResults(res.data.items ?? []);
        } else {
          setSearchError(res.error ?? 'Product search failed');
          setResults([]);
        }
      } catch (err) {
        setSearchError(err instanceof Error ? err.message : 'Network error');
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);
  }, []);

  /**
   * Fetch full product detail (UoMs, prices, warehouse stock).
   * Called when user clicks a product row.
   */
  const loadProductDetail = useCallback(async (
    productId:   number,
    pricelistId?: number,
    warehouseId?: number,
  ): Promise<ProductDetail | null> => {
    setIsLoadingDetail(true);
    setProductDetail(null);
    try {
      const res = await posPerfumeApi.getProductData({
        product_id:   productId,
        pricelist_id: pricelistId ?? null,
        warehouse_id: warehouseId ?? null,
      });
      if (res.success && res.data) {
        const detail = res.data as unknown as ProductDetail;
        setProductDetail(detail);
        return detail;
      }
      return null;
    } catch {
      return null;
    } finally {
      setIsLoadingDetail(false);
    }
  }, []);

  /**
   * Get updated price when user changes UoM.
   * Returns the new price_unit or null on error.
   */
  const fetchUomPrice = useCallback(async (
    productId:   number,
    pricelistId: number,
    uomId:       number,
  ): Promise<number | null> => {
    try {
      const res = await posPerfumeApi.getUomPrice({ product_id: productId, pricelist_id: pricelistId, uom_id: uomId });
      return res.success && res.data ? res.data.price_unit : null;
    } catch {
      return null;
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setSearchError(null);
    setProductDetail(null);
  }, []);

  return {
    results,
    isSearching,
    searchError,
    productDetail,
    isLoadingDetail,
    search,
    loadProductDetail,
    fetchUomPrice,
    clearResults,
  };
}
