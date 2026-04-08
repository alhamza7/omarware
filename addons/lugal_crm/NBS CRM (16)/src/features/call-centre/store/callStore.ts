import { create } from 'zustand';
import type { Call, CallQueue, CallScript } from '../types';

interface CallStore {
  calls:       Call[];
  activeCall:  Call | null;
  queue:       CallQueue[];
  scripts:     CallScript[];
  total:       number;
  isLoading:   boolean;
  error:       string | null;

  setCalls:      (calls: Call[], total: number) => void;
  setActiveCall: (call: Call | null) => void;
  setQueue:      (queue: CallQueue[]) => void;
  setScripts:    (scripts: CallScript[]) => void;
  setLoading:    (loading: boolean) => void;
  setError:      (error: string | null) => void;
  updateCall:    (call: Call) => void;
}

export const useCallStore = create<CallStore>((set) => ({
  calls:      [],
  activeCall: null,
  queue:      [],
  scripts:    [],
  total:      0,
  isLoading:  false,
  error:      null,

  setCalls:      (calls, total) => set({ calls, total, isLoading: false }),
  setActiveCall: (activeCall) => set({ activeCall }),
  setQueue:      (queue) => set({ queue }),
  setScripts:    (scripts) => set({ scripts }),
  setLoading:    (isLoading) => set({ isLoading }),
  setError:      (error) => set({ error, isLoading: false }),
  updateCall:    (updated) =>
    set((s) => ({
      calls:      s.calls.map((c) => (c.id === updated.id ? updated : c)),
      activeCall: s.activeCall?.id === updated.id ? updated : s.activeCall,
    })),
}));
