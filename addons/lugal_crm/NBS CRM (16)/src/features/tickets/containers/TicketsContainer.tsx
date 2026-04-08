import { useTickets } from '../hooks/useTickets';
import { Tickets } from '../../../app/components/tickets/tickets';

interface TicketsContainerProps {
  branchId?: number;
}

/** Connects Tickets UI with live API data via useTickets hook */
export function TicketsContainer({ branchId }: TicketsContainerProps) {
  const {
    tickets, selectedTicket, followUps, isLoading, error,
    setSelected, fetchFollowUps, createTicket, closeTicket, addFollowUp, assignTicket,
  } = useTickets(branchId);

  return (
    <Tickets
      tickets={tickets as never}
      selectedTicket={selectedTicket as never}
      followUps={followUps as never}
      isLoading={isLoading}
      error={error}
      onSelectTicket={(t) => { setSelected(t as never); fetchFollowUps((t as never).id); }}
      onCreateTicket={createTicket as never}
      onCloseTicket={closeTicket}
      onAddFollowUp={addFollowUp}
      onAssignTicket={assignTicket}
    />
  );
}
