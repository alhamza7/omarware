import { create } from 'zustand';
import type { OmniConversation, OmniMessage } from '../types';

interface OmnichannelStore {
  conversations:      OmniConversation[];
  activeConversation: OmniConversation | null;
  messages:           OmniMessage[];
  totalConversations: number;
  isLoading:          boolean;
  error:              string | null;
  channelFilter:      string | null;

  setConversations:      (convs: OmniConversation[], total: number) => void;
  setActiveConversation: (conv: OmniConversation | null) => void;
  setMessages:           (messages: OmniMessage[]) => void;
  addMessage:            (message: OmniMessage) => void;
  setLoading:            (loading: boolean) => void;
  setError:              (error: string | null) => void;
  setChannelFilter:      (channel: string | null) => void;
  updateConversation:    (conv: OmniConversation) => void;
}

export const useOmnichannelStore = create<OmnichannelStore>((set) => ({
  conversations:      [],
  activeConversation: null,
  messages:           [],
  totalConversations: 0,
  isLoading:          false,
  error:              null,
  channelFilter:      null,

  setConversations:      (conversations, totalConversations) =>
    set({ conversations, totalConversations, isLoading: false }),
  setActiveConversation: (activeConversation) =>
    set({ activeConversation, messages: [] }),
  setMessages:           (messages) => set({ messages }),
  addMessage:            (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLoading:            (isLoading) => set({ isLoading }),
  setError:              (error) => set({ error, isLoading: false }),
  setChannelFilter:      (channelFilter) => set({ channelFilter }),
  updateConversation:    (updated) =>
    set((s) => ({
      conversations:      s.conversations.map((c) => (c.id === updated.id ? updated : c)),
      activeConversation: s.activeConversation?.id === updated.id ? updated : s.activeConversation,
    })),
}));
