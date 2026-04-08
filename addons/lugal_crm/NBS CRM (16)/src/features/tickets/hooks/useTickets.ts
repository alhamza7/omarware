import { useCallback, useEffect } from 'react';
import { useTicketStore } from '../store/ticketStore';
import { ticketService } from '../services/ticketService';
import type { CreateTicketPayload } from '../types';

export function useTickets(branchId?: number) {
  const store = useTicketStore();

  const fetchTickets = useCallback(async () => {
    store.setLoading(true);
    const result = await ticketService.listTickets({
      branch_id: branchId,
      status:    store.statusFilter ?? undefined,
    });
    if (result.success && result.data) {
      store.setTickets(result.data.items, result.data.total);
    } else {
      store.setError(result.error ?? 'Failed to load tickets');
    }
  }, [branchId, store.statusFilter]);

  const fetchFollowUps = useCallback(async (ticketId: number) => {
    const result = await ticketService.getFollowUps(ticketId);
    if (result.success && result.data) store.setFollowUps(result.data);
  }, [store]);

  const createTicket = useCallback(async (payload: CreateTicketPayload) => {
    const result = await ticketService.createTicket(payload);
    if (result.success) await fetchTickets();
    return result;
  }, [fetchTickets]);

  const closeTicket = useCallback(async (id: number, note?: string) => {
    const result = await ticketService.closeTicket(id, note);
    if (result.success && result.data) store.updateTicket(result.data);
    return result;
  }, [store]);

  const addFollowUp = useCallback(async (ticketId: number, note: string) => {
    const result = await ticketService.addFollowUp(ticketId, note);
    if (result.success && result.data) store.addFollowUp(result.data);
    return result;
  }, [store]);

  const assignTicket = useCallback(async (id: number, agentId: number) => {
    const result = await ticketService.assignTicket(id, agentId);
    if (result.success && result.data) store.updateTicket(result.data);
    return result;
  }, [store]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  return {
    tickets:        store.tickets,
    selectedTicket: store.selectedTicket,
    followUps:      store.followUps,
    total:          store.total,
    isLoading:      store.isLoading,
    error:          store.error,
    statusFilter:   store.statusFilter,
    setSelected:    store.setSelectedTicket,
    setStatusFilter: store.setStatusFilter,
    fetchTickets,
    fetchFollowUps,
    createTicket,
    closeTicket,
    addFollowUp,
    assignTicket,
  };
}
