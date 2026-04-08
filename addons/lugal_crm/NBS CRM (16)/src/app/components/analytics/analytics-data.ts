// ═══════════════════════════════════════════════════════════
// Mock Analytics Data - Noor Al-Nebras Perfume Store
// Ready to be replaced with Supabase queries
// ═══════════════════════════════════════════════════════════

// ─── Types ───────────────────────────────────────────────
export type TimePeriod = "day" | "week" | "month" | "year" | "overall";

export interface ChannelStat {
  channel: string;
  channelAr: string;
  messages: number;
  calls: number;
  chats: number;
  tickets: number;
  leads: number;
  conversionRate: number;
  color: string;
}

export interface ChannelTimeSeries {
  period: string;
  whatsapp: number;
  instagram: number;
  x: number;
  snapchat: number;
  tiktok: number;
  telegram: number;
  website: number;
  email: number;
  store: number;
}

export interface EmployeeStat {
  id: string;
  name: string;
  avatar: string;
  branch: string;
  department: string;
  role: string;
  totalMessages: number;
  answeredMessages: number;
  totalCalls: number;
  answeredCalls: number;
  frtMinutes: number; // First Response Time
  ttrHours: number;   // Time to Resolve
  lateMessages: number;
  lateCalls: number;
  conversionsOrders: number;
  conversionsQuotations: number;
  satisfactionScore: number;
  kpiScore: number;
  kpiTier: "star" | "excellent" | "good" | "developing" | "needs-support";
  availabilityRate: number;
  aiAssisted: number;
}

export interface TicketStat {
  status: string;
  statusAr: string;
  count: number;
  color: string;
  trend: number;
}

export interface BranchStat {
  id: string;
  name: string;
  city: string;
  customerCount: number;
  revenue: number;
  ticketsOpen: number;
  ticketsClosed: number;
  ticketsStale: number;
  avgFrt: number;
  avgTtr: number;
  satisfaction: number;
  topAgent: string;
  employeeCount: number;
}

export interface VipStat {
  totalVip: number;
  totalInteractions: number;
  avgResponseTime: number;
  avgResolutionTime: number;
  satisfaction: number;
  retentionRate: number;
  revenueShare: number;
  escalations: number;
  dedicatedAgents: number;
}

export interface AiHumanStat {
  category: string;
  categoryAr: string;
  ai: number;
  human: number;
}

// ─── Channel Data ────────────────────────────────────────
export const channelStats: ChannelStat[] = [
  { channel: "whatsapp", channelAr: "واتساب", messages: 12480, calls: 890, chats: 8340, tickets: 1240, leads: 620, conversionRate: 34.2, color: "#25D366" },
  { channel: "instagram", channelAr: "إنستغرام", messages: 8920, calls: 0, chats: 6100, tickets: 820, leads: 450, conversionRate: 28.5, color: "#E1306C" },
  { channel: "x", channelAr: "X (تويتر)", messages: 3240, calls: 0, chats: 2100, tickets: 340, leads: 180, conversionRate: 15.8, color: "#1DA1F2" },
  { channel: "snapchat", channelAr: "سناب شات", messages: 4560, calls: 0, chats: 3200, tickets: 280, leads: 320, conversionRate: 22.1, color: "#FFFC00" },
  { channel: "tiktok", channelAr: "تيك توك", messages: 6780, calls: 0, chats: 4500, tickets: 180, leads: 540, conversionRate: 31.4, color: "#000000" },
  { channel: "telegram", channelAr: "تيليجرام", messages: 2100, calls: 0, chats: 1800, tickets: 120, leads: 90, conversionRate: 12.5, color: "#0088CC" },
  { channel: "website", channelAr: "الموقع", messages: 5400, calls: 320, chats: 3900, tickets: 620, leads: 380, conversionRate: 26.3, color: "#06B6D4" },
  { channel: "email", channelAr: "البريد", messages: 3800, calls: 0, chats: 0, tickets: 890, leads: 210, conversionRate: 18.7, color: "#EA4335" },
  { channel: "store", channelAr: "المتجر", messages: 0, calls: 1200, chats: 0, tickets: 340, leads: 890, conversionRate: 52.3, color: "#8B5CF6" },
];

