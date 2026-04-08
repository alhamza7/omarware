import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { Call, CallScript, CallQueue, StartCallPayload, EndCallPayload } from '../types';
import type { PaginatedResponse } from '../../../shared/types';

/** POST /api/crm/calls/list */
async function listCalls(params: {
  page?: number;
  per_page?: number;
  customer_id?: number;
  branch_id?: number;
  status?: string;
}): Promise<ApiResult<PaginatedResponse<Call>>> {
  return apiPost('/api/crm/calls/list', {
    page:        params.page        ?? 1,
    per_page:    params.per_page    ?? 20,
    customer_id: params.customer_id ?? null,
    branch_id:   params.branch_id   ?? null,
    status:      params.status      ?? null,
  });
}

/** POST /api/crm/calls/create — start a new call */
async function startCall(payload: StartCallPayload): Promise<ApiResult<Call>> {
  return apiPost('/api/crm/calls/create', {
    direction:   payload.direction,
    customer_id: payload.customer_id ?? null,
    branch_id:   payload.branch_id   ?? null,
    script_id:   payload.script_id   ?? null,
  });
}

/** POST /api/crm/calls/:id/end */
async function endCall(id: number, payload: EndCallPayload): Promise<ApiResult<Call>> {
  return apiPost(`/api/crm/calls/${id}/end`, {
    post_call_notes: payload.post_call_notes ?? null,
    qa_score:        payload.qa_score        ?? null,
  });
}

/**
 * POST /api/crm/calls/queue/list
 * Returns the active call queue for a branch.
 */
async function getQueue(branchId?: number): Promise<ApiResult<CallQueue[]>> {
  return apiPost('/api/crm/calls/queue/list', { branch_id: branchId ?? null });
}

/**
 * POST /api/crm/calls/queue/:queueId/assign
 * Assign agent to a queued call.
 */
async function assignFromQueue(queueId: number): Promise<ApiResult<Call>> {
  return apiPost(`/api/crm/calls/queue/${queueId}/assign`, {});
}

/**
 * POST /api/crm/config/scripts/list
 * Fetch call scripts, optionally filtered by branch.
 */
async function getScripts(branchId?: number): Promise<ApiResult<CallScript[]>> {
  return apiPost('/api/crm/config/scripts/list', { branch_id: branchId ?? null });
}

/**
 * POST /api/crm/calls/:id/attach_recording
 * Attach a recording URL to a completed call.
 */
async function updateRecording(id: number, url: string): Promise<ApiResult<Call>> {
  return apiPost(`/api/crm/calls/${id}/attach_recording`, { recording_url: url });
}

/** POST /api/crm/calls/:id — get single call detail */
async function getCall(id: number): Promise<ApiResult<Call>> {
  return apiPost(`/api/crm/calls/${id}`, {});
}

/** POST /api/crm/calls/:id/update */
async function updateCall(id: number, payload: Partial<Call>): Promise<ApiResult<Call>> {
  return apiPost(`/api/crm/calls/${id}/update`, payload as Record<string, unknown>);
}

/** POST /api/crm/calls/queue/add — add customer to queue */
async function addToQueue(customerId: number, branchId: number, phone?: string): Promise<ApiResult<CallQueue>> {
  return apiPost('/api/crm/calls/queue/add', {
    customer_id: customerId,
    branch_id:   branchId,
    phone:       phone ?? null,
  });
}

export const callService = {
  listCalls,
  startCall,
  endCall,
  getQueue,
  assignFromQueue,
  getScripts,
  updateRecording,
  getCall,
  updateCall,
  addToQueue,
};
