// ── Types ──────────────────────────────────────────

export type EmployeeRole = "agent" | "supervisor" | "manager" | "qa" | "qa-supervisor";
export type EmployeeStatus = "available" | "busy" | "break" | "offline" | "away";
export type ChannelType = "phone" | "whatsapp" | "email" | "instagram" | "x" | "live-chat";
export type SLAStatus = "on-track" | "warning" | "breached";
export type TaskStatus = "open" | "in-progress" | "completed" | "overdue";
export type TaskPriority = "urgent" | "high" | "normal" | "low";
export type TicketSeverity = "critical" | "high" | "medium" | "low";
export type TicketStatus = "open" | "escalated" | "in-progress" | "resolved" | "closed";
export type AuditAction = "login" | "logout" | "status-change" | "call-open" | "call-listen" | "recording-play" | "rule-edit" | "evaluate" | "ticket-open" | "conversation-transfer" | "message-review" | "approval" | "decision";

export interface Employee {
  id: string;
  name: string;
  avatar: string;
  role: EmployeeRole;
  status: EmployeeStatus;
  channel: ChannelType | null;
  openConversations: number;
  callsToday: number;
  messagesHandled: number;
  lastResponse: string;
  sla: SLAStatus;
  slaPercent: number;
  avgResponseTime: string;
  shift: string;
  loginTime: string;
  activeTime: string;
  idleTime: string;
  satisfaction: number;
}

export interface VIPCustomer {
  id: string;
  name: string;
  avatar: string;
  segment: string;
  totalSpent: number;
  lastOrder: string;
  lastContact: string;
  preferredChannel: ChannelType;
  assignedAgent: string;
  openIssues: number;
  satisfaction: number;
  tags: string[];
}

export interface Task {
  id: string;
  title: string;
  customerName: string;
  customerId: string;
  type: "call" | "follow-up" | "reply" | "task" | "escalation";
  reason: string;
  assignee: string | null;
  dueDate: string;
  dueTime: string;
  status: TaskStatus;
  priority: TaskPriority;
  channel: ChannelType;
  vip: boolean;
  notes: string;
  createdAt: string;
}

export interface Complaint {
  id: string;
  ticketNumber: string;
  customerName: string;
  customerId: string;
  customerType: "VIP" | "regular";
  type: string;
  severity: TicketSeverity;
  status: TicketStatus;
  assignee: string;
  createdAt: string;
  updatedAt: string;
  relatedConversation?: string;
  relatedEmployee?: string;
  description: string;
  steps: string[];
}

export interface AttendanceRecord {
  id: string;
  employeeName: string;
  employeeId: string;
  role: EmployeeRole;
  loginTime: string;
  logoutTime: string | null;
  hoursWorked: string;
  activeTime: string;
  idleTime: string;
  messagesHandled: number;
  callsHandled: number;
  ip: string;
  deviceType: "desktop" | "laptop" | "mobile" | "tablet";
  browser: string;
  location: string;
  isRemote: boolean;
  status: "present" | "late" | "absent" | "remote" | "half-day";
}

export interface AuditEntry {
  id: string;
  userId: string;
  userName: string;
  userRole: EmployeeRole;
  action: AuditAction;
  target: string;
  details: string;
  timestamp: string;
  ip: string;
}

export interface QAEvaluation {
  id: string;
  auditorId: string;
  auditorName: string;
  targetType: "call" | "message" | "conversation";
  targetId: string;
  targetAgent: string;
  customerName: string;
  score: number;
  maxScore: number;
  criteria: { name: string; score: number; max: number }[];
  notes: string;
  listenDuration: number;
  evaluatedAt: string;
  hasNotes: boolean;
  actuallyEvaluated: boolean;
}

export interface QAAuditor {
  id: string;
  name: string;
  avatar: string;
  evaluationsToday: number;
  evaluationsWeek: number;
  evaluationsMonth: number;
  avgListenDuration: number;
  totalListenTime: number;
  messagesReviewed: number;
  conversationsReviewed: number;
  loginTime: string;
  logoutTime: string | null;
  activeTime: string;
  idleTime: string;
  withNotes: number;
  withoutNotes: number;
  openedAndLeft: number;
  avgScore: number;
  productivity: number;
}