export const channelTimeSeries: Record<TimePeriod, ChannelTimeSeries[]> = {
  day: [
    { period: "00:00", whatsapp: 12, instagram: 8, x: 2, snapchat: 3, tiktok: 5, telegram: 1, website: 4, email: 2, store: 0 },
    { period: "04:00", whatsapp: 5, instagram: 3, x: 1, snapchat: 1, tiktok: 2, telegram: 0, website: 1, email: 1, store: 0 },
    { period: "08:00", whatsapp: 45, instagram: 22, x: 8, snapchat: 10, tiktok: 15, telegram: 5, website: 18, email: 12, store: 35 },
    { period: "12:00", whatsapp: 78, instagram: 45, x: 15, snapchat: 20, tiktok: 32, telegram: 8, website: 28, email: 18, store: 42 },
    { period: "16:00", whatsapp: 92, instagram: 56, x: 18, snapchat: 25, tiktok: 40, telegram: 12, website: 35, email: 22, store: 58 },
    { period: "20:00", whatsapp: 65, instagram: 48, x: 12, snapchat: 18, tiktok: 28, telegram: 6, website: 15, email: 8, store: 20 },
  ],
  week: [
    { period: "الأحد", whatsapp: 420, instagram: 280, x: 85, snapchat: 120, tiktok: 180, telegram: 55, website: 140, email: 95, store: 210 },
    { period: "الإثنين", whatsapp: 380, instagram: 250, x: 78, snapchat: 110, tiktok: 165, telegram: 48, website: 130, email: 88, store: 195 },
    { period: "الثلاثاء", whatsapp: 410, instagram: 290, x: 92, snapchat: 128, tiktok: 195, telegram: 52, website: 145, email: 102, store: 220 },
    { period: "الأربعاء", whatsapp: 450, instagram: 310, x: 98, snapchat: 135, tiktok: 210, telegram: 58, website: 155, email: 108, store: 235 },
    { period: "الخميس", whatsapp: 520, instagram: 380, x: 105, snapchat: 160, tiktok: 245, telegram: 65, website: 180, email: 120, store: 280 },
    { period: "الجمعة", whatsapp: 350, instagram: 220, x: 65, snapchat: 95, tiktok: 140, telegram: 38, website: 110, email: 72, store: 150 },
    { period: "السبت", whatsapp: 480, instagram: 350, x: 95, snapchat: 145, tiktok: 225, telegram: 60, website: 165, email: 112, store: 260 },
  ],
  month: [
    { period: "الأسبوع 1", whatsapp: 2800, instagram: 1900, x: 680, snapchat: 920, tiktok: 1400, telegram: 420, website: 1100, email: 780, store: 1600 },
    { period: "الأسبوع 2", whatsapp: 3100, instagram: 2200, x: 750, snapchat: 1050, tiktok: 1620, telegram: 480, website: 1250, email: 860, store: 1800 },
    { period: "الأسبوع 3", whatsapp: 3400, instagram: 2400, x: 820, snapchat: 1150, tiktok: 1780, telegram: 540, website: 1380, email: 940, store: 1950 },
    { period: "الأسبوع 4", whatsapp: 3180, instagram: 2420, x: 790, snapchat: 1080, tiktok: 1680, telegram: 510, website: 1320, email: 900, store: 1850 },
  ],
  year: [
    { period: "يناير", whatsapp: 10200, instagram: 7100, x: 2600, snapchat: 3500, tiktok: 5400, telegram: 1650, website: 4300, email: 3100, store: 6200 },
    { period: "فبراير", whatsapp: 9800, instagram: 6800, x: 2450, snapchat: 3300, tiktok: 5100, telegram: 1550, website: 4100, email: 2900, store: 5800 },
    { period: "مارس", whatsapp: 11500, instagram: 8200, x: 2900, snapchat: 3900, tiktok: 6200, telegram: 1800, website: 4800, email: 3400, store: 7100 },
    { period: "أبريل", whatsapp: 10800, instagram: 7600, x: 2700, snapchat: 3700, tiktok: 5800, telegram: 1700, website: 4500, email: 3200, store: 6600 },
    { period: "مايو", whatsapp: 11200, instagram: 7900, x: 2800, snapchat: 3800, tiktok: 6000, telegram: 1750, website: 4650, email: 3300, store: 6900 },
    { period: "يونيو", whatsapp: 12000, instagram: 8500, x: 3000, snapchat: 4100, tiktok: 6500, telegram: 1900, website: 5000, email: 3500, store: 7400 },
    { period: "يوليو", whatsapp: 11800, instagram: 8300, x: 2950, snapchat: 4000, tiktok: 6400, telegram: 1850, website: 4900, email: 3450, store: 7200 },
    { period: "أغسطس", whatsapp: 10500, instagram: 7400, x: 2600, snapchat: 3600, tiktok: 5600, telegram: 1620, website: 4400, email: 3100, store: 6400 },
    { period: "سبتمبر", whatsapp: 11000, instagram: 7800, x: 2750, snapchat: 3750, tiktok: 5900, telegram: 1720, website: 4600, email: 3250, store: 6800 },
    { period: "أكتوبر", whatsapp: 11900, instagram: 8400, x: 2980, snapchat: 4050, tiktok: 6450, telegram: 1880, website: 4950, email: 3480, store: 7350 },
    { period: "نوفمبر", whatsapp: 12480, instagram: 8920, x: 3240, snapchat: 4560, tiktok: 6780, telegram: 2100, website: 5400, email: 3800, store: 7800 },
    { period: "ديسمبر", whatsapp: 13500, instagram: 9500, x: 3400, snapchat: 4800, tiktok: 7200, telegram: 2200, website: 5700, email: 4000, store: 8500 },
  ],
  overall: [
    { period: "2023", whatsapp: 98000, instagram: 68000, x: 24000, snapchat: 32000, tiktok: 50000, telegram: 15000, website: 39000, email: 28000, store: 58000 },
    { period: "2024", whatsapp: 125000, instagram: 89000, x: 31000, snapchat: 42000, tiktok: 65000, telegram: 19500, website: 51000, email: 36000, store: 74000 },
    { period: "2025", whatsapp: 136700, instagram: 96400, x: 34070, snapchat: 45160, tiktok: 71380, telegram: 21550, website: 55300, email: 39480, store: 81150 },
  ],
};

