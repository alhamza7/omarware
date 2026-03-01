// ═══════════════════════════════════════════════════════════
//  Tickets — Data Model & Mock Data
//  Connected to: Omni-Channel, Customers, Agents, SLA Rules
//  Numbering: Configurable reset per year or cumulative
// ═══════════════════════════════════════════════════════════

export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
export type TicketPriority = "low" | "normal" | "high" | "urgent";

// Classification — flexible: pre-defined + ability to add custom
export const defaultClassifications = [
  "سعر", "توفر", "شكوى", "استبدال", "توصيل", "متابعة", "معلومات عامة",
] as const;
export type TicketClassification = typeof defaultClassifications[number] | string;

export interface Ticket {
  id: string;
  number: string; // e.g. "TK-2026-0001"
  subject: string;
  description: string;
  classification: TicketClassification;
  status: TicketStatus;
  priority: TicketPriority;
  customerId: string;
  customerName: string;
  assignedAgent: string | null;
  assignedAgentName?: string;
  channel: string; // which channel it came from
  conversationId?: string;
  createdAt: string;
  updatedAt: string;
  closedAt?: string;
  slaDeadline: string;
  slaBreach: boolean;
  escalated: boolean;
  escalatedTo?: string;
  // Auto-filled after call
  autoCreated: boolean;
  callRecordingId?: string;
  // History
  history: TicketHistoryEntry[];
  // Follow-up flag
  followUp: boolean;
  followUpDate?: string;
  followUpNote?: string;
  // Transfer
  transferHistory: TicketTransfer[];
}

export interface TicketHistoryEntry {
  id: string;
  action: string;
  actor: string;
  timestamp: string;
  details?: string;
}

export interface TicketTransfer {
  id: string;
  from: string;
  to: string;
  reason: string;
  status: "pending" | "accepted" | "rejected";
  timestamp: string;
}

// ── Ticket Numbering Config ─────────────────────────────

export interface TicketNumberingConfig {
  prefix: string; // "TK"
  resetPerYear: boolean; // if true, counter resets each year
  currentYear: number;
  currentCounter: number;
}

export const defaultNumberingConfig: TicketNumberingConfig = {
  prefix: "TK",
  resetPerYear: true,
  currentYear: 2026,
  currentCounter: 47,
};

export function generateTicketNumber(config: TicketNumberingConfig): string {
  const counter = String(config.currentCounter).padStart(4, "0");
  return config.resetPerYear
    ? `${config.prefix}-${config.currentYear}-${counter}`
    : `${config.prefix}-${counter}`;
}

// ── Mock Tickets ────────────────────────────────────────

