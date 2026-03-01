import { create } from 'zustand';
import type { Product, PriceListEntry } from '../services/productService';

interface ProductStore {
  products:   Product[];
  priceList:  PriceListEntry[];
  total:      number;
  isLoading:  boolean;
  error:      string | null;
  search:     string;
  category:   string | null;

  setProducts:  (products: Product[], total: number) => void;
  setPriceList: (list: PriceListEntry[]) => void;
  setLoading:   (loading: boolean) => void;
  setError:     (error: string | null) => void;
  setSearch:    (q: string) => void;
  setCategory:  (cat: string | null) => void;
}

export const useProductStore = create<ProductStore>((set) => ({
  products:  [],
  priceList: [],
  total:     0,
  isLoading: false,
  error:     null,
  search:    '',
  category:  null,

  setProducts:  (products, total) => set({ products, total, isLoading: false }),
  setPriceList: (priceList) => set({ priceList }),
  setLoading:   (isLoading) => set({ isLoading }),
  setError:     (error) => set({ error, isLoading: false }),
  setSearch:    (search) => set({ search }),
  setCategory:  (category) => set({ category }),
}));
