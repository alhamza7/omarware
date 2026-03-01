// ── Types ──────────────────────────────────────────

export interface Agent {
  id: string;
  name: string;
  avatar: string;
  status: "available" | "busy" | "break" | "offline";
  currentCall?: string;
  callsToday: number;
  avgDuration: string;
  satisfaction: number;
  ticketsResolved: number;
  shift: string;
}

export interface LiveCall {
  id: string;
  customerName: string;
  customerId: string;
  agentId: string;
  agentName: string;
  type: "inbound" | "outbound";
  duration: number; // seconds elapsed
  topic: string;
  vip: boolean;
}

export interface QueueItem {
  id: string;
  customerName: string;
  waitTime: number; // seconds
  topic: string;
  priority: "high" | "normal";
  vip: boolean;
}

export interface CallRecord {
  id: string;
  customerName: string;
  customerId: string;
  agentName: string;
  type: "inbound" | "outbound" | "missed";
  date: string;
  time: string;
  duration: string;
  status: "completed" | "missed" | "voicemail";
  topic: string;
  satisfaction?: number;
  hasRecording: boolean;
}

export interface Ticket {
  id: string;
  title: string;
  customerName: string;
  customerId: string;
  priority: "urgent" | "high" | "normal" | "low";
  status: "open" | "in-progress" | "resolved" | "closed";
  assignee: string;
  createdAt: string;
  updatedAt: string;
  category: string;
  messages: number;
}

export interface InboxMessage {
  id: string;
  customerName: string;
  customerId: string;
  channel: "whatsapp" | "email" | "instagram" | "x" | "live-chat";
  lastMessage: string;
  time: string;
  unread: boolean;
  unreadCount: number;
  vip: boolean;
  assignee?: string;
}

export interface Script {
  id: string;
  title: string;
  category: string;
  content: string;
  usageCount: number;
  tags: string[];
}

export interface FollowUp {
  id: string;
  customerName: string;
  customerId: string;
  agentName: string;
  scheduledDate: string;
  scheduledTime: string;
  reason: string;
  status: "pending" | "completed" | "overdue";
  notes: string;
  priority: "high" | "normal";
}

// ── Active Call Types ──────────────────────────────

export interface Invoice {
  id: string;
  date: string;
  dueDate: string;
  amount: number;
  paid: number;
  status: "paid" | "partial" | "unpaid" | "overdue";
  items: InvoiceItem[];
}

export interface InvoiceItem {
  name: string;
  qty: number;
  price: number;
  discount: number;
}

export interface PaymentRecord {
  id: string;
  date: string;
  amount: number;
  method: "cash" | "card" | "bank" | "qi";
  reference: string;
  invoiceId: string;
}

export interface CustomerFinance {
  currentBalance: number;
  creditLimit: number;
  usedCredit: number;
  availableCredit: number;
  totalCollected: number;
  totalOutstanding: number;
  collectionRate: number;
  debtAging: {
    current: number;
    days30: number;
    days60: number;
    days90: number;
    days120plus: number;
  };
}

export interface FrequentItem {
  id: string;
  name: string;
  category: string;
  lastOrdered: string;
  timesOrdered: number;
  avgQty: number;
  lastPrice: number;
  stock: number;
}

export interface GuidedStep {
  id: number;
  title: string;
  description: string;
  script: string;
  actions?: string[];
}

export interface CallSession {
  id: string;
  customerId: string;
  customerName: string;
  customerPhone: string;
  channel: "phone" | "whatsapp" | "sip";
  type: "inbound" | "outbound";
  vip: boolean;
  startTime: number;
  status: "ringing" | "active" | "on-hold" | "ended";
  tags: string[];
  outcome?: "resolved" | "callback" | "escalated" | "voicemail";
  notes: string;
  aiSummary?: AISummary;
}

export interface AISummary {
  agentName: string;
  duration: string;
  keyPoints: string[];
  situationStatus: "resolved" | "pending" | "escalated";
  qaScore: number;
  issuesFound: string[];
  invoiceMade?: { id: string; status: string };
  quotationMade?: { id: string; status: string };
  discountSuggestions: string[];
}