export const mockTickets: Ticket[] = [
  {
    id: "tk-001",
    number: "TK-2026-0041",
    subject: "استفسار عن سعر العود الملكي",
    description: "العميل يستفسر عن أسعار العود الملكي بالأحجام المختلفة",
    classification: "سعر",
    status: "open",
    priority: "normal",
    customerId: "C-001",
    customerName: "أحمد محمد العلي",
    assignedAgent: "emp-01",
    assignedAgentName: "سعود المالكي",
    channel: "whatsapp",
    conversationId: "conv-001",
    createdAt: "2026-02-23T10:15:00",
    updatedAt: "2026-02-23T10:15:00",
    slaDeadline: "2026-02-24T10:15:00",
    slaBreach: false,
    escalated: false,
    autoCreated: false,
    history: [
      { id: "h1", action: "إنشاء التكت", actor: "النظام", timestamp: "2026-02-23T10:15:00" },
      { id: "h2", action: "تعيين إلى سعود المالكي", actor: "النظام", timestamp: "2026-02-23T10:15:00" },
    ],
    followUp: false,
    transferHistory: [],
  },
  {
    id: "tk-002",
    number: "TK-2026-0042",
    subject: "شكوى تأخر توصيل",
    description: "العميلة تشتكي من تأخر وصول الطلب رقم ORD-4521",
    classification: "توصيل",
    status: "in_progress",
    priority: "high",
    customerId: "C-006",
    customerName: "سارة علي الحربي",
    assignedAgent: "emp-01",
    assignedAgentName: "سعود المالكي",
    channel: "instagram",
    conversationId: "conv-004",
    createdAt: "2026-02-22T14:10:00",
    updatedAt: "2026-02-23T09:00:00",
    slaDeadline: "2026-02-23T14:10:00",
    slaBreach: false,
    escalated: false,
    autoCreated: false,
    history: [
      { id: "h1", action: "إنشاء التكت", actor: "سعود المالكي", timestamp: "2026-02-22T14:10:00" },
      { id: "h2", action: "تغيير الحالة → قيد التنفيذ", actor: "سعود المالكي", timestamp: "2026-02-22T14:15:00" },
      { id: "h3", action: "إضافة ملاحظة: تم التواصل مع شركة الشحن", actor: "سعود المالكي", timestamp: "2026-02-23T09:00:00" },
    ],
    followUp: true,
    followUpDate: "2026-02-24T09:00:00",
    followUpNote: "متابعة وصول الطلب مع شركة الشحن",
    transferHistory: [],
  },
  {
    id: "tk-003",
    number: "TK-2026-0043",
    subject: "طلب فاتورة",
    description: "العميل يطلب فاتورة الطلب الأخير",
    classification: "معلومات عامة",
    status: "open",
    priority: "high",
    customerId: "C-003",
    customerName: "خالد سعد القحطاني",
    assignedAgent: null,
    channel: "email",
    conversationId: "conv-006",
    createdAt: "2026-02-23T08:30:00",
    updatedAt: "2026-02-23T08:30:00",
    slaDeadline: "2026-02-23T20:30:00",
    slaBreach: true,
    escalated: true,
    escalatedTo: "فهد الراشد",
    autoCreated: false,
    history: [
      { id: "h1", action: "إنشاء التكت", actor: "النظام", timestamp: "2026-02-23T08:30:00" },
      { id: "h2", action: "تصعيد — تجاوز SLA", actor: "النظام", timestamp: "2026-02-23T08:36:00" },
    ],
    followUp: true,
    followUpDate: "2026-02-23T12:00:00",
    followUpNote: "إرسال الفاتورة للعميل VIP",
    transferHistory: [],
  },
  {
    id: "tk-004",
    number: "TK-2026-0044",
    subject: "استبدال عطر",
    description: "العميلة تريد استبدال عطر بسبب رائحة مختلفة عن المتوقع",
    classification: "استبدال",
    status: "resolved",
    priority: "normal",
    customerId: "C-002",
    customerName: "فاطمة عبدالله السالم",
    assignedAgent: "emp-02",
    assignedAgentName: "منى الشهري",
    channel: "whatsapp",
    createdAt: "2026-02-21T11:00:00",
    updatedAt: "2026-02-22T16:00:00",
    closedAt: "2026-02-22T16:00:00",
    slaDeadline: "2026-02-22T11:00:00",
    slaBreach: false,
    escalated: false,
    autoCreated: false,
    history: [
      { id: "h1", action: "إنشاء التكت", actor: "منى الشهري", timestamp: "2026-02-21T11:00:00" },
      { id: "h2", action: "تغيير الحالة → قيد التنفيذ", actor: "منى الشهري", timestamp: "2026-02-21T11:30:00" },
      { id: "h3", action: "معالجة الاستبدال — طلب شحن عكسي", actor: "منى الشهري", timestamp: "2026-02-22T10:00:00" },
      { id: "h4", action: "تغيير الحالة → تم الحل", actor: "منى الشهري", timestamp: "2026-02-22T16:00:00" },
    ],
    followUp: false,
    transferHistory: [],
  },
  {
    id: "tk-005",
    number: "TK-2026-0045",
    subject: "استفسار توفر عطر معين",
    description: "العميل يستفسر عن توفر عطر Tom Ford في المخزون",
    classification: "توفر",
    status: "closed",
    priority: "low",
    customerId: "C-007",
    customerName: "محمد عبدالله العتيبي",
    assignedAgent: "emp-03",
    assignedAgentName: "عبدالله الحربي",
    channel: "webchat",
    createdAt: "2026-02-20T15:00:00",
    updatedAt: "2026-02-20T16:30:00",
    closedAt: "2026-02-20T16:30:00",
    slaDeadline: "2026-02-21T15:00:00",
    slaBreach: false,
    escalated: false,
    autoCreated: true,
    history: [
      { id: "h1", action: "إنشاء تلقائي بعد انتهاء المكالمة", actor: "النظام", timestamp: "2026-02-20T15:00:00" },
      { id: "h2", action: "تعيين إلى عبدالله الحربي", actor: "النظام", timestamp: "2026-02-20T15:00:00" },
      { id: "h3", action: "الرد على العميل — المنتج غير متوفر حالياً", actor: "عبدالله الحربي", timestamp: "2026-02-20T15:45:00" },
      { id: "h4", action: "إغلاق التكت", actor: "عبدالله الحربي", timestamp: "2026-02-20T16:30:00" },
    ],
    followUp: false,
    transferHistory: [],
  },
  {
    id: "tk-006",
    number: "TK-2026-0046",
    subject: "شكوى جودة المنتج",
    description: "العميل يشتكي من أن العطر الذي استلمه لا يثبت بشكل جيد",
    classification: "شكوى",
    status: "in_progress",
    priority: "urgent",
    customerId: "C-011",
    customerName: "ماجد عمر السبيعي",
    assignedAgent: "emp-01",
    assignedAgentName: "سعود المالكي",
    channel: "whatsapp",
    createdAt: "2026-02-23T07:00:00",
    updatedAt: "2026-02-23T09:30:00",
    slaDeadline: "2026-02-23T19:00:00",
    slaBreach: false,
    escalated: false,
    autoCreated: false,
    history: [
      { id: "h1", action: "إنشاء التكت", actor: "سعود المالكي", timestamp: "2026-02-23T07:00:00" },
      { id: "h2", action: "تغيير الأولوية → عاجل", actor: "فهد الراشد", timestamp: "2026-02-23T07:30:00" },
      { id: "h3", action: "تعليق: يحتاج فحص من قسم الجودة", actor: "سعود المالكي", timestamp: "2026-02-23T09:30:00" },
    ],
    followUp: true,
    followUpDate: "2026-02-24T10:00:00",
    followUpNote: "انتظار نتيجة فحص الجودة",
    transferHistory: [
      { id: "tr-01", from: "سعود المالكي", to: "فهد الراشد", reason: "يحتاج موافقة المشرف على الاستبدال", status: "accepted", timestamp: "2026-02-23T09:30:00" },
    ],
  },
  {
    id: "tk-007",
    number: "TK-2026-0047",
    subject: "متابعة طلب سابق",
    description: "متابعة طلب عميل بخصوص وصول شحنة عينات",
    classification: "متابعة",
    status: "open",
    priority: "normal",
    customerId: "C-004",
    customerName: "نورة بدر المالكي",
    assignedAgent: "emp-02",
    assignedAgentName: "منى الشهري",
    channel: "whatsapp2",
    conversationId: "conv-007",
    createdAt: "2026-02-22T14:30:00",
    updatedAt: "2026-02-22T16:00:00",
    slaDeadline: "2026-02-23T14:30:00",
    slaBreach: false,
    escalated: false,
    autoCreated: false,
    history: [
      { id: "h1", action: "إنشاء التكت", actor: "منى الشهري", timestamp: "2026-02-22T14:30:00" },
    ],
    followUp: true,
    followUpDate: "2026-02-23T14:00:00",
    followUpNote: "التأكد من وصول العينات",
    transferHistory: [],
  },
];

