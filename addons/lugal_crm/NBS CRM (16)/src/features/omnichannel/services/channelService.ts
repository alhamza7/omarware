import { apiPost } from '../../../shared/services/apiClient';
import type { ApiResult } from '../../../shared/services/apiClient';
import type { OmniMessage, OmniConversation, SendMessagePayload } from '../types';
import type { PaginatedResponse } from '../../../shared/types';

/**
 * POST /api/crm/channels/messages/list
 * List all inbound messages / conversations.
 */
async function listConversations(params: {
  page?: number;
  status?: string;
  channel?: string;
  branch_id?: number;
}): Promise<ApiResult<PaginatedResponse<OmniConversation>>> {
  return apiPost('/api/crm/channels/messages/list', {
    page:      params.page      ?? 1,
    per_page:  25,
    status:    params.status    ?? null,
    channel:   params.channel   ?? null,
    branch_id: params.branch_id ?? null,
  });
}

/**
 * POST /api/crm/channels/messages/conversation
 * Get all messages in a single conversation thread.
 */
async function getMessages(
  conversationId: number,
  page = 1,
): Promise<ApiResult<PaginatedResponse<OmniMessage>>> {
  return apiPost('/api/crm/channels/messages/conversation', {
    conversation_id: conversationId,
    page,
  });
}

/**
 * POST /api/crm/channels/messages/create
 * Send an outbound message via the specified channel.
 */
async function sendMessage(payload: SendMessagePayload): Promise<ApiResult<OmniMessage>> {
  return apiPost('/api/crm/channels/messages/create', {
    customer_id: payload.customer_id ?? null,
    channel:     payload.channel,
    content:     payload.body,
    direction:   'outbound',
  });
}

/**
 * POST /api/crm/channels/messages/:id/resolve
 * Mark a conversation as resolved.
 */
async function resolveConversation(id: number): Promise<ApiResult<OmniConversation>> {
  return apiPost(`/api/crm/channels/messages/${id}/resolve`, {});
}

/**
 * POST /api/crm/channels/messages/:id/assign
 * Assign conversation to an agent.
 */
async function assignConversation(id: number, agentId: number): Promise<ApiResult<OmniConversation>> {
  return apiPost(`/api/crm/channels/messages/${id}/assign`, { assigned_to_id: agentId });
}

/**
 * POST /api/crm/channels/messages/:id/reply
 * Reply to an existing message thread.
 */
async function replyToMessage(id: number, content: string): Promise<ApiResult<OmniMessage>> {
  return apiPost(`/api/crm/channels/messages/${id}/reply`, { content });
}

/**
 * POST /api/crm/channels/messages/:id/transfer
 * Transfer conversation to another agent.
 */
async function transferConversation(id: number, newOwnerId: number): Promise<ApiResult<OmniConversation>> {
  return apiPost(`/api/crm/channels/messages/${id}/transfer`, { new_owner_id: newOwnerId });
}

/** POST /api/crm/channels/config_list — get channel config per branch */
async function getChannelConfig(branchId?: number): Promise<ApiResult<unknown[]>> {
  return apiPost('/api/crm/channels/config_list', { branch_id: branchId ?? null });
}

export const channelService = {
  listConversations,
  getMessages,
  sendMessage,
  resolveConversation,
  assignConversation,
  replyToMessage,
  transferConversation,
  getChannelConfig,
};
