import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { Shift, Attendance, MessageTemplate, LiveAgent } from '../types';
import type { PaginatedResponse } from '../../../shared/types';

/**
 * POST /api/crm/attendance/live_status
 * Returns live agents currently checked-in, grouped by branch.
 * This is the closest equivalent to "agents list".
 */
async function getLiveAgents(branchId?: number): Promise<ApiResult<LiveAgent[]>> {
  return apiPost('/api/crm/attendance/live_status', {
    branch_id: branchId ?? null,
  });
}

/** POST /api/crm/shifts/list */
async function listShifts(branchId?: number): Promise<ApiResult<Shift[]>> {
  return apiPost('/api/crm/shifts/list', { branch_id: branchId ?? null });
}

/** POST /api/crm/shifts/create */
async function createShift(payload: Partial<Shift>): Promise<ApiResult<Shift>> {
  return apiPost('/api/crm/shifts/create', {
    name:       payload.name       ?? '',
    branch_id:  payload.branch_id  ?? null,
    shift_type: payload.shift_type ?? 'morning',
    start_time: payload.start_time ?? 8.0,
    end_time:   payload.end_time   ?? 17.0,
  });
}

/** POST /api/crm/shifts/:id/update */
async function updateShift(id: number, payload: Partial<Shift>): Promise<ApiResult<Shift>> {
  return apiPost(`/api/crm/shifts/${id}/update`, payload as Record<string, unknown>);
}

/** POST /api/crm/shifts/:id/delete */
async function deleteShift(id: number): Promise<ApiResult<void>> {
  return apiPost(`/api/crm/shifts/${id}/delete`, {});
}

/** POST /api/crm/attendance/check_in */
async function checkIn(params: {
  branch_id?: number;
  shift_id?: number;
  work_type?: 'office' | 'remote';
}): Promise<ApiResult<Attendance>> {
  return apiPost('/api/crm/attendance/check_in', {
    branch_id: params.branch_id ?? null,
    shift_id:  params.shift_id  ?? null,
    work_type: params.work_type ?? 'office',
  });
}

/** POST /api/crm/attendance/check_out */
async function checkOut(notes?: string): Promise<ApiResult<Attendance>> {
  return apiPost('/api/crm/attendance/check_out', { notes: notes ?? null });
}

/** POST /api/crm/attendance/list */
async function listAttendance(params: {
  page?: number;
  branch_id?: number;
  employee_id?: number;
  date_from?: string;
  date_to?: string;
}): Promise<ApiResult<PaginatedResponse<Attendance>>> {
  return apiPost('/api/crm/attendance/list', {
    page:        params.page        ?? 1,
    per_page:    25,
    branch_id:   params.branch_id   ?? null,
    employee_id: params.employee_id ?? null,
    date_from:   params.date_from   ?? null,
    date_to:     params.date_to     ?? null,
  });
}

/** POST /api/crm/templates/list */
async function listTemplates(params: {
  channel?: string;
  category?: string;
  branch_id?: number;
} = {}): Promise<ApiResult<MessageTemplate[]>> {
  return apiPost('/api/crm/templates/list', {
    channel:   params.channel   ?? null,
    category:  params.category  ?? null,
    branch_id: params.branch_id ?? null,
  });
}

/** POST /api/crm/templates/create */
async function createTemplate(payload: Partial<MessageTemplate>): Promise<ApiResult<MessageTemplate>> {
  return apiPost('/api/crm/templates/create', {
    name:     payload.name     ?? '',
    channel:  payload.channel  ?? 'whatsapp',
    body:     payload.body     ?? '',
    category: payload.category ?? 'other',
    body_ar:  payload.body_ar  ?? null,
  });
}

/** POST /api/crm/templates/:id/render — render template for a customer */
async function renderTemplate(id: number, customerId?: number): Promise<ApiResult<{ rendered: string }>> {
  return apiPost(`/api/crm/templates/${id}/render`, { customer_id: customerId ?? null });
}

export const workforceService = {
  getLiveAgents,
  listShifts,
  createShift,
  updateShift,
  deleteShift,
  checkIn,
  checkOut,
  listAttendance,
  listTemplates,
  createTemplate,
  renderTemplate,
};
