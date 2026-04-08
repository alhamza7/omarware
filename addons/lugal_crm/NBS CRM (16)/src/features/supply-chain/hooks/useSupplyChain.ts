import { useCallback, useEffect } from 'react';
import { useSupplyStore } from '../store/supplyStore';
import { supplyService } from '../services/supplyService';
import type { CreatePoPayload } from '../types';

export function useSupplyChain() {
  const store = useSupplyStore();

  const fetchAll = useCallback(async () => {
    store.setLoading(true);
    const [poRes, vendorRes, containerRes] = await Promise.all([
      supplyService.listPurchaseOrders({ status: store.statusFilter ?? undefined }),
      supplyService.listVendors(),
      supplyService.listContainers(),
    ]);
    if (poRes.success && poRes.data)           store.setPurchaseOrders(poRes.data.items ?? [], poRes.data.total ?? 0);
    if (vendorRes.success && vendorRes.data)   store.setVendors(vendorRes.data.items ?? []);
    if (containerRes.success && containerRes.data) store.setContainers(containerRes.data.items ?? []);
    if (!poRes.success) store.setError(poRes.error ?? 'Failed to load supply chain');
    else store.setLoading(false);
  }, [store.statusFilter]);

  const createPo = useCallback(async (payload: CreatePoPayload) => {
    const result = await supplyService.createPurchaseOrder(payload);
    if (result.success) await fetchAll();
    return result;
  }, [fetchAll]);

  const confirmPo = useCallback(async (id: number) => {
    const result = await supplyService.confirmPurchaseOrder(id);
    if (result.success && result.data) store.updatePo(result.data);
    return result;
  }, [store]);

  const cancelPo = useCallback(async (id: number) => {
    const result = await supplyService.cancelPurchaseOrder(id);
    if (result.success && result.data) store.updatePo(result.data);
    return result;
  }, [store]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    purchaseOrders: store.purchaseOrders,
    vendors:        store.vendors,
    containers:     store.containers,
    selectedPo:     store.selectedPo,
    total:          store.total,
    isLoading:      store.isLoading,
    error:          store.error,
    statusFilter:   store.statusFilter,
    setSelected:    store.setSelectedPo,
    setStatusFilter: store.setStatusFilter,
    fetchAll,
    createPo,
    confirmPo,
    cancelPo,
  };
}
