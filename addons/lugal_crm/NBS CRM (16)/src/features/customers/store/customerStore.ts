import { create } from 'zustand';
import type { Customer } from '../types';

interface CustomerStore {
  customers:        Customer[];
  selectedCustomer: Customer | null;
  total:            number;
  page:             number;
  isLoading:        boolean;
  error:            string | null;
  searchQuery:      string;
  stageFilter:      number | null;
  branchFilter:     number | null;
  vipOnly:          boolean;

  setCustomers:        (customers: Customer[], total: number) => void;
  setSelectedCustomer: (customer: Customer | null) => void;
  setPage:             (page: number) => void;
  setLoading:          (loading: boolean) => void;
  setError:            (error: string | null) => void;
  setSearchQuery:      (q: string) => void;
  setStageFilter:      (id: number | null) => void;
  setBranchFilter:     (id: number | null) => void;
  setVipOnly:          (vipOnly: boolean) => void;
  updateCustomer:      (customer: Customer) => void;
  removeCustomer:      (id: number) => void;
}

export const useCustomerStore = create<CustomerStore>((set) => ({
  customers:        [],
  selectedCustomer: null,
  total:            0,
  page:             1,
  isLoading:        false,
  error:            null,
  searchQuery:      '',
  stageFilter:      null,
  branchFilter:     null,
  vipOnly:          false,

  setCustomers:  (customers, total) => set({ customers, total, isLoading: false }),
  setSelectedCustomer: (selectedCustomer) => set({ selectedCustomer }),
  setPage:       (page) => set({ page }),
  setLoading:    (isLoading) => set({ isLoading }),
  setError:      (error) => set({ error, isLoading: false }),
  setSearchQuery: (searchQuery) => set({ searchQuery, page: 1 }),
  setStageFilter:  (stageFilter) => set({ stageFilter, page: 1 }),
  setBranchFilter: (branchFilter) => set({ branchFilter, page: 1 }),
  setVipOnly:    (vipOnly) => set({ vipOnly, page: 1 }),

  updateCustomer: (updated) =>
    set((state) => ({
      customers: state.customers.map((c) => (c.id === updated.id ? updated : c)),
      selectedCustomer:
        state.selectedCustomer?.id === updated.id ? updated : state.selectedCustomer,
    })),

  removeCustomer: (id) =>
    set((state) => ({
      customers: state.customers.filter((c) => c.id !== id),
      selectedCustomer: state.selectedCustomer?.id === id ? null : state.selectedCustomer,
    })),
}));
