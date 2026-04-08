import { useCallback, useEffect } from 'react';
import { useCustomerStore } from '../store/customerStore';
import { customerService } from '../services/customerService';
import type { CreateCustomerPayload, Customer } from '../types';

/**
 * Main customers hook — used by CustomerListContainer and CustomerFormContainer.
 * Encapsulates all customer CRUD logic.
 */
export function useCustomers() {
  const store = useCustomerStore();

  /** Fetch paginated customer list with current filters */
  const fetchCustomers = useCallback(async () => {
    store.setLoading(true);
    // Ensure default stages exist and un-staged customers get 'active' stage
    await customerService.setupStages();
    const result = await customerService.listCustomers({
      page:      store.page,
      per_page:  500,
      search:    store.searchQuery || undefined,
      stage_id:  store.stageFilter  ?? undefined,
      branch_id: store.branchFilter ?? undefined,
      vip_only:  store.vipOnly,
    });
    if (result.success && result.data) {
      store.setCustomers(result.data.items, result.data.total);
    } else {
      store.setError(result.error ?? 'Failed to load customers');
    }
  }, [store.page, store.searchQuery, store.stageFilter, store.branchFilter, store.vipOnly]);

  /** Fetch a single customer's 360° view */
  const fetchCustomer360 = useCallback(async (id: number) => {
    const result = await customerService.getCustomer360(id);
    if (result.success && result.data) {
      store.setSelectedCustomer(result.data as Customer);
    }
    return result;
  }, []);

  /** Create a new customer */
  const createCustomer = useCallback(async (payload: CreateCustomerPayload) => {
    const result = await customerService.createCustomer(payload);
    if (result.success) await fetchCustomers();
    return result;
  }, [fetchCustomers]);

  /** Update existing customer */
  const updateCustomer = useCallback(
    async (id: number, payload: Partial<CreateCustomerPayload>) => {
      const result = await customerService.updateCustomer(id, payload);
      if (result.success && result.data) store.updateCustomer(result.data);
      return result;
    },
    [store],
  );

  /** Soft-delete customer */
  const deleteCustomer = useCallback(async (id: number) => {
    const result = await customerService.deleteCustomer(id);
    if (result.success) store.removeCustomer(id);
    return result;
  }, [store]);

  /** Move customer to a different pipeline stage */
  const changeStage = useCallback(async (id: number, stageId: number) => {
    const result = await customerService.changeStage(id, stageId);
    if (result.success && result.data) store.updateCustomer(result.data);
    return result;
  }, [store]);

  /** Re-fetch when filters/page change */
  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  return {
    customers:        store.customers,
    selectedCustomer: store.selectedCustomer,
    total:            store.total,
    page:             store.page,
    isLoading:        store.isLoading,
    error:            store.error,
    searchQuery:      store.searchQuery,
    stageFilter:      store.stageFilter,
    vipOnly:          store.vipOnly,
    setPage:          store.setPage,
    setSearchQuery:   store.setSearchQuery,
    setStageFilter:   store.setStageFilter,
    setBranchFilter:  store.setBranchFilter,
    setVipOnly:       store.setVipOnly,
    setSelected:      store.setSelectedCustomer,
    fetchCustomers,
    fetchCustomer360,
    createCustomer,
    updateCustomer,
    deleteCustomer,
    changeStage,
  };
}
