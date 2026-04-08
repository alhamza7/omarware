import { create } from 'zustand';
import type { PurchaseOrder, Vendor, Container } from '../types';

interface SupplyStore {
  purchaseOrders: PurchaseOrder[];
  vendors:        Vendor[];
  containers:     Container[];
  selectedPo:     PurchaseOrder | null;
  total:          number;
  isLoading:      boolean;
  error:          string | null;
  statusFilter:   string | null;

  setPurchaseOrders: (pos: PurchaseOrder[], total: number) => void;
  setVendors:        (vendors: Vendor[]) => void;
  setContainers:     (containers: Container[]) => void;
  setSelectedPo:     (po: PurchaseOrder | null) => void;
  setLoading:        (loading: boolean) => void;
  setError:          (error: string | null) => void;
  setStatusFilter:   (status: string | null) => void;
  updatePo:          (po: PurchaseOrder) => void;
}

export const useSupplyStore = create<SupplyStore>((set) => ({
  purchaseOrders: [],
  vendors:        [],
  containers:     [],
  selectedPo:     null,
  total:          0,
  isLoading:      false,
  error:          null,
  statusFilter:   null,

  setPurchaseOrders: (purchaseOrders, total) => set({ purchaseOrders, total, isLoading: false }),
  setVendors:        (vendors) => set({ vendors }),
  setContainers:     (containers) => set({ containers }),
  setSelectedPo:     (selectedPo) => set({ selectedPo }),
  setLoading:        (isLoading) => set({ isLoading }),
  setError:          (error) => set({ error, isLoading: false }),
  setStatusFilter:   (statusFilter) => set({ statusFilter }),
  updatePo: (updated) =>
    set((s) => ({
      purchaseOrders: s.purchaseOrders.map((p) => (p.id === updated.id ? updated : p)),
      selectedPo:     s.selectedPo?.id === updated.id ? updated : s.selectedPo,
    })),
}));
