// ═══════════════════════════════════════════════════════════
//  Omni-Channel — Data Model & Mock Data
//  Channels: WhatsApp, WhatsApp2, Telegram, TikTok, Instagram, Snapchat, SMS, X
//  Connected to: Customers, Tickets, Agents, SLA Rules
// ═══════════════════════════════════════════════════════════

// ── Channel Definitions ──────────────────────────────────

export type ChannelType =
  | "whatsapp"
  | "whatsapp2"
  | "telegram"
  | "tiktok"
  | "instagram"
  | "snapchat"
  | "sms"
  | "x";

export interface ChannelConfig {
  id: ChannelType;
  label: string;
  labelEn: string;
  color: string;
  icon: string; // lucide icon name
  enabled: boolean;
  assignedAgents: string[]; // agent IDs — empty = free for all
  aiEnabled: boolean; // AI bot for after-hours
  autoReplyTemplate?: string;
}

export const channelConfigs: ChannelConfig[] = [
  { id: "whatsapp", label: "واتساب", labelEn: "WhatsApp", color: "#25D366", icon: "MessageCircle", enabled: true, assignedAgents: [], aiEnabled: true },
  { id: "whatsapp2", label: "واتساب 2", labelEn: "WhatsApp 2", color: "#128C7E", icon: "MessageCircle", enabled: true, assignedAgents: ["emp-02"], aiEnabled: false },
  { id: "telegram", label: "تيليجرام", labelEn: "Telegram", color: "#0088cc", icon: "Send", enabled: true, assignedAgents: [], aiEnabled: true },
  { id: "tiktok", label: "تيك توك", labelEn: "TikTok", color: "#ff0050", icon: "Music", enabled: true, assignedAgents: ["emp-03"], aiEnabled: false },
  { id: "instagram", label: "إنستقرام", labelEn: "Instagram", color: "#E4405F", icon: "Camera", enabled: true, assignedAgents: [], aiEnabled: true },
  { id: "snapchat", label: "سناب شات", labelEn: "Snapchat", color: "#FFFC00", icon: "Ghost", enabled: true, assignedAgents: [], aiEnabled: false },
  { id: "sms", label: "رسائل قصيرة", labelEn: "SMS", color: "#22c55e", icon: "Smartphone", enabled: true, assignedAgents: [], aiEnabled: false },
  { id: "x", label: "إكس", labelEn: "X", color: "#1DA1F2", icon: "AtSign", enabled: false, assignedAgents: [], aiEnabled: false },
];

// ── Conversation & Message Models ───────────────────────

export type ConversationStatus =
  | "open"          // customer sent, no agent response yet
  | "responded"     // agent responded, waiting customer reply
  | "waiting"       // customer replied again after agent response
  | "closed";

export type MessageSender = "customer" | "agent" | "ai" | "system";
export type MessageType = "text" | "image" | "file" | "voice" | "catalogue" | "invoice" | "template" | "internal_note";

export interface OCMessage {
  id: string;
  conversationId: string;
  sender: MessageSender;
  senderName: string;
  type: MessageType;
  content: string;
  timestamp: string;
  read: boolean;
  // internal notes visible only to agents
  isInternalNote?: boolean;
  mentionedAgents?: string[];
}

export interface OCConversation {
  id: string;
  channel: ChannelType;
  customerId: string | null; // null = unregistered lead
  customerName: string;
  customerPhone?: string;
  customerAvatar?: string;
  status: ConversationStatus;
  assignedAgent: string | null; // agent ID
  assignedAgentName?: string;
  activeWriter: string | null; // agent currently typing (visual block)
  priority: "normal" | "high" | "urgent";
  isVip: boolean;
  isUnregistered: boolean; // flagged as unregistered lead
  leadTag?: string; // "lead-whatsapp", "lead-tiktok" etc.
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  openedBy: string[]; // agent IDs who opened without responding
  createdAt: string;
  slaDeadline?: string; // from SLA rules
  isEscalated: boolean;
  escalatedAt?: string;
  aiHandled: boolean; // currently handled by AI bot
  linkedTicketId?: string;
  // audit
  messageCount: number;
  respondedCount: number;
  avgResponseTime?: number; // minutes
}