export interface CallCustomerProfile {
  id: string;
  name: string;
  phone: string;
  email: string;
  avatar: string;
  vip: boolean;
  segment: string;
  tags: string[];
  joinDate: string;
  address: string;
  favoriteFragrance?: string;
  lastOrder: {
    id: string;
    date: string;
    amount: number;
    items: InvoiceItem[];
    status: "delivered" | "shipped" | "processing";
  };
  finance: CustomerFinance;
  invoices: Invoice[];
  payments: PaymentRecord[];
  frequentItems: FrequentItem[];
}

// ── Active Call Mock Data ──────────────────────────

export const sampleCallCustomer: CallCustomerProfile = {
  id: "C-003",
  name: "خالد سعد القحطاني",
  phone: "+966 54 456 7890",
  email: "khalid.q@email.com",
  avatar: "خق",
  vip: true,
  segment: "بلاتيني",
  tags: ["VIP", "عود", "هدايا", "بلاتيني"],
  joinDate: "2023-11-10",
  address: "الدمام، حي الفيصلية، شارع الأمير محمد",
  favoriteFragrance: "مسك الليل",
  lastOrder: {
    id: "ORD-3045",
    date: "2026-02-18",
    amount: 2850,
    items: [
      { name: "عود ملكي 50مل", qty: 2, price: 750, discount: 0 },
      { name: "مسك الليل 100مل", qty: 1, price: 950, discount: 5 },
      { name: "بخور العربية", qty: 3, price: 150, discount: 0 },
    ],
    status: "delivered",
  },
  finance: {
    currentBalance: 4250,
    creditLimit: 15000,
    usedCredit: 10750,
    availableCredit: 4250,
    totalCollected: 68500,
    totalOutstanding: 4250,
    collectionRate: 94.2,
    debtAging: {
      current: 2850,
      days30: 900,
      days60: 350,
      days90: 150,
      days120plus: 0,
    },
  },
  invoices: [
    {
      id: "INV-2024-089",
      date: "2026-02-18",
      dueDate: "2026-03-18",
      amount: 2850,
      paid: 0,
      status: "unpaid",
      items: [
        { name: "عود ملكي 50مل", qty: 2, price: 750, discount: 0 },
        { name: "مسك الليل 100مل", qty: 1, price: 950, discount: 5 },
        { name: "بخور العربية", qty: 3, price: 150, discount: 0 },
      ],
    },
    {
      id: "INV-2024-075",
      date: "2026-01-22",
      dueDate: "2026-02-22",
      amount: 900,
      paid: 0,
      status: "overdue",
      items: [
        { name: "روز باريس 75مل", qty: 1, price: 650, discount: 0 },
        { name: "عينات فاخرة (5)", qty: 1, price: 250, discount: 0 },
      ],
    },
    {
      id: "INV-2024-060",
      date: "2025-12-15",
      dueDate: "2026-01-15",
      amount: 500,
      paid: 150,
      status: "partial",
      items: [
        { name: "دهن عود قديم 12مل", qty: 1, price: 500, discount: 0 },
      ],
    },
    {
      id: "INV-2024-045",
      date: "2025-11-10",
      dueDate: "2025-12-10",
      amount: 1200,
      paid: 1200,
      status: "paid",
      items: [
        { name: "مجموعة هدايا VIP", qty: 1, price: 1200, discount: 10 },
      ],
    },
  ],
  payments: [
    { id: "PAY-001", date: "2026-02-15", amount: 1200, method: "card", reference: "VISA-****4521", invoiceId: "INV-2024-045" },
    { id: "PAY-002", date: "2026-01-20", amount: 150, method: "cash", reference: "إيصال #3210", invoiceId: "INV-2024-060" },
    { id: "PAY-003", date: "2025-12-01", amount: 3500, method: "bank", reference: "حوالة #78432", invoiceId: "INV-2024-040" },
    { id: "PAY-004", date: "2025-11-15", amount: 2200, method: "qi", reference: "QI-TXN-99812", invoiceId: "INV-2024-035" },
  ],
  frequentItems: [
    { id: "fi1", name: "عود ملكي 50مل", category: "عطور", lastOrdered: "2026-02-18", timesOrdered: 8, avgQty: 2, lastPrice: 750, stock: 15 },
    { id: "fi2", name: "مسك الليل 100مل", category: "عطور", lastOrdered: "2026-02-18", timesOrdered: 5, avgQty: 1, lastPrice: 950, stock: 10 },
    { id: "fi3", name: "روز باريس 75مل", category: "عطور", lastOrdered: "2026-01-22", timesOrdered: 4, avgQty: 1, lastPrice: 650, stock: 5 },
    { id: "fi4", name: "بخور العربية", category: "عطور", lastOrdered: "2026-02-18", timesOrdered: 12, avgQty: 3, lastPrice: 150, stock: 20 },
    { id: "fi5", name: "دهن عود قديم 12مل", category: "عطور", lastOrdered: "2025-12-15", timesOrdered: 3, avgQty: 1, lastPrice: 500, stock: 8 },
    { id: "fi6", name: "مجموعة هدايا VIP", category: "عطور", lastOrdered: "2025-11-10", timesOrdered: 2, avgQty: 1, lastPrice: 1200, stock: 3 },
    { id: "fi7", name: "قارورة كريستال 100مل", category: "زجاجيات", lastOrdered: "2026-02-10", timesOrdered: 6, avgQty: 10, lastPrice: 45, stock: 12 },
    { id: "fi8", name: "زجاجة عطر ذهبية 50مل", category: "زجاجيات", lastOrdered: "2026-01-28", timesOrdered: 4, avgQty: 15, lastPrice: 35, stock: 7 },
    { id: "fi9", name: "عبوة رذاذ فاخرة 30مل", category: "زجاجيات", lastOrdered: "2026-02-05", timesOrdered: 8, avgQty: 20, lastPrice: 22, stock: 18 },
    { id: "fi10", name: "قارورة مخروطية 75مل", category: "زجاجيات", lastOrdered: "2025-12-20", timesOrdered: 3, avgQty: 8, lastPrice: 55, stock: 4 },
    { id: "fi11", name: "كحول إيثيلي نقي 96%", category: "كحول", lastOrdered: "2026-02-15", timesOrdered: 10, avgQty: 5, lastPrice: 120, stock: 25 },
    { id: "fi12", name: "كحول أيزوبروبيل 99%", category: "كحول", lastOrdered: "2026-01-30", timesOrdered: 7, avgQty: 3, lastPrice: 95, stock: 15 },
    { id: "fi13", name: "ديبروبيلين غلايكول DPG", category: "كحول", lastOrdered: "2026-02-08", timesOrdered: 5, avgQty: 2, lastPrice: 180, stock: 10 },
    { id: "fi14", name: "كحول معطّر خاص", category: "كحول", lastOrdered: "2025-12-25", timesOrdered: 3, avgQty: 1, lastPrice: 250, stock: 6 },
  ],
};

