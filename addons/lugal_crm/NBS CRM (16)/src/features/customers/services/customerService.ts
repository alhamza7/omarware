import { apiPost, apiUpload } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type {
  Customer,
  CustomerListParams,
  CustomerListResponse,
  CreateCustomerPayload,
  UpdateCustomerPayload,
  Customer360,
  DeleteCustomerResponse,
  UploadImageResponse,
  UploadDocumentResponse,
  CustomerDocType,
} from '../types';

/** POST /api/crm/customers/list */
async function listCustomers(
  params: CustomerListParams = {},
): Promise<ApiResult<CustomerListResponse>> {
  return apiPost('/api/crm/customers/list', {
    page:      params.page      ?? 1,
    per_page:  params.per_page  ?? 50,
    search:    params.search    ?? null,
    stage_id:  params.stage_id  ?? null,
    branch_id: params.branch_id ?? null,
    vip_only:  params.vip_only  ?? false,
  });
}

/** POST /api/crm/customers/:id */
async function getCustomer(id: number): Promise<ApiResult<Customer>> {
  return apiPost(`/api/crm/customers/${id}`, {});
}

/**
 * POST /api/crm/customers/:id/activity
 * Returns the full 360° customer view (interactions, calls, tickets).
 */
async function getCustomer360(id: number): Promise<ApiResult<Customer360>> {
  return apiPost(`/api/crm/customers/${id}/activity`, {});
}

/** POST /api/crm/customers/create */
async function createCustomer(
  payload: CreateCustomerPayload,
): Promise<ApiResult<Customer>> {
  return apiPost('/api/crm/customers/create', payload as Record<string, unknown>);
}

/** POST /api/crm/customers/:id/update — partial update, accepts same fields as create */
async function updateCustomer(
  id: number,
  payload: UpdateCustomerPayload,
): Promise<ApiResult<Customer>> {
  return apiPost(`/api/crm/customers/${id}/update`, payload as Record<string, unknown>);
}

/** POST /api/crm/customers/:id/delete — soft-delete (sets is_deleted=true, active=false) */
async function deleteCustomer(id: number): Promise<ApiResult<DeleteCustomerResponse>> {
  return apiPost(`/api/crm/customers/${id}/delete`, {});
}

/**
 * POST /api/crm/customers/:id/kanban_move
 * Move customer to a different pipeline stage.
 */
async function changeStage(
  id: number,
  stageId: number,
): Promise<ApiResult<Customer>> {
  return apiPost(`/api/crm/customers/${id}/kanban_move`, { stage_id: stageId });
}

/** POST /api/crm/customers/search */
async function searchCustomers(query: string, limit = 20): Promise<ApiResult<Customer[]>> {
  return apiPost('/api/crm/customers/search', { query, limit });
}

/** POST /api/crm/customers/:id/interactions */
async function getInteractions(id: number): Promise<ApiResult<unknown[]>> {
  return apiPost(`/api/crm/customers/${id}/interactions`, {});
}

/** POST /api/crm/customers/:id/calls */
async function getCustomerCalls(id: number): Promise<ApiResult<unknown[]>> {
  return apiPost(`/api/crm/customers/${id}/calls`, {});
}

/** POST /api/crm/customers/:id/tickets */
async function getCustomerTickets(id: number): Promise<ApiResult<unknown[]>> {
  return apiPost(`/api/crm/customers/${id}/tickets`, {});
}

/** POST /api/crm/customers/:id/note/add */
async function addNote(id: number, note: string): Promise<ApiResult<void>> {
  return apiPost(`/api/crm/customers/${id}/note/add`, { body: note });
}

/** POST /api/crm/customers/:id/channel_identity/add */
async function addChannelIdentity(
  id: number,
  channel: string,
  handle: string,
): Promise<ApiResult<unknown>> {
  return apiPost(`/api/crm/customers/${id}/channel_identity/add`, { channel, handle });
}

/**
 * POST /api/crm/customers/setup_stages
 * Create the 5 default CRM stages if missing and assign 'active' stage to
 * customers imported from Odoo (those with no stage set).
 */
async function setupStages(): Promise<ApiResult<{ stages_created: number; customers_updated: number }>> {
  return apiPost('/api/crm/customers/setup_stages', {});
}

/**
 * POST /api/crm/customers/sync_from_odoo
 * Import res.partner contacts (customer_rank > 0) that are not yet in the CRM.
 * Returns { imported: number, total: number }.
 */
async function syncFromOdoo(): Promise<ApiResult<{ imported: number; total: number }>> {
  return apiPost('/api/crm/customers/sync_from_odoo', {});
}

/**
 * POST /api/crm/upload/image  (multipart/form-data)
 * Upload one or more shop images.
 *
 * @param files      – FileList or array of File objects
 * @param customerId – optional, links uploaded images to a specific customer
 *
 * Returns { files: [{ id, url, filename }] }
 */
async function uploadImages(
  files: File[],
  customerId?: number,
): Promise<ApiResult<UploadImageResponse['data']>> {
  const form = new FormData();
  for (const file of files) form.append('files[]', file);
  if (customerId != null) form.append('customer_id', String(customerId));
  return apiUpload<UploadImageResponse['data']>('/api/crm/upload/image', form);
}

/**
 * POST /api/crm/upload/document  (multipart/form-data)
 * Upload a single customer document with type metadata.
 *
 * @param file       – the document File
 * @param type       – document type (national_id | shop_license | tax_certificate | …)
 * @param name       – human-readable name (optional, defaults to filename)
 * @param customerId – optional, links document to a specific customer
 *
 * Returns { id, url, type, name, filename }
 */
async function uploadDocument(
  file: File,
  type: CustomerDocType,
  name?: string,
  customerId?: number,
): Promise<ApiResult<UploadDocumentResponse['data']>> {
  const form = new FormData();
  form.append('file', file);
  form.append('type', type);
  if (name) form.append('name', name);
  if (customerId != null) form.append('customer_id', String(customerId));
  return apiUpload<UploadDocumentResponse['data']>('/api/crm/upload/document', form);
}

export const customerService = {
  listCustomers,
  getCustomer,
  getCustomer360,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  changeStage,
  searchCustomers,
  getInteractions,
  getCustomerCalls,
  getCustomerTickets,
  addNote,
  addChannelIdentity,
  setupStages,
  syncFromOdoo,
  uploadImages,
  uploadDocument,
};