// ─── Employee Data ───────────────────────────────────────
export const employeeStats: EmployeeStat[] = [
  {
    id: "E-001", name: "سلطان الدوسري", avatar: "سد", branch: "الرياض - النخيل", department: "خدمة العملاء", role: "مشرف",
    totalMessages: 2840, answeredMessages: 2780, totalCalls: 420, answeredCalls: 408,
    frtMinutes: 1.8, ttrHours: 2.1, lateMessages: 12, lateCalls: 3,
    conversionsOrders: 145, conversionsQuotations: 89,
    satisfactionScore: 4.8, kpiScore: 96, kpiTier: "star",
    availabilityRate: 98.2, aiAssisted: 320,
  },
  {
    id: "E-002", name: "نوف العتيبي", avatar: "نع", branch: "جدة - التحلية", department: "خدمة العملاء", role: "وكيل",
    totalMessages: 2450, answeredMessages: 2380, totalCalls: 380, answeredCalls: 365,
    frtMinutes: 2.3, ttrHours: 2.8, lateMessages: 18, lateCalls: 5,
    conversionsOrders: 128, conversionsQuotations: 72,
    satisfactionScore: 4.6, kpiScore: 91, kpiTier: "excellent",
    availabilityRate: 96.5, aiAssisted: 280,
  },
  {
    id: "E-003", name: "فهد القحطاني", avatar: "فق", branch: "الدمام - الفيصلية", department: "المبيعات", role: "وكيل",
    totalMessages: 1980, answeredMessages: 1890, totalCalls: 520, answeredCalls: 498,
    frtMinutes: 3.1, ttrHours: 3.5, lateMessages: 28, lateCalls: 8,
    conversionsOrders: 185, conversionsQuotations: 95,
    satisfactionScore: 4.4, kpiScore: 87, kpiTier: "excellent",
    availabilityRate: 94.8, aiAssisted: 190,
  },
  {
    id: "E-004", name: "ريم الشهري", avatar: "رش", branch: "الرياض - العليا", department: "خدمة VIP", role: "مختص VIP",
    totalMessages: 1620, answeredMessages: 1610, totalCalls: 290, answeredCalls: 288,
    frtMinutes: 0.8, ttrHours: 1.2, lateMessages: 2, lateCalls: 0,
    conversionsOrders: 92, conversionsQuotations: 45,
    satisfactionScore: 4.9, kpiScore: 98, kpiTier: "star",
    availabilityRate: 99.1, aiAssisted: 150,
  },
  {
    id: "E-005", name: "عبدالله المالكي", avatar: "عم", branch: "جدة - الحمراء", department: "خدمة العملاء", role: "وكيل",
    totalMessages: 2100, answeredMessages: 1950, totalCalls: 340, answeredCalls: 310,
    frtMinutes: 4.2, ttrHours: 4.8, lateMessages: 45, lateCalls: 12,
    conversionsOrders: 78, conversionsQuotations: 52,
    satisfactionScore: 4.1, kpiScore: 72, kpiTier: "good",
    availabilityRate: 91.2, aiAssisted: 240,
  },
  {
    id: "E-006", name: "هدى السالم", avatar: "هس", branch: "الرياض - النخيل", department: "التسويق", role: "وكيل",
    totalMessages: 1850, answeredMessages: 1790, totalCalls: 180, answeredCalls: 172,
    frtMinutes: 2.8, ttrHours: 3.0, lateMessages: 22, lateCalls: 4,
    conversionsOrders: 110, conversionsQuotations: 68,
    satisfactionScore: 4.5, kpiScore: 85, kpiTier: "excellent",
    availabilityRate: 95.3, aiAssisted: 210,
  },
  {
    id: "E-007", name: "محمد الحربي", avatar: "مح", branch: "الدمام - الشاطئ", department: "خدمة العملاء", role: "متدرب",
    totalMessages: 980, answeredMessages: 880, totalCalls: 150, answeredCalls: 128,
    frtMinutes: 6.5, ttrHours: 6.2, lateMessages: 58, lateCalls: 18,
    conversionsOrders: 32, conversionsQuotations: 28,
    satisfactionScore: 3.8, kpiScore: 58, kpiTier: "developing",
    availabilityRate: 87.5, aiAssisted: 310,
  },
  {
    id: "E-008", name: "لينا الزهراني", avatar: "لز", branch: "مكة - العزيزية", department: "خدمة العملاء", role: "وكيل",
    totalMessages: 1540, answeredMessages: 1420, totalCalls: 260, answeredCalls: 238,
    frtMinutes: 5.1, ttrHours: 5.5, lateMessages: 42, lateCalls: 10,
    conversionsOrders: 65, conversionsQuotations: 40,
    satisfactionScore: 3.9, kpiScore: 65, kpiTier: "good",
    availabilityRate: 89.8, aiAssisted: 260,
  },
];

