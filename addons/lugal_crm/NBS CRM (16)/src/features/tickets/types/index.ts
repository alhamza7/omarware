export interface Ticket {
  id:            number;
  title:         string;
  description?:  string;
  customer_id?:  number;
  customer_name?:string;
  assigned_to?:  number;
  agent_name?:   string;
  branch_id?:    number;
  priority:      'low' | 'medium' | 'high' | 'urgent';
  status:        'open' | 'in_progress' | 'pending' | 'resolved' | 'closed';
  channel?:      string;
  sla_deadline?: string;
  sla_breached:  boolean;
  tags?:         string[];
  created_at:    string;
  updated_at?:   string;
  is_deleted:    boolean;
}

export interface FollowUp {
  id:          number;
  ticket_id:   number;
  note:        string;
  agent_id:    number;
  agent_name?: string;
  created_at:  string;
}

export interface CreateTicketPayload {
  title:        string;
  description?: string;
  customer_id?: number;
  priority?:    Ticket['priority'];
  channel?:     string;
  branch_id?:   number;
}