// ── Templates ───────────────────────────────────────────

export interface OCTemplate {
  id: string;
  name: string;
  channel: ChannelType | "all";
  content: string;
  category: "greeting" | "follow-up" | "catalogue" | "promotion" | "closing" | "auto-reply";
  variables: string[]; // e.g. ["customerName", "orderNumber"]
}

export const ocTemplates: OCTemplate[] = [
  { id: "tpl-01", name: "ترحيب عام", channel: "all", content: "أهلاً وسهلاً {{customerName}}! شكراً لتواصلك مع نور النبراس للعطور. كيف يمكننا مساعدتك؟", category: "greeting", variables: ["customerName"] },
  { id: "tpl-02", name: "ترحيب VIP", channel: "all", content: "مرحباً {{customerName}}! يسعدنا تواصلك معنا. كعميل مميز لدينا، نحن هنا لخدمتك. كيف نستطيع مساعدتك اليوم؟", category: "greeting", variables: ["customerName"] },
  { id: "tpl-03", name: "إرسال الكتالوج", channel: "whatsapp", content: "تفضل كتالوج نور النبراس الجديد 📋✨\nيشمل أحدث العطور والإصدارات المميزة", category: "catalogue", variables: [] },
  { id: "tpl-04", name: "متابعة طلب", channel: "all", content: "مرحباً {{customerName}}، نود التأكد من استلامك للطلب رقم {{orderNumber}}. هل كل شيء على ما يرام؟", category: "follow-up", variables: ["customerName", "orderNumber"] },
  { id: "tpl-05", name: "رد تلقائي خارج الدوام", channel: "all", content: "شكراً لتواصلك! نحن حالياً خارج ساعات العمل. سيتم الرد عليك فور بدء الدوام. يمكنك الاستفسار عن الأسعار والمخزون من خلال المساعد الذكي.", category: "auto-reply", variables: [] },
  { id: "tpl-06", name: "عرض ترويجي", channel: "whatsapp", content: "🎉 عرض خاص لعملائنا!\n{{promotionDetails}}\nالعرض ساري حتى {{expiryDate}}", category: "promotion", variables: ["promotionDetails", "expiryDate"] },
  { id: "tpl-07", name: "إغلاق المحادثة", channel: "all", content: "شكراً لتواصلك {{customerName}}. نتمنى أن نكون قد أفدناك. لا تتردد بالتواصل في أي وقت 🌟", category: "closing", variables: ["customerName"] },
];

// ── Mock Conversations ──────────────────────────────────