export const guidedWorkflow: GuidedStep[] = [
  {
    id: 1,
    title: "التحية والترحيب",
    description: "رحّب بالعميل واستخدم اسمه",
    script: "السلام عليكم [خالد]، سعداء بتواصلك مع نور النبراس. بصفتك من عملائنا المميزين، كيف يمكنني خدمتك اليوم؟",
    actions: ["تحقق من ملف العميل", "لاحظ حالة VIP"],
  },
  {
    id: 2,
    title: "فهم الاحتياج",
    description: "استمع بتركيز وحدد الطلب",
    script: "بالتأكيد [خالد]، دعني أفهم طلبك بالتفصيل. [أعد صياغة ما قاله العميل]. هل فهمتك صح؟",
    actions: ["سجّل الموضوع", "حدد نوع اللب"],
  },
  {
    id: 3,
    title: "الحل والعرض",
    description: "قدّم الحل أو العرض المناسب",
    script: "بناءً على طلبك، أقترح [الحل]. كما أود أن أُطلعك على [عرض/منتج مناسب].",
    actions: ["عرض المنتجات المقترحة", "تحقق من المخزون", "اذكر العروض الحالية"],
  },
  {
    id: 4,
    title: "إتمام وتأكيد",
    description: "أكّد مع العميل واختم المكالمة",
    script: "تم معالجة طلبك [التفاصيل]. هل تحتاج أي شيء آخر؟ شكراً لثقتك بنور النبراس، نتمنى لك يوماً سعيداً.",
    actions: ["أكّد التفاصيل", "سجّل الملاحظات", "حدد المتابعة"],
  },
];

// ── Mock Data ──────────────────────────────────────