// ── Follow-up Items (aggregated from tickets + customer + products) ──

export interface FollowUpItem {
  id: string;
  type: "ticket" | "customer" | "product" | "credit";
  subject: string;
  details: string;
  linkedId: string; // ticket ID, customer ID, etc.
  linkedName: string;
  assignedAgent: string;
  assignedAgentName: string;
  dueDate: string;
  status: "pending" | "in_progress" | "resolved";
  createdAt: string;
  escalated: boolean;
  escalatedTo?: string;
  reminders: string[]; // dates of reminders set
}

export const mockFollowUps: FollowUpItem[] = [
  { id: "fu-01", type: "ticket", subject: "متابعة تأخر التوصيل", details: "الطلب ORD-4521 — متابعة مع شركة الشحن", linkedId: "tk-002", linkedName: "سارة علي الحربي", assignedAgent: "emp-01", assignedAgentName: "سعود المالكي", dueDate: "2026-02-24T09:00:00", status: "pending", createdAt: "2026-02-22T14:15:00", escalated: false, reminders: ["2026-02-23T09:00:00"] },
  { id: "fu-02", type: "ticket", subject: "إرسال فاتورة VIP", details: "إرسال فاتورة الطلب الأخير للعميل VIP", linkedId: "tk-003", linkedName: "خالد سعد القحطاني", assignedAgent: "emp-01", assignedAgentName: "سعود المالكي", dueDate: "2026-02-23T12:00:00", status: "pending", createdAt: "2026-02-23T08:30:00", escalated: true, escalatedTo: "فهد الراشد", reminders: [] },
  { id: "fu-03", type: "ticket", subject: "نتيجة فحص الجودة", details: "انتظار نتيجة فحص الجودة لعطر العميل", linkedId: "tk-006", linkedName: "ماجد عمر السبيعي", assignedAgent: "emp-01", assignedAgentName: "سعود المالكي", dueDate: "2026-02-24T10:00:00", status: "in_progress", createdAt: "2026-02-23T09:30:00", escalated: false, reminders: ["2026-02-24T08:00:00"] },
  { id: "fu-04", type: "credit", subject: "فاتورة مستحقة", details: "فاتورة رقم INV-2026-0089 مستحقة خلال 3 أيام", linkedId: "C-005", linkedName: "عبدالرحمن ياسر الدوسري", assignedAgent: "emp-02", assignedAgentName: "منى الشهري", dueDate: "2026-02-26T00:00:00", status: "pending", createdAt: "2026-02-20T00:00:00", escalated: false, reminders: ["2026-02-25T09:00:00"] },
  { id: "fu-05", type: "customer", subject: "إعادة تنشيط عميل خامل", details: "العميلة لم تطلب منذ 4 أشهر — إرسال عرض خاص", linkedId: "C-008", linkedName: "ريم سعود الراشد", assignedAgent: "emp-02", assignedAgentName: "منى الشهري", dueDate: "2026-02-25T10:00:00", status: "pending", createdAt: "2026-02-22T00:00:00", escalated: false, reminders: [] },
  { id: "fu-06", type: "ticket", subject: "متابعة عينات", details: "التأكد من وصول العينات للعميلة", linkedId: "tk-007", linkedName: "نورة بدر المالكي", assignedAgent: "emp-02", assignedAgentName: "منى الشهري", dueDate: "2026-02-23T14:00:00", status: "pending", createdAt: "2026-02-22T14:30:00", escalated: false, reminders: ["2026-02-23T13:00:00"] },
];

// ── Status Labels & Colors ──────────────────────────────

export const ticketStatusLabels: Record<TicketStatus, string> = {
  open: "مفتوح",
  in_progress: "قيد التنفيذ",
  resolved: "تم الحل",
  closed: "مغلق",
};

export const ticketStatusColors: Record<TicketStatus, string> = {
  open: "bg-blue-500/15 text-blue-500",
  in_progress: "bg-primary/15 text-primary",
  resolved: "bg-emerald-500/15 text-emerald-500",
  closed: "bg-muted-foreground/15 text-muted-foreground",
};

export const ticketPriorityLabels: Record<TicketPriority, string> = {
  low: "منخفض",
  normal: "عادي",
  high: "عالي",
  urgent: "عاجل",
};

export const ticketPriorityColors: Record<TicketPriority, string> = {
  low: "bg-muted/30 text-muted-foreground",
  normal: "bg-blue-500/10 text-blue-400",
  high: "bg-primary/15 text-primary",
  urgent: "bg-red-500/15 text-red-500",
};
