import { useWorkforce } from '../hooks/useWorkforce';
import { Agents } from '../../../app/components/agents/agents';

interface WorkforceContainerProps {
  branchId?: number;
}

/** Connects Agents/Workforce UI with live data from API */
export function WorkforceContainer({ branchId }: WorkforceContainerProps) {
  const { agents, shifts, attendance, isLoading, error, createShift } = useWorkforce(branchId);

  return (
    <Agents
      agents={agents as never}
      shifts={shifts as never}
      attendance={attendance as never}
      isLoading={isLoading}
      error={error}
      onCreateShift={createShift as never}
    />
  );
}