export const mockConversations: OCConversation[] = [
  {
    id: "conv-001",
    channel: "whatsapp",
    customerId: "C-001",
    customerName: "أحمد محمد العلي",
    customerPhone: "+966 50 123 4567",
    status: "open",
    assignedAgent: "emp-01",
    assignedAgentName: "سعود المالكي",
    activeWriter: null,
    priority: "urgent",
    isVip: true,
    isUnregistered: false,
    lastMessage: "أحتاج عينة من العود الملكي الجديد",
    lastMessageTime: "2026-02-23T10:30:00",
    unreadCount: 3,
    openedBy: ["emp-01"],
    createdAt: "2026-02-23T10:15:00",
    slaDeadline: "2026-02-23T10:16:00",
    isEscalated: false,
    aiHandled: false,
    messageCount: 5,
    respondedCount: 2,
    avgResponseTime: 1.5,
  },
  {
    id: "conv-002",
    channel: "telegram",
    customerId: null,
    customerName: "مستخدم تيليجرام",
    customerPhone: "+966 55 000 1111",
    status: "open",
    assignedAgent: null,
    activeWriter: null,
    priority: "normal",
    isVip: false,
    isUnregistered: true,
    leadTag: "lead-telegram",
    lastMessage: "هل عندكم عطور نسائية؟",
    lastMessageTime: "2026-02-23T10:25:00",
    unreadCount: 1,
    openedBy: [],
    createdAt: "2026-02-23T10:25:00",
    isEscalated: false,
    aiHandled: true,
    messageCount: 1,
    respondedCount: 0,
  },
  {
    id: "conv-003",
    channel: "whatsapp",
    customerId: "C-002",
    customerName: "فاطمة عبدالله السالم",
    customerPhone: "+966 55 987 6543",
    status: "responded",
    assignedAgent: "emp-02",
    assignedAgentName: "منى الشهري",
    activeWriter: null,
    priority: "normal",
    isVip: false,
    isUnregistered: false,
    lastMessage: "تم إرسال الكتالوج ✅",
    lastMessageTime: "2026-02-23T09:45:00",
    unreadCount: 0,
    openedBy: ["emp-02"],
    createdAt: "2026-02-23T09:30:00",
    isEscalated: false,
    aiHandled: false,
    messageCount: 8,
    respondedCount: 4,
    avgResponseTime: 2.0,
  },
  {
    id: "conv-004",
    channel: "instagram",
    customerId: "C-006",
    customerName: "سارة علي الحربي",
    customerPhone: "+966 59 555 6666",
    status: "waiting",
    assignedAgent: "emp-01",
    assignedAgentName: "سعود المالكي",
    activeWriter: null,
    priority: "high",
    isVip: false,
    isUnregistered: false,
    lastMessage: "متى يوصل الطلب؟",
    lastMessageTime: "2026-02-23T10:10:00",
    unreadCount: 2,
    openedBy: ["emp-01", "emp-03"],
    createdAt: "2026-02-22T14:00:00",
    isEscalated: false,
    aiHandled: false,
    messageCount: 12,
    respondedCount: 6,
    avgResponseTime: 3.5,
  },
  {
    id: "conv-005",
    channel: "tiktok",
    customerId: null,
    customerName: "user_tiktok_392",
    status: "open",
    assignedAgent: "emp-03",
    assignedAgentName: "عبدالله الحربي",
    activeWriter: "emp-03",
    priority: "normal",
    isVip: false,
    isUnregistered: true,
    leadTag: "lead-tiktok",
    lastMessage: "شفت المنتج عندكم في تيك توك وحبيت أستفسر",
    lastMessageTime: "2026-02-23T10:20:00",
    unreadCount: 1,
    openedBy: ["emp-03"],
    createdAt: "2026-02-23T10:18:00",
    isEscalated: false,
    aiHandled: false,
    messageCount: 3,
    respondedCount: 1,
    avgResponseTime: 2.0,
  },
  {
    id: "conv-006",
    channel: "sms",
    customerId: "C-003",
    customerName: "خالد سعد القحطاني",
    status: "open",
    assignedAgent: null,
    activeWriter: null,
    priority: "high",
    isVip: true,
    isUnregistered: false,
    lastMessage: "أريد فاتورة الطلب الأخير",
    lastMessageTime: "2026-02-23T08:30:00",
    unreadCount: 1,
    openedBy: [],
    createdAt: "2026-02-23T08:30:00",
    slaDeadline: "2026-02-23T08:31:00",
    isEscalated: true,
    escalatedAt: "2026-02-23T08:36:00",
    aiHandled: false,
    messageCount: 1,
    respondedCount: 0,
  },
  {
    id: "conv-007",
    channel: "whatsapp2",
    customerId: "C-004",
    customerName: "نورة بدر المالكي",
    customerPhone: "+966 53 456 7890",
    status: "responded",
    assignedAgent: "emp-02",
    assignedAgentName: "منى الشهري",
    activeWriter: null,
    priority: "normal",
    isVip: false,
    isUnregistered: false,
    lastMessage: "شكراً جزيلاً! طلبي وصل بحالة ممتازة",
    lastMessageTime: "2026-02-22T16:00:00",
    unreadCount: 0,
    openedBy: ["emp-02"],
    createdAt: "2026-02-22T14:30:00",
    isEscalated: false,
    aiHandled: false,
    messageCount: 6,
    respondedCount: 3,
    avgResponseTime: 1.8,
  },
  {
    id: "conv-008",
    channel: "snapchat",
    customerId: null,
    customerName: "مستخدم سناب",
    status: "open",
    assignedAgent: null,
    activeWriter: null,
    priority: "normal",
    isVip: false,
    isUnregistered: true,
    leadTag: "lead-snapchat",
    lastMessage: "هل يمكنني طلب عينات؟",
    lastMessageTime: "2026-02-23T10:28:00",
    unreadCount: 1,
    openedBy: [],
    createdAt: "2026-02-23T10:28:00",
    isEscalated: false,
    aiHandled: true,
    messageCount: 2,
    respondedCount: 0,
  },
];