// ── Mock Data ──────────────────────────────────────

export const employees: Employee[] = [
  {
    id: "e1", name: "سارة الحربي", avatar: "سح", role: "agent",
    status: "busy", channel: "phone", openConversations: 5, callsToday: 18,
    messagesHandled: 45, lastResponse: "منذ دقيقتين", sla: "on-track", slaPercent: 94,
    avgResponseTime: "1:32", shift: "08:00 - 16:00", loginTime: "07:55",
    activeTime: "6:45", idleTime: "0:22", satisfaction: 4.8,
  },
  {
    id: "e2", name: "محمد العتيبي", avatar: "مع", role: "agent",
    status: "available", channel: "whatsapp", openConversations: 3, callsToday: 14,
    messagesHandled: 62, lastResponse: "منذ 5 دقائق", sla: "on-track", slaPercent: 88,
    avgResponseTime: "2:10", shift: "08:00 - 16:00", loginTime: "08:02",
    activeTime: "6:30", idleTime: "0:35", satisfaction: 4.6,
  },
  {
    id: "e3", name: "نورة الشمري", avatar: "نش", role: "agent",
    status: "busy", channel: "live-chat", openConversations: 8, callsToday: 21,
    messagesHandled: 78, lastResponse: "منذ دقيقة", sla: "warning", slaPercent: 76,
    avgResponseTime: "3:45", shift: "08:00 - 16:00", loginTime: "08:00",
    activeTime: "7:10", idleTime: "0:10", satisfaction: 4.9,
  },
  {
    id: "e4", name: "خالد الدوسري", avatar: "خد", role: "agent",
    status: "break", channel: null, openConversations: 2, callsToday: 11,
    messagesHandled: 28, lastResponse: "منذ 25 دقيقة", sla: "breached", slaPercent: 58,
    avgResponseTime: "6:20", shift: "12:00 - 20:00", loginTime: "12:05",
    activeTime: "3:40", idleTime: "1:15", satisfaction: 4.3,
  },
  {
    id: "e5", name: "ريم القحطاني", avatar: "رق", role: "agent",
    status: "available", channel: "email", openConversations: 4, callsToday: 16,
    messagesHandled: 53, lastResponse: "منذ 3 دقائق", sla: "on-track", slaPercent: 91,
    avgResponseTime: "1:55", shift: "12:00 - 20:00", loginTime: "11:58",
    activeTime: "5:20", idleTime: "0:28", satisfaction: 4.7,
  },
  {
    id: "e6", name: "عبدالله المطيري", avatar: "عم", role: "agent",
    status: "offline", channel: null, openConversations: 0, callsToday: 0,
    messagesHandled: 0, lastResponse: "—", sla: "on-track", slaPercent: 0,
    avgResponseTime: "—", shift: "16:00 - 00:00", loginTime: "—",
    activeTime: "0:00", idleTime: "0:00", satisfaction: 4.5,
  },
  {
    id: "e7", name: "فهد الراشد", avatar: "فر", role: "supervisor",
    status: "available", channel: "phone", openConversations: 2, callsToday: 6,
    messagesHandled: 15, lastResponse: "منذ 10 دقائق", sla: "on-track", slaPercent: 95,
    avgResponseTime: "1:10", shift: "08:00 - 16:00", loginTime: "07:50",
    activeTime: "7:00", idleTime: "0:15", satisfaction: 4.9,
  },
  {
    id: "e8", name: "منى السالم", avatar: "مس", role: "qa",
    status: "busy", channel: null, openConversations: 0, callsToday: 0,
    messagesHandled: 0, lastResponse: "—", sla: "on-track", slaPercent: 92,
    avgResponseTime: "—", shift: "08:00 - 16:00", loginTime: "08:00",
    activeTime: "6:50", idleTime: "0:18", satisfaction: 0,
  },
  {
    id: "e9", name: "أحمد الغامدي", avatar: "أغ", role: "qa",
    status: "available", channel: null, openConversations: 0, callsToday: 0,
    messagesHandled: 0, lastResponse: "—", sla: "warning", slaPercent: 72,
    avgResponseTime: "—", shift: "08:00 - 16:00", loginTime: "08:10",
    activeTime: "5:40", idleTime: "1:30", satisfaction: 0,
  },
];

