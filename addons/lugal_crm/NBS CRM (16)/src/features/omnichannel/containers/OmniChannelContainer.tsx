import { useOmnichannel } from '../hooks/useOmnichannel';
import { OmniChannel } from '../../../app/components/omni-channel/omni-channel';

/** Connects OmniChannel UI with live conversation + message data from API */
export function OmniChannelContainer() {
  const {
    conversations, activeConversation, messages, isLoading, error,
    channelFilter, setChannelFilter, openConversation, sendMessage, resolveConversation,
  } = useOmnichannel();

  return (
    <OmniChannel
      conversations={conversations as never}
      activeConversation={activeConversation as never}
      messages={messages as never}
      isLoading={isLoading}
      error={error}
      channelFilter={channelFilter}
      onChannelFilter={setChannelFilter}
      onSelectConversation={(id) => openConversation(id)}
      onSendMessage={sendMessage as never}
      onResolve={(id) => resolveConversation(id)}
    />
  );
}