// ── Mock Messages ───────────────────────────────────────

export const mockMessages: Record<string, OCMessage[]> = {
  "conv-001": [
    { id: "m-001", conversationId: "conv-001", sender: "customer", senderName: "أحمد محمد العلي", type: "text", content: "السلام عليكم", timestamp: "2026-02-23T10:15:00", read: true },
    { id: "m-002", conversationId: "conv-001", sender: "agent", senderName: "سعود المالكي", type: "text", content: "وعليكم السلام! أهلاً بك أخ أحمد، كيف نقدر نساعدك اليوم؟", timestamp: "2026-02-23T10:16:30", read: true },
    { id: "m-003", conversationId: "conv-001", sender: "customer", senderName: "أحمد محمد العلي", type: "text", content: "أبغى أعرف عن العود الملكي الجديد", timestamp: "2026-02-23T10:18:00", read: true },
    { id: "m-004", conversationId: "conv-001", sender: "agent", senderName: "سعود المالكي", type: "text", content: "بالتأكيد! العود الملكي الجديد إصدار محدود، متوفر بعبوات 25مل و50مل", timestamp: "2026-02-23T10:20:00", read: true },
    { id: "m-005", conversationId: "conv-001", sender: "customer", senderName: "أحمد محمد العلي", type: "text", content: "أحتاج عينة من العود الملكي الجديد", timestamp: "2026-02-23T10:30:00", read: false },
    { id: "m-int-01", conversationId: "conv-001", sender: "agent", senderName: "سعود المالكي", type: "internal_note", content: "عميل VIP مهتم بالعود الملكي — يحتاج عينة مخصصة @منى", timestamp: "2026-02-23T10:31:00", read: true, isInternalNote: true, mentionedAgents: ["emp-02"] },
  ],
  "conv-004": [
    { id: "m-020", conversationId: "conv-004", sender: "customer", senderName: "سارة علي الحربي", type: "text", content: "مرحباً، طلبت عطر روز باريس قبل 3 أيام", timestamp: "2026-02-22T14:00:00", read: true },
    { id: "m-021", conversationId: "conv-004", sender: "agent", senderName: "سعود المالكي", type: "text", content: "أهلاً سارة! خليني أتحقق من حالة الطلب", timestamp: "2026-02-22T14:05:00", read: true },
    { id: "m-022", conversationId: "conv-004", sender: "agent", senderName: "سعود المالكي", type: "text", content: "طلبك رقم #ORD-4521 تم شحنه أمس ومتوقع وصوله خلال 24-48 ساعة", timestamp: "2026-02-22T14:08:00", read: true },
    { id: "m-023", conversationId: "conv-004", sender: "customer", senderName: "سارة علي الحربي", type: "text", content: "متى يوصل الطلب؟", timestamp: "2026-02-23T10:10:00", read: false },
  ],
};

// ── SLA Config (connected to Rule Engine) ───────────────

export interface OCSlaConfig {
  firstResponseTime: number; // minutes
  firstResponseTimeVip: number;
  escalationTime: number; // minutes after SLA breach
  supervisorSla: number; // minutes for supervisor response after escalation
  reminderInterval: number; // minutes between reminders
}

export const defaultSlaConfig: OCSlaConfig = {
  firstResponseTime: 3,
  firstResponseTimeVip: 1,
  escalationTime: 5,
  supervisorSla: 10,
  reminderInterval: 2,
};

// ── Agent Presence (live status) ────────────────────────

export type AgentPresence = "available" | "busy" | "on-call" | "offline" | "on-leave";
export type AgentActivity = "idle" | "in-chat" | "on-call" | "writing" | "reviewing";

