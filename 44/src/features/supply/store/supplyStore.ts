// ============================================================
// Supply Chain — Zustand Store
// ============================================================
import { create } from 'zustand';
import type { Po, PoListFilter, Vendor } from '../../../types/supply';

interface SupplyState {
  // Auth
  token:     string;
  setToken:  (t: string) => void;
  clearAuth: () => void;

  // PO List
  pos:        Po[];
  total:      number;
  filter:     PoListFilter;
  loading:    boolean;
  error:      string | null;
  setPOs:     (items: Po[], total: number) => void;
  setFilter:  (f: Partial<PoListFilter>) => void;
  setLoading: (v: boolean) => void;
  setError:   (e: string | null) => void;

  // Selected PO (detail view)
  selectedPo:    Po | null;
  setSelectedPo: (po: Po | null) => void;
  updatePoInList:(po: Po) => void;
  removePoFromList:(id: number) => void;

  // Vendor search (for create form)
  vendors:       Vendor[];
  vendorLoading: boolean;
  setVendors:    (v: Vendor[]) => void;
  setVendorLoading: (v: boolean) => void;
}

export const useSupplyStore = create<SupplyState>((set) => ({
  // Auth
  token:    localStorage.getItem('supply_jwt') ?? '',
  setToken: (t) => { localStorage.setItem('supply_jwt', t); set({ token: t }); },
  clearAuth:() => { localStorage.removeItem('supply_jwt'); set({ token: '' }); },

  // PO List
  pos:     [],
  total:   0,
  filter:  { page: 1, per_page: 20, status: '', search: '', division: '' },
  loading: false,
  error:   null,
  setPOs:     (items, total) => set({ pos: items, total }),
  setFilter:  (f) => set((s) => ({ filter: { ...s.filter, ...f, page: f.page ?? 1 } })),
  setLoading: (v) => set({ loading: v }),
  setError:   (e) => set({ error: e }),

  // Selected PO
  selectedPo:   null,
  setSelectedPo:(po) => set({ selectedPo: po }),
  updatePoInList:(po) => set((s) => ({
    pos:        s.pos.map((p) => (p.id === po.id ? po : p)),
    selectedPo: s.selectedPo?.id === po.id ? po : s.selectedPo,
  })),
  removePoFromList:(id) => set((s) => ({
    pos:        s.pos.filter((p) => p.id !== id),
    total:      s.total - 1,
    selectedPo: s.selectedPo?.id === id ? null : s.selectedPo,
  })),

  // Vendors
  vendors:          [],
  vendorLoading:    false,
  setVendors:       (v) => set({ vendors: v }),
  setVendorLoading: (v) => set({ vendorLoading: v }),
}));
