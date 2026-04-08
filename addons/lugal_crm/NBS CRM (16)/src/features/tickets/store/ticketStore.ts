import { create } from 'zustand';
import type { Ticket, FollowUp } from '../types';

interface TicketStore {
  tickets:         Ticket[];
  selectedTicket:  Ticket | null;
  followUps:       FollowUp[];
  total:           number;
  isLoading:       boolean;
  error:           string | null;
  statusFilter:    string | null;

  setTickets:        (tickets: Ticket[], total: number) => void;
  setSelectedTicket: (ticket: Ticket | null) => void;
  setFollowUps:      (followUps: FollowUp[]) => void;
  addFollowUp:       (followUp: FollowUp) => void;
  setLoading:        (loading: boolean) => void;
  setError:          (error: string | null) => void;
  setStatusFilter:   (status: string | null) => void;
  updateTicket:      (ticket: Ticket) => void;
  removeTicket:      (id: number) => void;
}

export const useTicketStore = create<TicketStore>((set) => ({
  tickets:        [],
  selectedTicket: null,
  followUps:      [],
  total:          0,
  isLoading:      false,
  error:          null,
  statusFilter:   null,

  setTickets:        (tickets, total) => set({ tickets, total, isLoading: false }),
  setSelectedTicket: (selectedTicket) => set({ selectedTicket, followUps: [] }),
  setFollowUps:      (followUps) => set({ followUps }),
  addFollowUp:       (fu) => set((s) => ({ followUps: [...s.followUps, fu] })),
  setLoading:        (isLoading) => set({ isLoading }),
  setError:          (error) => set({ error, isLoading: false }),
  setStatusFilter:   (statusFilter) => set({ statusFilter }),
  updateTicket:      (updated) =>
    set((s) => ({
      tickets:        s.tickets.map((t) => (t.id === updated.id ? updated : t)),
      selectedTicket: s.selectedTicket?.id === updated.id ? updated : s.selectedTicket,
    })),
  removeTicket: (id) =>
    set((s) => ({ tickets: s.tickets.filter((t) => t.id !== id) })),
}));