export const vipCustomers: VIPCustomer[] = [
  {
    id: "vc1", name: "خالد سعد القحطاني", avatar: "خق", segment: "بلاتيني",
    totalSpent: 68500, lastOrder: "2026-02-18", lastContact: "اليوم",
    preferredChannel: "whatsapp", assignedAgent: "سارة الحربي",
    openIssues: 1, satisfaction: 4.8, tags: ["VIP", "عود", "هدايا"],
  },
  {
    id: "vc2", name: "أحمد محمد العلي", avatar: "أع", segment: "ذهبي",
    totalSpent: 42300, lastOrder: "2026-02-15", lastContact: "أمس",
    preferredChannel: "email", assignedAgent: "محمد العتيبي",
    openIssues: 0, satisfaction: 4.9, tags: ["VIP", "مجموعات"],
  },
  {
    id: "vc3", name: "لمى الغامدي", avatar: "لغ", segment: "بلاتيني",
    totalSpent: 55200, lastOrder: "2026-02-20", lastContact: "اليوم",
    preferredChannel: "whatsapp", assignedAgent: "ريم القحطاني",
    openIssues: 0, satisfaction: 5.0, tags: ["VIP", "هدايا", "حفلات"],
  },
  {
    id: "vc4", name: "نواف الشريف", avatar: "نش", segment: "ذهبي",
    totalSpent: 38900, lastOrder: "2026-02-10", lastContact: "منذ 3 أيام",
    preferredChannel: "phone", assignedAgent: "سارة الحربي",
    openIssues: 2, satisfaction: 4.2, tags: ["VIP", "بخور", "عود"],
  },
  {
    id: "vc5", name: "سلطان المالكي", avatar: "سم", segment: "بلاتيني",
    totalSpent: 91000, lastOrder: "2026-02-22", lastContact: "اليوم",
    preferredChannel: "phone", assignedAgent: "نورة الشمري",
    openIssues: 0, satisfaction: 4.7, tags: ["VIP", "تصدير", "بالجملة"],
  },
  {
    id: "vc6", name: "هيفاء العمري", avatar: "هع", segment: "فضي",
    totalSpent: 28700, lastOrder: "2026-01-28", lastContact: "منذ أسبوع",
    preferredChannel: "instagram", assignedAgent: "نورة الشمري",
    openIssues: 1, satisfaction: 4.5, tags: ["VIP", "عطور نسائية"],
  },
];

