import { useCallback, useEffect } from 'react';
import { useCallStore } from '../store/callStore';
import { callService } from '../services/callService';
import type { StartCallPayload, EndCallPayload } from '../types';

/** Main call-centre hook — used by CallCentreContainer */
export function useCalls(branchId?: number) {
  const store = useCallStore();

  const fetchCalls = useCallback(async () => {
    store.setLoading(true);
    const result = await callService.listCalls({ branch_id: branchId });
    if (result.success && result.data) {
      store.setCalls(result.data.items, result.data.total);
    } else {
      store.setError(result.error ?? 'Failed to load calls');
    }
  }, [branchId]);

  const fetchQueue = useCallback(async () => {
    const result = await callService.getQueue(branchId);
    /** queue/list returns { data: { items: [] } } — extract the array */
    if (result.success && result.data) store.setQueue(result.data.items ?? []);
  }, [branchId]);

  const fetchScripts = useCallback(async () => {
    const result = await callService.getScripts(branchId);
    if (result.success && result.data) store.setScripts(result.data.items ?? []);
  }, [branchId]);

  const startCall = useCallback(async (payload: StartCallPayload) => {
    const result = await callService.startCall(payload);
    if (result.success && result.data) store.setActiveCall(result.data);
    return result;
  }, [store]);

  const endCall = useCallback(async (id: number, payload: EndCallPayload) => {
    const result = await callService.endCall(id, payload);
    if (result.success && result.data) {
      store.updateCall(result.data);
      store.setActiveCall(null);
    }
    return result;
  }, [store]);

  useEffect(() => {
    fetchCalls();
    fetchQueue();
    fetchScripts();
  }, [fetchCalls, fetchQueue, fetchScripts]);

  return {
    calls:       store.calls,
    activeCall:  store.activeCall,
    queue:       store.queue,
    scripts:     store.scripts,
    total:       store.total,
    isLoading:   store.isLoading,
    error:       store.error,
    startCall,
    endCall,
    fetchCalls,
    fetchQueue,
    setActiveCall: store.setActiveCall,
  };
}