export const agents: Agent[] = [
  {
    id: "a1",
    name: "سارة الحربي",
    avatar: "سح",
    status: "busy",
    currentCall: "أحمد العلي",
    callsToday: 18,
    avgDuration: "4:32",
    satisfaction: 4.8,
    ticketsResolved: 12,
    shift: "08:00 - 16:00",
  },
  {
    id: "a2",
    name: "محمد العتيبي",
    avatar: "مع",
    status: "available",
    callsToday: 14,
    avgDuration: "5:10",
    satisfaction: 4.6,
    ticketsResolved: 9,
    shift: "08:00 - 16:00",
  },
  {
    id: "a3",
    name: "نورة الشمري",
    avatar: "نش",
    status: "busy",
    currentCall: "فاطمة السالم",
    callsToday: 21,
    avgDuration: "3:45",
    satisfaction: 4.9,
    ticketsResolved: 16,
    shift: "08:00 - 16:00",
  },
  {
    id: "a4",
    name: "خالد الدوسري",
    avatar: "خد",
    status: "break",
    callsToday: 11,
    avgDuration: "6:20",
    satisfaction: 4.3,
    ticketsResolved: 7,
    shift: "12:00 - 20:00",
  },
  {
    id: "a5",
    name: "ريم القحطاني",
    avatar: "رق",
    status: "available",
    callsToday: 16,
    avgDuration: "4:55",
    satisfaction: 4.7,
    ticketsResolved: 11,
    shift: "12:00 - 20:00",
  },
  {
    id: "a6",
    name: "عبدالله المطيري",
    avatar: "عم",
    status: "offline",
    callsToday: 0,
    avgDuration: "0:00",
    satisfaction: 4.5,
    ticketsResolved: 0,
    shift: "16:00 - 00:00",
  },
];

export const liveCalls: LiveCall[] = [
  {
    id: "lc1",
    customerName: "أحمد محمد العلي",
    customerId: "C-001",
    agentId: "a1",
    agentName: "سارة الحربي",
    type: "inbound",
    duration: 187,
    topic: "استفسار عن مجموعة الربيع الجديدة",
    vip: true,
  },
  {
    id: "lc2",
    customerName: "فاطمة عبدالله السالم",
    customerId: "C-002",
    agentId: "a3",
    agentName: "نورة الشمري",
    type: "inbound",
    duration: 94,
    topic: "متابعة طلب استبدال",
    vip: false,
  },
];

export const callQueue: QueueItem[] = [
  { id: "q1", customerName: "خالد القحطاني", waitTime: 45, topic: "شكوى جودة منتج", priority: "high", vip: true },
  { id: "q2", customerName: "هند الزهراني", waitTime: 120, topic: "استفسار عن توصيل", priority: "normal", vip: false },
  { id: "q3", customerName: "ماجد السبيعي", waitTime: 30, topic: "طلب عطر مخصص", priority: "normal", vip: false },
];