// ─── KPI Tier Config ─────────────────────────────────────
export const kpiTierConfig: Record<string, { label: string; color: string; bg: string; range: string; description: string }> = {
  star: { label: "نجم", color: "text-primary", bg: "bg-primary/10 border-primary/20", range: "95-100", description: "أداء استثنائي متميز" },
  excellent: { label: "ممتاز", color: "text-green-600 dark:text-green-400", bg: "bg-green-500/10 border-green-500/20", range: "85-94", description: "أداء ممتاز ومتسق" },
  good: { label: "جيد", color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-500/10 border-blue-500/20", range: "70-84", description: "أداء جيد مع فرص للتحسين" },
  developing: { label: "تطوير", color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-500/10 border-purple-500/20", range: "50-69", description: "في طور التطوير والنمو" },
  "needs-support": { label: "يحتاج دعم", color: "text-rose-600 dark:text-rose-400", bg: "bg-rose-500/10 border-rose-500/20", range: "< 50", description: "يحتاج دعم وتوجيه إضافي" },
};

// ─── Ticket Data ─────────────────────────────────────────
export const ticketStats: TicketStat[] = [
  { status: "open", statusAr: "مفتوحة", count: 342, color: "#3B82F6", trend: 5.2 },
  { status: "closed", statusAr: "مغلقة", count: 1856, color: "#22C55E", trend: 12.8 },
  { status: "stale", statusAr: "متأخرة / راكدة", count: 67, color: "#EF4444", trend: -8.3 },
  { status: "in-progress", statusAr: "قيد المعالجة", count: 189, color: "#F59E0B", trend: 2.1 },
  { status: "escalated", statusAr: "تصعيد", count: 23, color: "#8B5CF6", trend: -15.4 },
];

export const ticketsByChannel: { channel: string; channelAr: string; open: number; closed: number; stale: number; color: string }[] = [
  { channel: "whatsapp", channelAr: "واتساب", open: 98, closed: 520, stale: 15, color: "#25D366" },
  { channel: "instagram", channelAr: "إنستغرام", open: 65, closed: 380, stale: 12, color: "#E1306C" },
  { channel: "website", channelAr: "الموقع", open: 52, closed: 290, stale: 10, color: "#06B6D4" },
  { channel: "email", channelAr: "البريد", open: 48, closed: 410, stale: 18, color: "#EA4335" },
  { channel: "store", channelAr: "المتجر", open: 32, closed: 150, stale: 5, color: "#8B5CF6" },
  { channel: "x", channelAr: "X", open: 22, closed: 48, stale: 3, color: "#1DA1F2" },
  { channel: "snapchat", channelAr: "سناب شات", open: 15, closed: 32, stale: 2, color: "#FFFC00" },
  { channel: "telegram", channelAr: "تيليجرام", open: 8, closed: 18, stale: 1, color: "#0088CC" },
  { channel: "tiktok", channelAr: "تيك توك", open: 2, closed: 8, stale: 1, color: "#000000" },
];

// ─── Branch Data ─────────────────────────────────────────
export const branchStats: BranchStat[] = [
  { id: "B-001", name: "فرع الرياض - النخيل", city: "الرياض", customerCount: 1240, revenue: 2850000, ticketsOpen: 98, ticketsClosed: 520, ticketsStale: 12, avgFrt: 2.1, avgTtr: 2.8, satisfaction: 4.7, topAgent: "سلطان الدوسري", employeeCount: 8 },
  { id: "B-002", name: "فرع جدة - التحلية", city: "جدة", customerCount: 980, revenue: 2200000, ticketsOpen: 82, ticketsClosed: 440, ticketsStale: 15, avgFrt: 2.5, avgTtr: 3.2, satisfaction: 4.5, topAgent: "نوف العتيبي", employeeCount: 6 },
  { id: "B-003", name: "فرع الدمام - الفيصلية", city: "الدمام", customerCount: 720, revenue: 1650000, ticketsOpen: 65, ticketsClosed: 380, ticketsStale: 10, avgFrt: 3.0, avgTtr: 3.8, satisfaction: 4.3, topAgent: "فهد القحطاني", employeeCount: 5 },
  { id: "B-004", name: "فرع الرياض - العليا", city: "الرياض", customerCount: 890, revenue: 2100000, ticketsOpen: 55, ticketsClosed: 310, ticketsStale: 8, avgFrt: 1.5, avgTtr: 2.0, satisfaction: 4.8, topAgent: "ريم الشهري", employeeCount: 7 },
  { id: "B-005", name: "فرع مكة - العزيزية", city: "مكة", customerCount: 560, revenue: 1380000, ticketsOpen: 42, ticketsClosed: 206, ticketsStale: 22, avgFrt: 4.2, avgTtr: 5.0, satisfaction: 4.0, topAgent: "لينا الزهراني", employeeCount: 4 },
];

// ─── VIP Data ────────────────────────────────────────────
export const vipStats: VipStat = {
  totalVip: 248, totalInteractions: 4820, avgResponseTime: 1.2, avgResolutionTime: 1.8,
  satisfaction: 4.85, retentionRate: 96.5, revenueShare: 62.3, escalations: 8, dedicatedAgents: 4,
};

export const vipHandlingByAgent: { name: string; interactions: number; satisfaction: number; resolved: number; avgFrt: number }[] = [
  { name: "ريم الشهري", interactions: 1820, satisfaction: 4.9, resolved: 1790, avgFrt: 0.8 },
  { name: "سلطان الدوسري", interactions: 1450, satisfaction: 4.8, resolved: 1410, avgFrt: 1.2 },
  { name: "نوف العتيبي", interactions: 980, satisfaction: 4.7, resolved: 945, avgFrt: 1.5 },
  { name: "هدى السالم", interactions: 570, satisfaction: 4.6, resolved: 548, avgFrt: 1.8 },
];

export const vipByChannel: { channel: string; channelAr: string; count: number; satisfaction: number }[] = [
  { channel: "whatsapp", channelAr: "واتساب", count: 1650, satisfaction: 4.9 },
  { channel: "store", channelAr: "المتجر", count: 1280, satisfaction: 4.8 },
  { channel: "email", channelAr: "البريد", count: 820, satisfaction: 4.7 },
  { channel: "website", channelAr: "الموقع", count: 580, satisfaction: 4.6 },
  { channel: "instagram", channelAr: "إنستغرام", count: 490, satisfaction: 4.5 },
];

// ─── AI vs Human Data ────────────────────────────────────
export const aiHumanStats: AiHumanStat[] = [
  { category: "total_interactions", categoryAr: "إجمالي التفاعلات", ai: 18500, human: 28800 },
  { category: "resolved_first_contact", categoryAr: "حل من أول تواصل", ai: 14200, human: 21600 },
  { category: "escalated", categoryAr: "تصعيد", ai: 2800, human: 980 },
  { category: "avg_response_sec", categoryAr: "متوسط الاستجابة (ثانية)", ai: 3, human: 180 },
  { category: "satisfaction", categoryAr: "رضا العملاء", ai: 4.2, human: 4.6 },
  { category: "cost_per_interaction", categoryAr: "التكلفة لكل تفاعل (ر.س)", ai: 0.12, human: 4.50 },
];

export const aiHumanTimeSeries: { period: string; aiInteractions: number; humanInteractions: number; aiResolution: number; humanResolution: number }[] = [
  { period: "يناير", aiInteractions: 1200, humanInteractions: 2100, aiResolution: 78, humanResolution: 85 },
  { period: "فبراير", aiInteractions: 1350, humanInteractions: 2050, aiResolution: 79, humanResolution: 86 },
  { period: "مارس", aiInteractions: 1500, humanInteractions: 2200, aiResolution: 80, humanResolution: 86 },
  { period: "أبريل", aiInteractions: 1650, humanInteractions: 2300, aiResolution: 81, humanResolution: 87 },
  { period: "مايو", aiInteractions: 1800, humanInteractions: 2350, aiResolution: 82, humanResolution: 87 },
  { period: "يونيو", aiInteractions: 1950, humanInteractions: 2400, aiResolution: 83, humanResolution: 87 },
  { period: "يوليو", aiInteractions: 2100, humanInteractions: 2450, aiResolution: 84, humanResolution: 88 },
  { period: "أغسطس", aiInteractions: 2300, humanInteractions: 2500, aiResolution: 84, humanResolution: 88 },
  { period: "سبتمبر", aiInteractions: 2500, humanInteractions: 2550, aiResolution: 85, humanResolution: 88 },
  { period: "أكتوبر", aiInteractions: 2700, humanInteractions: 2600, aiResolution: 86, humanResolution: 89 },
  { period: "نوفمبر", aiInteractions: 2900, humanInteractions: 2650, aiResolution: 86, humanResolution: 89 },
  { period: "ديسمبر", aiInteractions: 3100, humanInteractions: 2700, aiResolution: 87, humanResolution: 89 },
];

// ─── Overview Summary ────────────────────────────────────
export const overviewKPIs = {
  totalCustomers: 4390,
  totalRevenue: 10180000,
  totalTickets: 2477,
  avgSatisfaction: 4.45,
  totalMessages: 47280,
  totalCalls: 2830,
  avgFrt: 2.8,
  avgTtr: 3.4,
  channelCount: 9,
  employeeCount: 8,
  branchCount: 5,
  vipCustomers: 248,
  aiHandledPercent: 39.1,
};