export const tasks: Task[] = [
  {
    id: "t1", title: "اتصال", customerName: "زبون A", customerId: "C-001",
    type: "call", reason: "سعر خاص", assignee: "أحمد",
    dueDate: "2026-02-23", dueTime: "16:00", status: "open",
    priority: "urgent", channel: "phone", vip: false,
    notes: "العميل يطلب سعر خاص على كمية كبيرة", createdAt: "2026-02-23 09:00",
  },
  {
    id: "t2", title: "متابعة", customerName: "زبون B", customerId: "C-002",
    type: "follow-up", reason: "شكوى توصيل", assignee: "علي",
    dueDate: "2026-02-22", dueTime: "14:00", status: "overdue",
    priority: "high", channel: "whatsapp", vip: false,
    notes: "العميل يشتكي من تأخر التوصيل", createdAt: "2026-02-22 10:00",
  },
  {
    id: "t3", title: "رد", customerName: "زبون VIP", customerId: "C-003",
    type: "reply", reason: "انتظار SAP", assignee: null,
    dueDate: "2026-02-23", dueTime: "12:00", status: "open",
    priority: "high", channel: "email", vip: true,
    notes: "بانتظار رد من فريق SAP", createdAt: "2026-02-23 08:00",
  },
  {
    id: "t4", title: "محادثة بدون رد", customerName: "خالد القحطاني", customerId: "C-003",
    type: "reply", reason: "استفسار عن منتج", assignee: null,
    dueDate: "2026-02-23", dueTime: "10:00", status: "open",
    priority: "urgent", channel: "whatsapp", vip: true,
    notes: "عميل VIP ينتظر رد منذ ساعة", createdAt: "2026-02-23 09:00",
  },
  {
    id: "t5", title: "تصعيد شكوى", customerName: "فاطمة السالم", customerId: "C-002",
    type: "escalation", reason: "منتج تالف", assignee: "سارة الحربي",
    dueDate: "2026-02-23", dueTime: "11:00", status: "in-progress",
    priority: "high", channel: "live-chat", vip: false,
    notes: "تم تصعيد الشكوى من الوكيل", createdAt: "2026-02-22 16:00",
  },
  {
    id: "t6", title: "متابعة عرض", customerName: "لمى الغامدي", customerId: "C-012",
    type: "follow-up", reason: "عرض هدايا VIP", assignee: "ريم القحطاني",
    dueDate: "2026-02-24", dueTime: "10:00", status: "open",
    priority: "normal", channel: "whatsapp", vip: true,
    notes: "تأكيد تفاصيل طلب هدايا لـ 10 أشخاص", createdAt: "2026-02-23 07:00",
  },
  {
    id: "t7", title: "رد على استفسار", customerName: "تركي المطيري", customerId: "C-009",
    type: "reply", reason: "استفسار أسعار", assignee: null,
    dueDate: "2026-02-23", dueTime: "14:00", status: "open",
    priority: "normal", channel: "x", vip: false,
    notes: "سؤال عن أسعار مجموعة الربيع", createdAt: "2026-02-23 08:30",
  },
  {
    id: "t8", title: "مهمة مكتملة", customerName: "نورة الشمري", customerId: "C-004",
    type: "task", reason: "تحديث بيانات", assignee: "محمد العتيبي",
    dueDate: "2026-02-22", dueTime: "16:00", status: "completed",
    priority: "low", channel: "email", vip: false,
    notes: "تم تحديث بيانات العميلة بنجاح", createdAt: "2026-02-22 09:00",
  },
];

