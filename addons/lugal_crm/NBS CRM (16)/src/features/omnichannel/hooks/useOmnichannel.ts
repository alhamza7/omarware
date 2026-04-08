import { useCallback, useEffect } from 'react';
import { useOmnichannelStore } from '../store/omnichannelStore';
import { channelService } from '../services/channelService';
import type { SendMessagePayload } from '../types';

export function useOmnichannel() {
  const store = useOmnichannelStore();

  const fetchConversations = useCallback(async () => {
    store.setLoading(true);
    const result = await channelService.listConversations({
      channel: store.channelFilter ?? undefined,
    });
    if (result.success && result.data) {
      store.setConversations(result.data.items, result.data.total);
    } else {
      store.setError(result.error ?? 'Failed to load conversations');
    }
  }, [store.channelFilter]);

  const openConversation = useCallback(async (conversationId: number) => {
    const found = store.conversations.find((c) => c.id === conversationId);
    if (found) store.setActiveConversation(found);
    const result = await channelService.getMessages(conversationId);
    if (result.success && result.data) store.setMessages(result.data.items);
  }, [store]);

  const sendMessage = useCallback(async (payload: SendMessagePayload) => {
    const result = await channelService.sendMessage(payload);
    if (result.success && result.data) store.addMessage(result.data);
    return result;
  }, [store]);

  const resolveConversation = useCallback(async (id: number) => {
    const result = await channelService.resolveConversation(id);
    if (result.success && result.data) {
      store.updateConversation(result.data);
      store.setActiveConversation(null);
    }
    return result;
  }, [store]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return {
    conversations:      store.conversations,
    activeConversation: store.activeConversation,
    messages:           store.messages,
    isLoading:          store.isLoading,
    error:              store.error,
    channelFilter:      store.channelFilter,
    setChannelFilter:   store.setChannelFilter,
    fetchConversations,
    openConversation,
    sendMessage,
    resolveConversation,
  };
}