export const callRecords: CallRecord[] = [
  {
    id: "cr1",
    customerName: "أحمد محمد العلي",
    customerId: "C-001",
    agentName: "سارة الحربي",
    type: "inbound",
    date: "2026-02-22",
    time: "09:15",
    duration: "6:32",
    status: "completed",
    topic: "استفسار عن عود ملكي",
    satisfaction: 5,
    hasRecording: true,
  },
  {
    id: "cr2",
    customerName: "فاطمة السالم",
    customerId: "C-002",
    agentName: "نورة الشمري",
    type: "inbound",
    date: "2026-02-22",
    time: "09:45",
    duration: "4:18",
    status: "completed",
    topic: "استبدال منتج",
    satisfaction: 4,
    hasRecording: true,
  },
  {
    id: "cr3",
    customerName: "خالد القحطاني",
    customerId: "C-003",
    agentName: "محمد العتيبي",
    type: "outbound",
    date: "2026-02-22",
    time: "10:00",
    duration: "3:45",
    status: "completed",
    topic: "متابعة طلب VIP",
    satisfaction: 5,
    hasRecording: true,
  },
  {
    id: "cr4",
    customerName: "نورة الشمري",
    customerId: "C-004",
    agentName: "سارة الحربي",
    type: "inbound",
    date: "2026-02-22",
    time: "10:30",
    duration: "0:00",
    status: "missed",
    topic: "غير محدد",
    hasRecording: false,
  },
  {
    id: "cr5",
    customerName: "عبدالرحمن الدوسري",
    customerId: "C-005",
    agentName: "ريم القحطاني",
    type: "inbound",
    date: "2026-02-22",
    time: "11:00",
    duration: "2:15",
    status: "voicemail",
    topic: "استفسار عام",
    hasRecording: true,
  },
  {
    id: "cr6",
    customerName: "سارة الحربي (عميلة)",
    customerId: "C-006",
    agentName: "محمد العتيبي",
    type: "outbound",
    date: "2026-02-21",
    time: "14:20",
    duration: "8:10",
    status: "completed",
    topic: "عرض ترويجي خاص",
    satisfaction: 4,
    hasRecording: true,
  },
  {
    id: "cr7",
    customerName: "ريم الراشد",
    customerId: "C-008",
    agentName: "نورة الشمري",
    type: "outbound",
    date: "2026-02-21",
    time: "15:00",
    duration: "5:40",
    status: "completed",
    topic: "إعادة تنشيط عميل",
    satisfaction: 3,
    hasRecording: true,
  },
  {
    id: "cr8",
    customerName: "تركي المطيري",
    customerId: "C-009",
    agentName: "خالد الدوسري",
    type: "inbound",
    date: "2026-02-21",
    time: "16:30",
    duration: "3:20",
    status: "completed",
    topic: "استفسار عن أسعار",
    satisfaction: 5,
    hasRecording: true,
  },
  {
    id: "cr9",
    customerName: "لمى الغامدي",
    customerId: "C-012",
    agentName: "سارة الحربي",
    type: "inbound",
    date: "2026-02-20",
    time: "10:45",
    duration: "12:05",
    status: "completed",
    topic: "طلب مجموعة هدايا VIP",
    satisfaction: 5,
    hasRecording: true,
  },
  {
    id: "cr10",
    customerName: "هند الزهراني",
    customerId: "C-010",
    agentName: "ريم القحطاني",
    type: "inbound",
    date: "2026-02-20",
    time: "13:10",
    duration: "0:00",
    status: "missed",
    topic: "غير محدد",
    hasRecording: false,
  },
];

export const tickets: Ticket[] = [
  {
    id: "T-001",
    title: "شكوى جودة عطر عود ملكي - دفعة فبراير",
    customerName: "خالد القحطاني",
    customerId: "C-003",
    priority: "urgent",
    status: "open",
    assignee: "سارة الحربي",
    createdAt: "2026-02-22 09:00",
    updatedAt: "2026-02-22 09:30",
    category: "جودة",
    messages: 3,
  },
  {
    id: "T-002",
    title: "طلب استبدال منتج تالف",
    customerName: "فاطمة السالم",
    customerId: "C-002",
    priority: "high",
    status: "in-progress",
    assignee: "نورة الشمري",
    createdAt: "2026-02-21 14:30",
    updatedAt: "2026-02-22 08:15",
    category: "استبدال",
    messages: 5,
  },
  {
    id: "T-003",
    title: "تأخر في توصيل الطلب #3045",
    customerName: "هند الزهراني",
    customerId: "C-010",
    priority: "normal",
    status: "in-progress",
    assignee: "محمد العتيبي",
    createdAt: "2026-02-20 11:00",
    updatedAt: "2026-02-21 16:45",
    category: "توصيل",
    messages: 4,
  },
  {
    id: "T-004",
    title: "طلب فاتورة ضريبية",
    customerName: "أحمد العلي",
    customerId: "C-001",
    priority: "low",
    status: "resolved",
    assignee: "ريم القحطاني",
    createdAt: "2026-02-19 10:00",
    updatedAt: "2026-02-20 09:30",
    category: "فواتير",
    messages: 2,
  },
  {
    id: "T-005",
    title: "اقتراح إضافة خدمة التغليف الفاخر",
    customerName: "لمى الغامدي",
    customerId: "C-012",
    priority: "normal",
    status: "closed",
    assignee: "سارة الحربي",
    createdAt: "2026-02-18 15:00",
    updatedAt: "2026-02-19 12:00",
    category: "اقتراحات",
    messages: 6,
  },
  {
    id: "T-006",
    title: "مشكلة في الدفع الإلكتروني",
    customerName: "ماجد السبيعي",
    customerId: "C-011",
    priority: "high",
    status: "open",
    assignee: "خالد الدوسري",
    createdAt: "2026-02-22 08:45",
    updatedAt: "2026-02-22 08:45",
    category: "مدفوعات",
    messages: 1,
  },
];