export const complaints: Complaint[] = [
  {
    id: "c1", ticketNumber: "1023", customerName: "خالد القحطاني", customerId: "C-003",
    customerType: "VIP", type: "سوء تعامل", severity: "high", status: "escalated",
    assignee: "مدير", createdAt: "2026-02-22 09:00", updatedAt: "2026-02-23 08:00",
    relatedConversation: "CONV-445", relatedEmployee: "خالد الدوسري",
    description: "العميل يشتكي من أسلوب الموظف في المكالمة الأخيرة",
    steps: ["تم فتح التكت بواسطة المشرف", "تم ربطه بالمكالمة رقم 445", "تم تصعيده للمدير"],
  },
  {
    id: "c2", ticketNumber: "1027", customerName: "هند الزهراني", customerId: "C-010",
    customerType: "regular", type: "تأخير", severity: "medium", status: "open",
    assignee: "مشرف", createdAt: "2026-02-22 14:00", updatedAt: "2026-02-22 14:00",
    relatedConversation: "CONV-448", relatedEmployee: "محمد العتيبي",
    description: "تأخر في توصيل الطلب أكثر من أسبوع",
    steps: ["تم فتح التكت آلياً من النظام"],
  },
  {
    id: "c3", ticketNumber: "1030", customerName: "لمى الغامدي", customerId: "C-012",
    customerType: "VIP", type: "جودة منتج", severity: "high", status: "in-progress",
    assignee: "سارة الحربي", createdAt: "2026-02-23 07:30", updatedAt: "2026-02-23 09:00",
    relatedConversation: "CONV-452", relatedEmployee: "ريم القحطاني",
    description: "منتج عود ملكي لا يطابق المواصفات المعتادة",
    steps: ["تم فتح التكت", "تم ربطه بالمحادثة", "جاري المراجعة مع قسم الجودة"],
  },
  {
    id: "c4", ticketNumber: "1031", customerName: "سلطان المالكي", customerId: "C-015",
    customerType: "VIP", type: "فاتورة خاطئة", severity: "medium", status: "open",
    assignee: "محمد العتيبي", createdAt: "2026-02-23 08:00", updatedAt: "2026-02-23 08:00",
    description: "خطأ في مبلغ الفاتورة الأخيرة",
    steps: ["تم فتح التكت بواسطة الوكيل"],
  },
  {
    id: "c5", ticketNumber: "1025", customerName: "أحمد العلي", customerId: "C-001",
    customerType: "VIP", type: "استرجاع", severity: "low", status: "resolved",
    assignee: "نورة الشمري", createdAt: "2026-02-20 11:00", updatedAt: "2026-02-22 16:00",
    description: "طلب استرجاع منتج غير مفتوح",
    steps: ["تم فتح التكت", "تمت الموافقة على الاسترجاع", "تم إرسال المبلغ"],
  },
  {
    id: "c6", ticketNumber: "1032", customerName: "ريم الراشد", customerId: "C-008",
    customerType: "regular", type: "منتج ناقص", severity: "medium", status: "open",
    assignee: "خالد الدوسري", createdAt: "2026-02-23 09:30", updatedAt: "2026-02-23 09:30",
    relatedConversation: "CONV-455",
    description: "الطلب وصل ناقص قطعة واحدة",
    steps: ["تم فتح التكت بواسطة الوكيل"],
  },
];

export const attendanceRecords: AttendanceRecord[] = [
  {
    id: "at1", employeeName: "سارة الحربي", employeeId: "e1", role: "agent",
    loginTime: "07:55", logoutTime: null, hoursWorked: "7:05",
    activeTime: "6:45", idleTime: "0:22", messagesHandled: 45, callsHandled: 18,
    ip: "192.168.1.105", deviceType: "desktop", browser: "Chrome 121",
    location: "الرياض - المقر الرئيسي", isRemote: false, status: "present",
  },
  {
    id: "at2", employeeName: "محمد العتيبي", employeeId: "e2", role: "agent",
    loginTime: "08:02", logoutTime: null, hoursWorked: "6:58",
    activeTime: "6:30", idleTime: "0:35", messagesHandled: 62, callsHandled: 14,
    ip: "192.168.1.108", deviceType: "desktop", browser: "Chrome 121",
    location: "الرياض - المقر الرئيسي", isRemote: false, status: "present",
  },
  {
    id: "at3", employeeName: "نورة الشمري", employeeId: "e3", role: "agent",
    loginTime: "08:00", logoutTime: null, hoursWorked: "7:00",
    activeTime: "7:10", idleTime: "0:10", messagesHandled: 78, callsHandled: 21,
    ip: "192.168.1.112", deviceType: "laptop", browser: "Chrome 121",
    location: "الرياض - المقر الرئيسي", isRemote: false, status: "present",
  },
  {
    id: "at4", employeeName: "خالد الدوسري", employeeId: "e4", role: "agent",
    loginTime: "12:05", logoutTime: null, hoursWorked: "3:55",
    activeTime: "3:40", idleTime: "1:15", messagesHandled: 28, callsHandled: 11,
    ip: "10.0.0.45", deviceType: "laptop", browser: "Safari 17",
    location: "جدة - عن بعد", isRemote: true, status: "remote",
  },
  {
    id: "at5", employeeName: "ريم القحطاني", employeeId: "e5", role: "agent",
    loginTime: "11:58", logoutTime: null, hoursWorked: "5:02",
    activeTime: "5:20", idleTime: "0:28", messagesHandled: 53, callsHandled: 16,
    ip: "192.168.1.115", deviceType: "desktop", browser: "Edge 121",
    location: "الرياض - المقر الرئيسي", isRemote: false, status: "present",
  },
  {
    id: "at6", employeeName: "عبدالله المطيري", employeeId: "e6", role: "agent",
    loginTime: "—", logoutTime: null, hoursWorked: "0:00",
    activeTime: "0:00", idleTime: "0:00", messagesHandled: 0, callsHandled: 0,
    ip: "—", deviceType: "desktop", browser: "—",
    location: "—", isRemote: false, status: "absent",
  },
  {
    id: "at7", employeeName: "فهد الراشد", employeeId: "e7", role: "supervisor",
    loginTime: "07:50", logoutTime: null, hoursWorked: "7:10",
    activeTime: "7:00", idleTime: "0:15", messagesHandled: 15, callsHandled: 6,
    ip: "192.168.1.100", deviceType: "desktop", browser: "Chrome 121",
    location: "الرياض - المقر الرئيسي", isRemote: false, status: "present",
  },
  {
    id: "at8", employeeName: "منى السالم", employeeId: "e8", role: "qa",
    loginTime: "08:00", logoutTime: null, hoursWorked: "7:00",
    activeTime: "6:50", idleTime: "0:18", messagesHandled: 0, callsHandled: 0,
    ip: "192.168.1.120", deviceType: "desktop", browser: "Firefox 122",
    location: "الرياض - المقر الرئيسي", isRemote: false, status: "present",
  },
  {
    id: "at9", employeeName: "أحمد الغامدي", employeeId: "e9", role: "qa",
    loginTime: "08:10", logoutTime: null, hoursWorked: "6:50",
    activeTime: "5:40", idleTime: "1:30", messagesHandled: 0, callsHandled: 0,
    ip: "10.0.0.78", deviceType: "mobile", browser: "Chrome Mobile",
    location: "الدمام - عن بعد", isRemote: true, status: "remote",
  },
];