export interface OCAgent {
  id: string;
  name: string;
  role: "agent" | "supervisor" | "manager";
  presence: AgentPresence;
  activity: AgentActivity;
  activeChannel?: ChannelType;
  activeConversations: number;
  maxCapacity: number;
  skills: string[];
  channels: ChannelType[];
  totalCalls: number;
  totalChats: number;
  avgHandleTime: number; // minutes
  todayReplied: number;
  todayMissed: number;
}

export const mockAgents: OCAgent[] = [
  { id: "emp-01", name: "سعود المالكي", role: "agent", presence: "available", activity: "in-chat", activeChannel: "whatsapp", activeConversations: 2, maxCapacity: 5, skills: ["sales", "vip", "general"], channels: ["whatsapp", "instagram", "telegram"], totalCalls: 145, totalChats: 320, avgHandleTime: 4.2, todayReplied: 18, todayMissed: 1 },
  { id: "emp-02", name: "منى الشهري", role: "agent", presence: "available", activity: "idle", activeConversations: 1, maxCapacity: 5, skills: ["sales", "general", "complaints"], channels: ["whatsapp", "whatsapp2", "sms"], totalCalls: 98, totalChats: 256, avgHandleTime: 3.8, todayReplied: 12, todayMissed: 0 },
  { id: "emp-03", name: "عبدالله الحربي", role: "agent", presence: "busy", activity: "writing", activeChannel: "tiktok", activeConversations: 3, maxCapacity: 5, skills: ["social", "sales"], channels: ["tiktok", "instagram", "snapchat"], totalCalls: 45, totalChats: 189, avgHandleTime: 5.1, todayReplied: 8, todayMissed: 2 },
  { id: "emp-04", name: "فهد الراشد", role: "supervisor", presence: "available", activity: "reviewing", activeConversations: 0, maxCapacity: 10, skills: ["vip", "complaints", "escalation"], channels: ["whatsapp", "telegram", "sms", "instagram", "tiktok", "whatsapp2", "snapchat"], totalCalls: 312, totalChats: 580, avgHandleTime: 6.0, todayReplied: 5, todayMissed: 0 },
];

// ── Calling List ────────────────────────────────────────

export interface CallingListItem {
  id: string;
  customerId: string;
  customerName: string;
  phone: string;
  target: string; // what to achieve
  notes: string;
  expectedSuccessRate: number; // 0-100
  assignedAgent: string;
  status: "pending" | "called" | "success" | "failed" | "rescheduled";
  createdBy: string;
  createdAt: string;
  calledAt?: string;
  outcome?: string;
}

export const mockCallingList: CallingListItem[] = [
  { id: "cl-01", customerId: "C-001", customerName: "أحمد محمد العلي", phone: "+966 50 123 4567", target: "عرض العود الملكي الجديد", notes: "عميل VIP مهتم بالإصدارات المحدودة", expectedSuccessRate: 85, assignedAgent: "emp-01", status: "pending", createdBy: "فهد الراشد", createdAt: "2026-02-23T08:00:00" },
  { id: "cl-02", customerId: "C-006", customerName: "سارة علي الحربي", phone: "+966 59 555 6666", target: "متابعة استلام الطلب", notes: "طلبت روز باريس — متابعة رضا العميل", expectedSuccessRate: 90, assignedAgent: "emp-02", status: "called", createdBy: "فهد الراشد", createdAt: "2026-02-23T08:00:00", calledAt: "2026-02-23T09:15:00", outcome: "تم التأكيد — راضية عن الخدمة" },
  { id: "cl-03", customerId: "C-008", customerName: "ريم سعود الراشد", phone: "+966 55 999 0000", target: "إعادة تنشيط العميل", notes: "عميلة خاملة منذ 4 أشهر — عرض خصم 15%", expectedSuccessRate: 40, assignedAgent: "emp-01", status: "pending", createdBy: "فهد الراشد", createdAt: "2026-02-23T08:00:00" },
  { id: "cl-04", customerId: "C-010", customerName: "هند خالد الزهراني", phone: "+966 56 444 5555", target: "إعادة تنشيط العميل", notes: "خاملة منذ 6 أشهر — إعادة تعريف بالمنتجات الجديدة", expectedSuccessRate: 30, assignedAgent: "emp-03", status: "rescheduled", createdBy: "فهد الراشد", createdAt: "2026-02-22T08:00:00" },
];

