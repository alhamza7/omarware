import { create } from 'zustand';
import type { Agent, Shift, AttendanceRecord } from '../services/workforceService';

interface WorkforceStore {
  agents:      Agent[];
  shifts:      Shift[];
  attendance:  AttendanceRecord[];
  isLoading:   boolean;
  error:       string | null;

  setAgents:     (agents: Agent[]) => void;
  setShifts:     (shifts: Shift[]) => void;
  setAttendance: (records: AttendanceRecord[]) => void;
  setLoading:    (loading: boolean) => void;
  setError:      (error: string | null) => void;
}

export const useWorkforceStore = create<WorkforceStore>((set) => ({
  agents:     [],
  shifts:     [],
  attendance: [],
  isLoading:  false,
  error:      null,

  setAgents:     (agents) => set({ agents }),
  setShifts:     (shifts) => set({ shifts }),
  setAttendance: (attendance) => set({ attendance }),
  setLoading:    (isLoading) => set({ isLoading }),
  setError:      (error) => set({ error, isLoading: false }),
}));