export const auditLog: AuditEntry[] = [
  { id: "au1", userId: "e2", userName: "محمد العتيبي", userRole: "agent", action: "status-change", target: "Available → Busy", details: "تعديل حالة", timestamp: "10:31", ip: "192.168.1.108" },
  { id: "au2", userId: "e7", userName: "فهد الراشد", userRole: "supervisor", action: "conversation-transfer", target: "VIP → أحمد", details: "نقل محادثة", timestamp: "10:35", ip: "192.168.1.100" },
  { id: "au3", userId: "e8", userName: "منى السالم", userRole: "qa", action: "evaluate", target: "Call #558", details: "تقييم مكالمة", timestamp: "11:02", ip: "192.168.1.120" },
  { id: "au4", userId: "e1", userName: "سارة الحربي", userRole: "agent", action: "login", target: "—", details: "تسجيل دخول", timestamp: "07:55", ip: "192.168.1.105" },
  { id: "au5", userId: "e9", userName: "أحمد الغامدي", userRole: "qa", action: "call-listen", target: "Call #556", details: "فتح مكالمة + استمع 15 ثانية + أغلق بدون تقييم", timestamp: "09:45", ip: "10.0.0.78" },
  { id: "au6", userId: "e7", userName: "فهد الراشد", userRole: "supervisor", action: "rule-edit", target: "SLA Rule #3", details: "تعديل قاعدة SLA من 5 دقائق إلى 3 دقائق", timestamp: "08:30", ip: "192.168.1.100" },
  { id: "au7", userId: "e3", userName: "نورة الشمري", userRole: "agent", action: "ticket-open", target: "Ticket #1030", details: "فتح تكت جديد - جودة منتج", timestamp: "07:35", ip: "192.168.1.112" },
  { id: "au8", userId: "e8", userName: "منى السالم", userRole: "qa", action: "message-review", target: "Conv #448", details: "مراجعة محادثة - 12 رسالة", timestamp: "10:15", ip: "192.168.1.120" },
  { id: "au9", userId: "e4", userName: "خالد الدوسري", userRole: "agent", action: "login", target: "—", details: "تسجيل دخول (عن بعد)", timestamp: "12:05", ip: "10.0.0.45" },
  { id: "au10", userId: "e7", userName: "فهد الراشد", userRole: "supervisor", action: "approval", target: "Refund #R-089", details: "موافقة على استرجاع مبلغ 950 ر.س", timestamp: "09:20", ip: "192.168.1.100" },
  { id: "au11", userId: "e5", userName: "ريم القحطاني", userRole: "agent", action: "recording-play", target: "Call #550", details: "تشغيل تسجيل مكالمة سابقة", timestamp: "11:30", ip: "192.168.1.115" },
  { id: "au12", userId: "e1", userName: "سارة الحربي", userRole: "agent", action: "status-change", target: "Available → Break", details: "تعديل حالة - استراحة", timestamp: "13:00", ip: "192.168.1.105" },
  { id: "au13", userId: "e9", userName: "أحمد الغامدي", userRole: "qa", action: "call-open", target: "Call #560", details: "فتح مكالمة للمراجعة", timestamp: "11:45", ip: "10.0.0.78" },
  { id: "au14", userId: "e8", userName: "منى السالم", userRole: "qa", action: "evaluate", target: "Conv #450", details: "تقييم محادثة - درجة 87/100", timestamp: "12:10", ip: "192.168.1.120" },
];