// ── Escalation Queue ────────────────────────────────────

export interface EscalationItem {
  id: string;
  conversationId: string;
  customerName: string;
  channel: ChannelType;
  reason: string;
  waitingMinutes: number;
  assignedTo: string | null;
  createdAt: string;
  priority: "high" | "urgent";
}

export const mockEscalations: EscalationItem[] = [
  { id: "esc-01", conversationId: "conv-006", customerName: "خالد سعد القحطاني", channel: "sms", reason: "تجاوز SLA — بدون رد", waitingMinutes: 120, assignedTo: null, createdAt: "2026-02-23T08:36:00", priority: "urgent" },
];

// ── Missed Calls (Agent View) ───────────────────────────

export type MissedCallAgentStatus = "pending" | "callback-scheduled" | "returned" | "resolved";

export interface OCMissedCall {
  id: string;
  customerName: string;
  customerPhone: string;
  channel: ChannelType | "phone";
  missedAt: string;
  attempts: number;
  reason: string;
  status: MissedCallAgentStatus;
  assignedAgent: string; // agent id
  assignedBy: string; // supervisor name
  callbackTime?: string;
  note?: string;
}

export const mockOCMissedCalls: OCMissedCall[] = [
  { id: "omc-01", customerName: "أحمد محمد العلي", customerPhone: "+966 50 123 4567", channel: "phone", missedAt: "2026-02-25T09:15:00", attempts: 2, reason: "جميع الموظفين مشغولون", status: "pending", assignedAgent: "emp-01", assignedBy: "فهد الراشد", note: "عميل VIP — يجب ��لاتصال فوراً" },
  { id: "omc-02", customerName: "ريم سعود الراشد", customerPhone: "+966 55 999 0000", channel: "phone", missedAt: "2026-02-25T10:05:00", attempts: 1, reason: "الموظف في استراحة", status: "pending", assignedAgent: "emp-01", assignedBy: "فهد الراشد" },
  { id: "omc-03", customerName: "فاطمة عبدالله السالم", customerPhone: "+966 55 987 6543", channel: "whatsapp", missedAt: "2026-02-25T09:32:00", attempts: 1, reason: "محادثة واتساب لم تُقرأ", status: "callback-scheduled", assignedAgent: "emp-02", assignedBy: "فهد الراشد", callbackTime: "2026-02-25T10:00:00" },
  { id: "omc-04", customerName: "محمد الدوسري", customerPhone: "+966 53 333 4444", channel: "phone", missedAt: "2026-02-25T09:55:00", attempts: 4, reason: "تكرار الاتصال — لا يوجد متاح", status: "pending", assignedAgent: "emp-02", assignedBy: "فهد الراشد", note: "أولوية عالية — 4 محاولات" },
  { id: "omc-05", customerName: "نوف العتيبي", customerPhone: "+966 50 777 8888", channel: "whatsapp", missedAt: "2026-02-25T10:18:00", attempts: 1, reason: "العميل أنهى المحادثة قبل الرد", status: "returned", assignedAgent: "emp-03", assignedBy: "فهد الراشد", note: "تم الاتصال — تريد معلومات عن عطر جديد" },
  { id: "omc-06", customerName: "عبدالرحمن الغامدي", customerPhone: "+966 54 222 1111", channel: "phone", missedAt: "2026-02-25T08:20:00", attempts: 2, reason: "السعة القصوى ممتلئة", status: "resolved", assignedAgent: "emp-03", assignedBy: "فهد الراشد", note: "تم حل المشكلة عبر الهاتف" },
];

// ── Transfer Request Model ──────────────────────────────

export type TransferStatus = "pending" | "approved" | "rejected" | "cancelled";

export interface TransferRequest {
  id: string;
  conversationId: string;
  customerName: string;
  channel: ChannelType;
  fromAgentId: string;
  fromAgentName: string;
  toAgentId: string;
  toAgentName: string;
  reason: string;
  rejectionReason?: string;
  status: TransferStatus;
  createdAt: string;
  respondedAt?: string;
}