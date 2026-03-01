import { useCalls } from '../hooks/useCalls';
import { CallCentre } from '../../../app/components/call-centre/call-centre';

interface CallCentreContainerProps {
  branchId?: number;
}

/**
 * Injects live API data into the CallCentre UI component.
 * The UI component remains a pure presenter; all logic lives here.
 */
export function CallCentreContainer({ branchId }: CallCentreContainerProps) {
  const {
    calls,
    activeCall,
    queue,
    scripts,
    isLoading,
    error,
    startCall,
    endCall,
  } = useCalls(branchId);

  // Pass data + handlers to the existing pure CallCentre component
  return (
    <CallCentre
      calls={calls as never}
      activeCall={activeCall as never}
      queue={queue as never}
      scripts={scripts as never}
      isLoading={isLoading}
      error={error}
      onStartCall={startCall as never}
      onEndCall={endCall as never}
    />
  );
}