export const qaEvaluations: QAEvaluation[] = [
  {
    id: "qe1", auditorId: "e8", auditorName: "منى السالم",
    targetType: "call", targetId: "Call #558", targetAgent: "سارة الحربي",
    customerName: "خالد القحطاني", score: 92, maxScore: 100,
    criteria: [
      { name: "التحية والترحيب", score: 10, max: 10 },
      { name: "فهم الاحتياج", score: 9, max: 10 },
      { name: "جودة الحل", score: 18, max: 20 },
      { name: "اللباقة والأسلوب", score: 19, max: 20 },
      { name: "سرعة الاستجابة", score: 17, max: 20 },
      { name: "الإغلاق والمتابعة", score: 19, max: 20 },
    ],
    notes: "أداء ممتاز. العميل راضٍ تماماً. التحسين: سرعة أكثر في فتح ملف العميل.",
    listenDuration: 385, evaluatedAt: "2026-02-23 11:02", hasNotes: true, actuallyEvaluated: true,
  },
  {
    id: "qe2", auditorId: "e8", auditorName: "منى السالم",
    targetType: "conversation", targetId: "Conv #450", targetAgent: "محمد العتيبي",
    customerName: "أحمد العلي", score: 87, maxScore: 100,
    criteria: [
      { name: "التحية والترحيب", score: 9, max: 10 },
      { name: "فهم الاحتياج", score: 8, max: 10 },
      { name: "جودة الحل", score: 17, max: 20 },
      { name: "اللباقة والأسلوب", score: 18, max: 20 },
      { name: "سرعة الاستجابة", score: 16, max: 20 },
      { name: "الإغلاق والمتابعة", score: 19, max: 20 },
    ],
    notes: "جيد. لكن تأخر في الرد على السؤال الثالث. يحتاج تحسين في سرعة الاستجابة.",
    listenDuration: 0, evaluatedAt: "2026-02-23 12:10", hasNotes: true, actuallyEvaluated: true,
  },
  {
    id: "qe3", auditorId: "e9", auditorName: "أحمد الغامدي",
    targetType: "call", targetId: "Call #556", targetAgent: "نورة الشمري",
    customerName: "فاطمة السالم", score: 0, maxScore: 100,
    criteria: [], notes: "", listenDuration: 15,
    evaluatedAt: "2026-02-23 09:45", hasNotes: false, actuallyEvaluated: false,
  },
  {
    id: "qe4", auditorId: "e9", auditorName: "أحمد الغامدي",
    targetType: "call", targetId: "Call #560", targetAgent: "خالد الدوسري",
    customerName: "هند الزهراني", score: 75, maxScore: 100,
    criteria: [
      { name: "التحية والترحيب", score: 8, max: 10 },
      { name: "فهم الاحتياج", score: 7, max: 10 },
      { name: "جودة الحل", score: 14, max: 20 },
      { name: "اللباقة والأسلوب", score: 15, max: 20 },
      { name: "سرعة الاستجابة", score: 13, max: 20 },
      { name: "الإغلاق والمتابعة", score: 18, max: 20 },
    ],
    notes: "أداء متوسط. الموظف يحتاج تدريب على سياسة الاسترجاع.",
    listenDuration: 290, evaluatedAt: "2026-02-23 11:50", hasNotes: true, actuallyEvaluated: true,
  },
];