export const inboxMessages: InboxMessage[] = [
  {
    id: "m1",
    customerName: "خالد القحطاني",
    customerId: "C-003",
    channel: "whatsapp",
    lastMessage: "متى يكون عندكم عرض على دهن العود؟",
    time: "منذ 5 دقائق",
    unread: true,
    unreadCount: 3,
    vip: true,
    assignee: "سارة الحربي",
  },
  {
    id: "m2",
    customerName: "نورة الشمري",
    customerId: "C-004",
    channel: "instagram",
    lastMessage: "حبيت العطر الجديد! هل فيه عينات للتجربة؟",
    time: "منذ 15 دقيقة",
    unread: true,
    unreadCount: 1,
    vip: false,
  },
  {
    id: "m3",
    customerName: "أحمد العلي",
    customerId: "C-001",
    channel: "email",
    lastMessage: "أرجو إرسال قائمة الأسعار المحدّثة لمجموعة 2026",
    time: "منذ 30 دقيقة",
    unread: true,
    unreadCount: 1,
    vip: true,
    assignee: "محمد العتيبي",
  },
  {
    id: "m4",
    customerName: "سارة الحربي (عميلة)",
    customerId: "C-006",
    channel: "live-chat",
    lastMessage: "شكراً على المساعدة، الطلب وصل بخير",
    time: "منذ ساعة",
    unread: false,
    unreadCount: 0,
    vip: false,
    assignee: "نورة الشمري",
  },
  {
    id: "m5",
    customerName: "لمى الغامدي",
    customerId: "C-012",
    channel: "whatsapp",
    lastMessage: "أبغى أطلب مجموعة هدايا لـ 10 أشخاص",
    time: "منذ ساعتين",
    unread: true,
    unreadCount: 2,
    vip: true,
    assignee: "ريم القحطاني",
  },
  {
    id: "m6",
    customerName: "تركي المطيري",
    customerId: "C-009",
    channel: "x",
    lastMessage: "وش أفضل عطر رجالي عندكم؟",
    time: "منذ 3 ساعات",
    unread: false,
    unreadCount: 0,
    vip: false,
  },
  {
    id: "m7",
    customerName: "ريم الراشد",
    customerId: "C-008",
    channel: "email",
    lastMessage: "هل يوجد خصم للطلبات الكبيرة؟",
    time: "أمس",
    unread: false,
    unreadCount: 0,
    vip: false,
  },
  {
    id: "m8",
    customerName: "فاطمة السالم",
    customerId: "C-002",
    channel: "live-chat",
    lastMessage: "متى يوصل الطلب البديل؟",
    time: "أمس",
    unread: false,
    unreadCount: 0,
    vip: false,
    assignee: "نورة الشمري",
  },
];

