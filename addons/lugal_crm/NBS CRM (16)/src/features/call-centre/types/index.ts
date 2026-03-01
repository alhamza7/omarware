export interface Call {
  id:                  number;
  call_number?:        string;
  direction:           'inbound' | 'outbound';
  customer_id?:        number;
  customer_name?:      string;
  agent_id?:           number;
  agent_name?:         string;
  branch_id?:          number;
  status:              'ringing' | 'active' | 'ended' | 'missed';
  started_at?:         string;
  ended_at?:           string;
  duration_seconds?:   number;
  recording_url?:      string;
  script_id?:          number;
  qa_score?:           number;
  post_call_notes?:    string;
  is_deleted:          boolean;
}

export interface CallScript {
  id:       number;
  title:    string;
  category: string;
  question: string;
  answer:   string;
}

export interface CallQueue {
  id:           number;
  customer_id:  number;
  customer_name:string;
  phone:        string;
  position:     number;
  status:       string;
  wait_minutes: number;
}

export interface StartCallPayload {
  direction:    'inbound' | 'outbound';
  customer_id?: number;
  phone?:       string;
  branch_id?:   number;
  script_id?:   number;
}

export interface EndCallPayload {
  post_call_notes?: string;
  qa_score?:        number;
}
