import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { Ticket, FollowUp, CreateTicketPayload } from '../types';
import type { PaginatedResponse } from '../../../shared/types';

/** POST /api/crm/tickets/list */
async function listTickets(params: {
  page?: number;
  per_page?: number;
  status?: string;
  customer_id?: number;
  branch_id?: number;
}): Promise<ApiResult<PaginatedResponse<Ticket>>> {
  return apiPost('/api/crm/tickets/list', {
    page:        params.page        ?? 1,
    per_page:    params.per_page    ?? 20,
    status:      params.status      ?? null,
    customer_id: params.customer_id ?? null,
    branch_id:   params.branch_id   ?? null,
  });
}

/** POST /api/crm/tickets/create */
async function createTicket(payload: CreateTicketPayload): Promise<ApiResult<Ticket>> {
  return apiPost('/api/crm/tickets/create', {
    customer_id: payload.customer_id ?? null,
    title:       payload.title,
    description: payload.description ?? null,
    branch_id:   payload.branch_id   ?? null,
    priority:    payload.priority    ?? 'medium',
    channel:     payload.channel     ?? null,
  });
}

/** POST /api/crm/tickets/:id/update */
async function updateTicket(
  id: number,
  payload: Partial<CreateTicketPayload & { status: string }>,
): Promise<ApiResult<Ticket>> {
  return apiPost(`/api/crm/tickets/${id}/update`, payload as Record<string, unknown>);
}

/** POST /api/crm/tickets/:id/assign */
async function assignTicket(id: number, agentId: number): Promise<ApiResult<Ticket>> {
  return apiPost(`/api/crm/tickets/${id}/assign`, { assigned_to_id: agentId });
}

/**
 * POST /api/crm/tickets/:id/update_status
 * Close ticket by setting status to 'closed'.
 */
async function closeTicket(id: number, note?: string): Promise<ApiResult<Ticket>> {
  const result = await apiPost<Ticket>(`/api/crm/tickets/${id}/update_status`, { status: 'closed' });
  // If a note is provided, add it separately
  if (result.success && note) {
    await addFollowUp(id, note);
  }
  return result;
}

/**
 * POST /api/crm/tickets/:id/notes
 * Get all notes/follow-ups for a ticket.
 */
async function getFollowUps(ticketId: number): Promise<ApiResult<FollowUp[]>> {
  return apiPost(`/api/crm/tickets/${ticketId}/notes`, {});
}

/**
 * POST /api/crm/tickets/:id/note/add
 * Add a follow-up note to a ticket.
 */
async function addFollowUp(ticketId: number, note: string): Promise<ApiResult<FollowUp>> {
  return apiPost(`/api/crm/tickets/${ticketId}/note/add`, { body: note });
}

/** POST /api/crm/tickets/:id/escalate */
async function escalateTicket(id: number, escalatedToId: number): Promise<ApiResult<Ticket>> {
  return apiPost(`/api/crm/tickets/${id}/escalate`, { escalated_to_id: escalatedToId });
}

/** POST /api/crm/tickets/search */
async function searchTickets(query: string, branchId?: number): Promise<ApiResult<Ticket[]>> {
  return apiPost('/api/crm/tickets/search', { query, branch_id: branchId ?? null, limit: 30 });
}

/** POST /api/crm/tickets/:id/delete */
async function deleteTicket(id: number): Promise<ApiResult<void>> {
  return apiPost(`/api/crm/tickets/${id}/delete`, {});
}

export const ticketService = {
  listTickets,
  createTicket,
  updateTicket,
  assignTicket,
  closeTicket,
  getFollowUps,
  addFollowUp,
  escalateTicket,
  searchTickets,
  deleteTicket,
};
