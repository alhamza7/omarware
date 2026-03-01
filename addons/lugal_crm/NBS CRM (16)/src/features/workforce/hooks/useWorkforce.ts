import { useCallback, useEffect } from 'react';
import { useWorkforceStore } from '../store/workforceStore';
import { workforceService } from '../services/workforceService';
import type { Shift } from '../services/workforceService';

export function useWorkforce(branchId?: number) {
  const store = useWorkforceStore();

  const fetchAll = useCallback(async () => {
    store.setLoading(true);
    const [agentRes, shiftRes, attRes] = await Promise.all([
      workforceService.listAgents({ branch_id: branchId }),
      workforceService.listShifts({ branch_id: branchId }),
      workforceService.listAttendance(),
    ]);
    if (agentRes.success && agentRes.data)  store.setAgents(agentRes.data.items);
    if (shiftRes.success && shiftRes.data)  store.setShifts(shiftRes.data.items);
    if (attRes.success && attRes.data)      store.setAttendance(attRes.data.items);
    if (!agentRes.success) store.setError(agentRes.error ?? 'Failed to load workforce');
    else store.setLoading(false);
  }, [branchId]);

  const createShift = useCallback(async (payload: Partial<Shift>) => {
    const result = await workforceService.createShift(payload);
    if (result.success) await fetchAll();
    return result;
  }, [fetchAll]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    agents:     store.agents,
    shifts:     store.shifts,
    attendance: store.attendance,
    isLoading:  store.isLoading,
    error:      store.error,
    fetchAll,
    createShift,
  };
}
