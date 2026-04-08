export interface OmniMessage {
  id:          number;
  channel:     'whatsapp' | 'instagram' | 'telegram' | 'email' | 'sms' | 'website';
  direction:   'inbound' | 'outbound';
  customer_id?: number;
  customer_name?:string;
  body:        string;
  sent_at:     string;
  is_read:     boolean;
  agent_id?:   number;
  branch_id?:  number;
}

export interface OmniConversation {
  id:             number;
  customer_id?:   number;
  customer_name?: string;
  channel:        string;
  last_message?:  string;
  last_at?:       string;
  unread_count:   number;
  status:         'open' | 'resolved';
}

export interface SendMessagePayload {
  conversation_id?: number;
  customer_id?:     number;
  channel:          string;
  body:             string;
}