export const qaAuditors: QAAuditor[] = [
  {
    id: "e8", name: "منى السالم", avatar: "مس",
    evaluationsToday: 8, evaluationsWeek: 42, evaluationsMonth: 165,
    avgListenDuration: 320, totalListenTime: 2560,
    messagesReviewed: 45, conversationsReviewed: 12,
    loginTime: "08:00", logoutTime: null,
    activeTime: "6:50", idleTime: "0:18",
    withNotes: 7, withoutNotes: 1, openedAndLeft: 0,
    avgScore: 85.4, productivity: 94,
  },
  {
    id: "e9", name: "أحمد الغامدي", avatar: "أغ",
    evaluationsToday: 4, evaluationsWeek: 22, evaluationsMonth: 88,
    avgListenDuration: 180, totalListenTime: 720,
    messagesReviewed: 18, conversationsReviewed: 5,
    loginTime: "08:10", logoutTime: null,
    activeTime: "5:40", idleTime: "1:30",
    withNotes: 2, withoutNotes: 1, openedAndLeft: 1,
    avgScore: 72.3, productivity: 68,
  },
];

// ── Helpers ──────────────────────────────────────────

export const fmt = (n: number) => new Intl.NumberFormat("ar-SA").format(n);

export const statusColors: Record<EmployeeStatus, { bg: string; text: string; dot: string; label: string }> = {
  available: { bg: "bg-emerald-500/10", text: "text-emerald-500", dot: "bg-emerald-500", label: "متاح" },
  busy: { bg: "bg-red-500/10", text: "text-red-500", dot: "bg-red-500", label: "مشغول" },
  break: { bg: "bg-yellow-500/10", text: "text-yellow-500", dot: "bg-yellow-500", label: "استراحة" },
  offline: { bg: "bg-zinc-500/10", text: "text-zinc-500", dot: "bg-zinc-500", label: "غير متصل" },
  away: { bg: "bg-blue-500/10", text: "text-blue-500", dot: "bg-blue-500", label: "بعيد" },
};

export const channelLabels: Record<ChannelType, { label: string; color: string }> = {
  phone: { label: "هاتف", color: "text-blue-500" },
  whatsapp: { label: "واتساب", color: "text-emerald-500" },
  email: { label: "بريد", color: "text-violet-500" },
  instagram: { label: "إنستقرام", color: "text-pink-500" },
  x: { label: "X", color: "text-zinc-400" },
  "live-chat": { label: "محادثة مباشرة", color: "text-cyan-500" },
};

export const slaColors: Record<SLAStatus, { bg: string; text: string; label: string }> = {
  "on-track": { bg: "bg-emerald-500/10", text: "text-emerald-500", label: "ضمن المعيار" },
  warning: { bg: "bg-yellow-500/10", text: "text-yellow-500", label: "تحذير" },
  breached: { bg: "bg-red-500/10", text: "text-red-500", label: "مخالفة" },
};

export const roleLabels: Record<EmployeeRole, string> = {
  agent: "وكيل",
  supervisor: "مشرف",
  manager: "مدير",
  qa: "مدقق",
  "qa-supervisor": "مشرف مدققين",
};