export const scripts: Script[] = [
  {
    id: "s1",
    title: "تحية العميل الافتتاحية",
    category: "عام",
    content: "السلام عليكم ورحمة الله وبركاته، معك [اسم الوكيل] من نور النبراس للعطور الفاخرة. كيف يمكنني مساعدتك اليوم؟",
    usageCount: 342,
    tags: ["ترحيب", "افتتاح"],
  },
  {
    id: "s2",
    title: "تحية عميل VIP",
    category: "VIP",
    content: "السلام عليكم [اسم العميل]، سعداء بتواصلك معنا. بصفتك من عملائنا المميزين، نحرص على تقديم أفضل خدمة لك. كيف أقدر أساعدك؟",
    usageCount: 156,
    tags: ["VIP", "ترحيب"],
  },
  {
    id: "s3",
    title: "التعامل مع شكوى جودة",
    category: "شاوى",
    content: "أعتذر جداً عن هذه التجربة، [اسم العميل]. جودة منتجاتنا من أهم أولوياتنا. سأقوم بتسجيل ملاحظتك فوراً وإحالتها لقسم الجودة. هل تفضل استبدال المنتج أو استرداد المبلغ؟ سنتابع معك خلال 24 ساعة.",
    usageCount: 89,
    tags: ["شكوى", "جودة", "استبدال"],
  },
  {
    id: "s4",
    title: "الاستفسار عن حالة الطلب",
    category: "طلبات",
    content: "بكل تأكيد، دعني أتحقق من حالة طلبك. رقم الطلب [رقم الطلب]. لحظة من فضلك... طلبك حالياً [الحالة] ومن المتوقع وصوله [التاريخ]. هل تحتاج أي شيء آخر؟",
    usageCount: 267,
    tags: ["طلبات", "توصيل", "تتبع"],
  },
  {
    id: "s5",
    title: "عرض ترويجي - البيع الإضافي",
    category: "مبيعات",
    content: "بمناسبة اهتمامك بـ [المنتج]، لدينا عرض خاص على مجموعة [المجموعة] مع خصم [النسبة]%. كما يمكنك إضافة [منتج مكمل] بسعر مميز. هل تودّ معرفة التفاصيل؟",
    usageCount: 134,
    tags: ["مبيعات", "عروض", "upsell"],
  },
  {
    id: "s6",
    title: "سياسة الاستبدال والاسترجاع",
    category: "سياسات",
    content: "سياسة الاستبدال لدينا تسمح بالاستبدال خلال 14 يوم من الشراء بشرط عدم فتح العبوة. الاسترجاع متاح خلال 7 أيام للمنتجات غير المفتوحة. المنتجات المخصصة غير قابلة للاسترجاع. هل تودّ بدء طلب استبدال؟",
    usageCount: 198,
    tags: ["استبدال", "استرجاع", "سياسات"],
  },
  {
    id: "s7",
    title: "إغلاق المكالمة",
    category: "عام",
    content: "شكراً لتواصلك مع نور النبراس، [اسم العميل]. هل هناك أي شيء آخر يمكنني مساعدتك فيه؟ ... نتمنى لك يوماً سعيداً ونسعد بخدمتك دائماً.",
    usageCount: 312,
    tags: ["إغلاق", "ختام"],
  },
  {
    id: "s8",
    title: "تحويل لقسم متخصص",
    category: "عام",
    content: "أقدّر صبرك، [اسم العميل]. هذا الموضوع يتطلب متخصص من قسم [القسم]. سأحولك الآن للزميل المختص. لن تحتاج لإعادة شرح المشكلة، فقد قمت بتسجيل كل التفاصيل. لحظة من فضلك.",
    usageCount: 76,
    tags: ["تحويل", "قسم"],
  },
];

export const followUps: FollowUp[] = [
  {
    id: "fu1",
    customerName: "خالد القحطاني",
    customerId: "C-003",
    agentName: "سارة الحربي",
    scheduledDate: "2026-02-22",
    scheduledTime: "14:00",
    reason: "متابعة شكوى جودة المنتج",
    status: "pending",
    notes: "العميل VIP - أولوية قصوى. تم إرسال منتج بديل.",
    priority: "high",
  },
  {
    id: "fu2",
    customerName: "فاطمة السالم",
    customerId: "C-002",
    agentName: "نورة الشمري",
    scheduledDate: "2026-02-22",
    scheduledTime: "15:30",
    reason: "تأكيد وصول المنتج البديل",
    status: "pending",
    notes: "م شحن المنتج البديل أمس.",
    priority: "normal",
  },
  {
    id: "fu3",
    customerName: "ريم الراشد",
    customerId: "C-008",
    agentName: "ريم القحطاني",
    scheduledDate: "2026-02-23",
    scheduledTime: "10:00",
    reason: "إعادة تنشيط عميلة غير نشطة",
    status: "pending",
    notes: "عرض خصم 20% لتشجيع العودة.",
    priority: "normal",
  },
  {
    id: "fu4",
    customerName: "لمى الغامدي",
    customerId: "C-012",
    agentName: "سارة الحربي",
    scheduledDate: "2026-02-21",
    scheduledTime: "11:00",
    reason: "تأكيد تفاصيل طلب هدايا VIP",
    status: "completed",
    notes: "تم تأكيد الطلب وبدأ التجهيز.",
    priority: "high",
  },
  {
    id: "fu5",
    customerName: "هند الزهراني",
    customerId: "C-010",
    agentName: "محمد العتيبي",
    scheduledDate: "2026-02-21",
    scheduledTime: "16:00",
    reason: "متابعة تأخر التوصيل",
    status: "overdue",
    notes: "لم يتم التواصل بعد - العميلة لم ترد.",
    priority: "high",
  },
  {
    id: "fu6",
    customerName: "أحمد العلي",
    customerId: "C-001",
    agentName: "محمد العتيبي",
    scheduledDate: "2026-02-24",
    scheduledTime: "09:00",
    reason: "عرض مجموعة الربيع الحصرية",
    status: "pending",
    notes: "عميل VIP مهتم بالمجموعات الجديدة.",
    priority: "normal",
  },
];