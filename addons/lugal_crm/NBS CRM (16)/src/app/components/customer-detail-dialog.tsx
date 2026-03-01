import { useState, useMemo } from "react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { ScrollArea } from "./ui/scroll-area";
import { Textarea } from "./ui/textarea";
import { Separator } from "./ui/separator";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import {
  ArrowRight, Crown, ShoppingBag, Package, FileText, MessageSquare, Settings,
  Phone, MapPin, Calendar, Clock, CreditCard, Truck, AlertCircle,
  XCircle, Download, Paperclip, Bell, Store, Heart,
  TrendingUp, Eye, Plus, MoreHorizontal, Building, Receipt,
  Send, ChevronDown, Sparkles, Activity, PhoneCall, PhoneIncoming,
  PhoneOutgoing, User, Timer, StickyNote,
  LayoutDashboard, Ticket, UserCheck, Globe,
  Star, CircleDot, CalendarCheck, BadgeCheck, Banknote,
  ClipboardList, Box, MessageCircle, Camera, Music, Hash, AtSign, Fingerprint, Link2, ShieldCheck
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { differenceInDays, differenceInHours, differenceInMonths, differenceInYears, format } from "date-fns";
import { ar } from "date-fns/locale";
import { InvoiceCreationContainer } from "../../features/pos-invoice/containers/InvoiceCreationContainer";

// ─── Types ─────────────────────────────────────────────
interface CustomerPhone {
  number: string;
  label: string;
}

interface ChannelIdentity {
  channel: "whatsapp" | "instagram" | "x" | "snapchat" | "tiktok" | "telegram" | "website" | "email" | "store";
  handle: string;
  verified: boolean;
  lastActive?: string;
}

interface CustomerAddress {
  country: string;
  state: string;
  city: string;
  district: string;
  street: string;
  building: string;
  postalCode: string;
}

interface Sample {
  id: string;
  name: string;
  version: string;
  dateSent: string;
  image: string;
}

interface CallEntry {
  id: string;
  date: string;
  time: string;
  duration: string;
  agent: string;
  type: "inbound" | "outbound" | "missed";
  notes: string;
  action: string;
  aiSummary?: string;
}

interface PaymentRecord {
  id: string;
  date: string;
  time: string;
  amount: number;
  method: "ERP" | "كاشير" | "مركز الاتصال";
  user: string;
  source: string;
  invoiceId: string;
  status: "مكتمل" | "معلق" | "مرفوض";
}

interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: "مدفوعة" | "معلقة" | "متأخرة" | "مسودة" | "قيد التوصيل";
  items: number;
  dueDate?: string;
}

interface TicketItem {
  id: string;
  subject: string;
  status: "مفتوحة" | "قيد المعالجة" | "مغلقة" | "متصاعدة";
  priority: "عاجل" | "عالي" | "م��وسط" | "منخفض";
  date: string;
  assignedTo: string;
}

interface StickyNote {
  id: string;
  text: string;
  author: string;
  date: string;
  color: "yellow" | "pink" | "green" | "blue" | "purple";
}

interface FollowUp {
  id: string;
  title: string;
  description: string;
  dueDate: string;
  assignedTo: string;
  assignedBy: string;
  priority: "عاجل" | "عالي" | "متوسط" | "منخفض";
  status: "معلق" | "مكتمل" | "متأخر";
}

interface Attachment {
  id: string;
  name: string;
  type: string;
  size: string;
  date: string;
  uploadedBy: string;
}

interface Branch {
  name: string;
  location: string;
  manager: string;
  phone: string;
}

interface TopItem {
  name: string;
  quantity: number;
  totalSpent: number;
  lastPurchase: string;
}

interface ActivityEntry {
  id: string;
  type: "purchase" | "call" | "ticket" | "payment" | "note" | "sample" | "follow-up";
  description: string;
  date: string;
  user?: string;
}

interface CustomerDetail {
  id: string;
  name: string;
  email: string;
  phones: CustomerPhone[];
  address: CustomerAddress;
  tags: string[];
  vipStatus: boolean;
  lifetimeValue: number;
  customerSince: string;
  lastCall: string;
  lastInteraction: string;
  lastInvoiceDate: string;
  currentStatus: {
    hasOpenInvoice: boolean;
    hasDelivery: boolean;
    hasDraft: boolean;
    overdueInvoices: number;
  };
  samples: Sample[];
  callLog: CallEntry[];
  payments: PaymentRecord[];
  paymentTrends: {
    discountsApplied: number;
    overdueCount: number;
    avgPaymentDays: number;
    totalPaid: number;
  };
  attachments: Attachment[];
  invoices: Invoice[];
  location: string;
  shop: string;
  notes: StickyNote[];
  branches: Branch[];
  topItems: TopItem[];
  tickets: TicketItem[];
  activities: ActivityEntry[];
  followUps: FollowUp[];
  favoriteFragrance: string;
  preferredShoppingTime: string;
  avgBasketValue: number;
  shippingInfo: { address: string; method: string };
  billingInfo: { address: string; method: string };
  accountManager: { name: string; role: string; phone: string; };
  referralSource: string;
  profileImage?: string;
  totalPurchases: number;
  channelIdentities: ChannelIdentity[];
}

// ─── Mock Data Generator ────────────────────────────────
function enrichCustomerData(customer: any): CustomerDetail {
  return {
    ...customer,
    phones: [
      { number: customer.phone || "+966 50 123 4567", label: "أساسي" },
      { number: "+966 55 987 6543", label: "ثانوي" },
      { number: "+966 11 234 5678", label: "مكتب" },
    ],
    address: {
      country: "المملكة العربية ا��سعودية",
      state: "منطقة الرياض",
      city: customer.address?.split("،")[0]?.trim() || "الرياض",
      district: customer.address?.split("،")[1]?.trim() || "حي النخيل",
      street: customer.address?.split("،")[2]?.trim() || "شارع الملك فهد",
      building: "مبنى رقم 45",
      postalCode: "12345",
    },
    tags: customer.vipStatus
      ? ["VIP", "عميل نشط", "مخلص", "مؤسسة كبيرة"]
      : ["عميل نشط", "فرصة كبيرة"],
    lifetimeValue: customer.totalPurchases * 2.8 || 45680,
    customerSince: customer.joinDate || "2023-01-15",
    lastCall: "2026-02-18",
    lastInteraction: "2026-02-15",
    lastInvoiceDate: "2026-02-10",
    currentStatus: {
      hasOpenInvoice: true,
      hasDelivery: customer.vipStatus,
      hasDraft: !customer.vipStatus,
      overdueInvoices: customer.vipStatus ? 0 : 2,
    },
    samples: [
      { id: "S-001", name: "عود ملكي - إصدار محدود", version: "V3.2", dateSent: "2025-11-15", image: "https://images.unsplash.com/photo-1610109790326-9a21dfe969b7?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxsdXh1cnklMjBvdWQlMjBwZXJmdW1lJTIwYm90dGxlJTIwZ29sZHxlbnwxfHx8fDE3NzE1ODQ3MzB8MA&ixlib=rb-4.1.0&q=80&w=1080" },
      { id: "S-002", name: "روز باريس الفاخر", version: "V2.0", dateSent: "2025-09-20", image: "https://images.unsplash.com/photo-1763987300634-7b0822cbf390?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxyb3NlJTIwcGVyZnVtZSUyMGJvdHRsZSUyMGx1eHVyeXxlbnwxfHx8fDE3NzE1ODQ3MzB8MA&ixlib=rb-4.1.0&q=80&w=1080" },
      { id: "S-003", name: "مسك الليل - تجريبي", version: "V1.5", dateSent: "2025-06-10", image: "https://images.unsplash.com/photo-1763970586856-0c71ab0e5c48?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtdXNrJTIwcGVyZnVtZSUyMGZyYWdyYW5jZSUyMGJvdHRsZXxlbnwxfHx8fDE3NzE1ODQ3MzF8MA&ixlib=rb-4.1.0&q=80&w=1080" },
    ],
    callLog: [
      { id: "CL-001", date: "2026-02-18", time: "10:30", duration: "12 دقيقة", agent: "سارة الحربي", type: "outbound", notes: "تم الاستفسار عن طلب جديد من العود الملكي، ورغبته في كمية أكبر.", action: "متابعة بعرض خاص", aiSummary: "العميل مهتم بالعود الملكي، يُنصح بعرض خصم 10% للكمية." },
      { id: "CL-002", date: "2026-02-10", time: "14:15", duration: "8 دقائق", agent: "محمد الخالدي", type: "inbound", notes: "اتصل للاستفسار عن حالة الشحنة الأخيرة.", action: "تم تزويده برقم التتبع", aiSummary: "استف��ار روتيني عن الشحن، لا يحتاج متابعة." },
      { id: "CL-003", date: "2026-01-25", time: "09:00", duration: "0 دقيقة", agent: "فاطمة السالم", type: "missed", notes: "مكالمة فائتة - تم إعادة الاتصال لاحقاً", action: "تمت إعادة الاتصال", aiSummary: undefined },
      { id: "CL-004", date: "2026-01-15", time: "16:45", duration: "20 دقيقة", agent: "سارة الحربي", type: "outbound", notes: "عرض حملة نهاية السنة، العميل مهتم بمجموعة العطور الجديدة.", action: "إرسال كتالوج بالمنتجات الجديدة", aiSummary: "فرصة بيع عالية، العميل مهتم بالمنتجات الجديدة. يُنصح بالمتابعة خلال أسبوع." },
    ],
    payments: [
      { id: "PAY-001", date: "2026-02-10", time: "10:30:45", amount: 3500, method: "ERP", user: "النظام التلقائي", source: "الموقع الإلكتروني", invoiceId: "INV-2024-089", status: "مكتمل" },
      { id: "PAY-002", date: "2026-01-15", time: "14:22:10", amount: 2800, method: "كاشير", user: "علي المحمد", source: "فرع الرياض - النخيل", invoiceId: "INV-2024-078", status: "مكتمل" },
      { id: "PAY-003", date: "2025-12-20", time: "09:15:33", amount: 5200, method: "مركز الاتصال", user: "سارة الحربي", source: "مركز الاتصال الرئيسي", invoiceId: "INV-2024-065", status: "مكتمل" },
      { id: "PAY-004", date: "2025-11-05", time: "16:40:12", amount: 1200, method: "ERP", user: "النظام التلقائي", source: "التطبيق", invoiceId: "INV-2024-052", status: "مكتمل" },
      { id: "PAY-005", date: "2025-10-10", time: "11:05:20", amount: 4100, method: "كاشير", user: "محمد الخالدي", source: "فرع جدة - التحلية", invoiceId: "INV-2024-041", status: "معلق" },
    ],
    paymentTrends: {
      discountsApplied: 3,
      overdueCount: customer.vipStatus ? 0 : 2,
      avgPaymentDays: 5,
      totalPaid: customer.totalPurchases || 15680,
    },
    attachments: [
      { id: "ATT-001", name: "الهوية الوطنية", type: "هوية", size: "2.4 MB", date: "2024-01-15", uploadedBy: "محمد الخالدي" },
      { id: "ATT-002", name: "السجل التجاري", type: "وثيقة", size: "1.8 MB", date: "2024-01-15", uploadedBy: "محمد الخالدي" },
      { id: "ATT-003", name: "عقد التوريد", type: "عقد", size: "3.2 MB", date: "2024-06-20", uploadedBy: "سارة الحربي" },
    ],
    invoices: [
      { id: "INV-2026-012", date: "2026-02-10", amount: 3500, status: "معلقة", items: 3, dueDate: "2026-03-10" },
      { id: "INV-2026-005", date: "2026-01-15", amount: 2800, status: "مدفوعة", items: 2 },
      { id: "INV-2025-089", date: "2025-12-20", amount: 5200, status: "مدفوعة", items: 5 },
      { id: "INV-2025-078", date: "2025-11-05", amount: 1200, status: "متأخرة", items: 1, dueDate: "2025-12-05" },
      { id: "INV-2025-065", date: "2025-10-10", amount: 4100, status: "مدفوعة", items: 4 },
      { id: "INV-2025-052", date: "2025-09-01", amount: 1800, status: "مسودة", items: 2 },
    ],
    location: customer.address?.split("،")[0]?.trim() || "الرياض",
    shop: "فرع الرياض - النخيل",
    notes: [
      { id: "N-001", text: "لا يُفضل التواصل عبر تيليجرام نهائياً. يُفضل الواتساب أو الاتصال المباشر.", author: "محمد الخالدي", date: "2026-01-10T14:30:00", color: "yellow" as const },
      { id: "N-002", text: "يفضل العطور الشرقية الثقيلة، خاصة العود والمسك. لا يحب الروائح الخفيفة.", author: "سارة الحربي", date: "2025-12-15T09:15:00", color: "pink" as const },
      { id: "N-003", text: "هذا العميل دائماً متأخر في السداد، يجب المتابعة المستمرة.", author: "فاطمة السالم", date: "2025-11-20T16:45:00", color: "green" as const },
      { id: "N-004", text: "تم تقديم خصم 15% في عيد ميلاده الماضي. موعد عيد ميلاده القادم: 15 مارس.", author: "علي المحمد", date: "2025-10-05T11:00:00", color: "blue" as const },
    ],
    branches: [
      { name: "الفرع الرئيسي", location: "الرياض - حي النخيل", manager: "أحمد العلي", phone: "+966 11 234 5678" },
      { name: "فرع جدة", location: "جدة - حي الحمراء", manager: "خالد المطيري", phone: "+966 12 345 6789" },
    ],
    topItems: [
      { name: "عود ملكي", quantity: 12, totalSpent: 7200, lastPurchase: "2026-02-10" },
      { name: "مسك الليل", quantity: 8, totalSpent: 4800, lastPurchase: "2026-01-20" },
      { name: "روز باريس", quantity: 6, totalSpent: 3600, lastPurchase: "2025-12-15" },
      { name: "عنبر فاخر", quantity: 4, totalSpent: 2400, lastPurchase: "2025-11-10" },
      { name: "بخور العرايس", quantity: 3, totalSpent: 1500, lastPurchase: "2025-10-01" },
    ],
    tickets: [
      { id: "TK-001", subject: "تأخر في تسليم الطلب #2089", status: "مفتوحة", priority: "عالي", date: "2026-02-18", assignedTo: "سارة الحربي" },
      { id: "TK-002", subject: "استبدال منتج تالف", status: "قيد المعالجة", priority: "متوسط", date: "2026-02-05", assignedTo: "محمد الخالدي" },
      { id: "TK-003", subject: "طلب فاتورة ضريبية", status: "مغلقة", priority: "منخفض", date: "2026-01-10", assignedTo: "فاطمة السالم" },
    ],
    activities: [
      { id: "A-001", type: "purchase", description: "شراء عطر عود ملكي (3 قطع)", date: "2026-02-10T10:30:00", user: "عبر الموقع" },
      { id: "A-002", type: "call", description: "مكالمة صادرة - متابعة طلب", date: "2026-02-08T14:15:00", user: "سارة الحربي" },
      { id: "A-003", type: "payment", description: "دفعة 3,500 ر.س عبر ERP", date: "2026-02-10T10:30:00", user: "تلقائي" },
      { id: "A-004", type: "ticket", description: "فتح تذكرة: تأخر تسليم", date: "2026-02-05T09:00:00", user: "العميل" },
      { id: "A-005", type: "sample", description: "إرسال عينة عود ملكي V3.2", date: "2025-11-15T11:00:00", user: "محمد الخالدي" },
      { id: "A-006", type: "note", description: "إضافة ملاحظة حول تفضيلات العميل", date: "2025-12-15T16:30:00", user: "سارة الحربي" },
      { id: "A-007", type: "follow-up", description: "تعيين متابعة للتواصل بخصوص عرض جديد", date: "2026-01-20T08:00:00", user: "المدير" },
      { id: "A-008", type: "purchase", description: "شراء مسك الليل (2 قطع)", date: "2026-01-20T12:00:00", user: "فرع الرياض" },
    ],
    followUps: [
      { id: "FU-001", title: "متابعة عرض العود الملكي", description: "متابعة العميل بخصوص عرض خصم 10% على العود الملكي - الكمية الكبيرة", dueDate: "2026-02-25", assignedTo: "سارة الحربي", assignedBy: "أحمد العلي", priority: "عالي", status: "معلق" },
      { id: "FU-002", title: "تجديد العقد السنوي", description: "يجب التواصل مع العميل لتجديد عقد التوريد السنوي قبل نهاية الشهر", dueDate: "2026-02-28", assignedTo: "محمد الخالدي", assignedBy: "أحمد العلي", priority: "عاجل", status: "معلق" },
      { id: "FU-003", title: "إرسال كتالوج الربيع", description: "إرسال كتالوج المنتجات الجديدة لموسم الربيع 2026", dueDate: "2026-03-01", assignedTo: "فاطمة السالم", assignedBy: "سارة الحربي", priority: "متوسط", status: "معلق" },
    ],
    favoriteFragrance: customer.favoriteFragrance || "عود ملكي",
    preferredShoppingTime: "مساءً (8-10 م)",
    avgBasketValue: 450,
    shippingInfo: {
      address: customer.address || "الرياض، حي النخيل، شارع الملك فهد",
      method: "توصيل سريع (24 ساعة)",
    },
    billingInfo: {
      address: customer.address || "الرياض، حي النخيل، شارع الملك فهد",
      method: "تحويل بنكي",
    },
    accountManager: {
      name: "محمد أحمد الخالدي",
      role: "مدير علاقات العملاء",
      phone: "+966 50 999 8877",
    },
    referralSource: "تسويق مباشر - معرض العطور الدولي 2023",
    profileImage: undefined,
    channelIdentities: [
      { channel: "whatsapp", handle: customer.phone || "+966 50 123 4567", verified: true, lastActive: "2026-02-22" },
      { channel: "instagram", handle: "@noor_alnebras_vip", verified: true, lastActive: "2026-02-20" },
      { channel: "x", handle: "@nabras_client", verified: false, lastActive: "2026-01-15" },
      { channel: "snapchat", handle: "nabras.snap", verified: false, lastActive: "2026-02-18" },
      { channel: "tiktok", handle: "@nabras_perfumes", verified: true, lastActive: "2026-02-10" },
      { channel: "telegram", handle: "@nabras_tg", verified: false, lastActive: "2025-12-20" },
      { channel: "website", handle: customer.email || "ahmed@example.com", verified: true, lastActive: "2026-02-21" },
      { channel: "email", handle: customer.email || "ahmed@example.com", verified: true, lastActive: "2026-02-19" },
      { channel: "store", handle: "فرع الرياض - النخيل", verified: true, lastActive: "2026-02-15" },
    ],
  };
}

// ─── Helpers ────────────────────────────────────────────
function getTimeSinceLastInteraction(dateStr: string) {
  const date = new Date(dateStr);
  const now = new Date();
  const years = differenceInYears(now, date);
  const months = differenceInMonths(now, date) % 12;
  const days = differenceInDays(now, date) % 30;
  const hours = differenceInHours(now, date) % 24;
  return { years, months, days, hours, total: differenceInDays(now, date) };
}

function getStatusColor(status: string) {
  switch (status) {
    case "مدفوعة": case "مكتمل": case "مغلقة": return "bg-green-100 dark:bg-green-500/10 text-green-700 dark:text-green-400 border-green-200 dark:border-green-500/20";
    case "معلقة": case "معلق": case "قيد المعالجة": return "bg-yellow-100 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/20";
    case "متأخرة": case "متأخر": case "مرفوض": case "متصاعدة": return "bg-red-100 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20";
    case "مسودة": return "bg-slate-100 dark:bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-500/20";
    case "قيد التوصيل": return "bg-blue-100 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20";
    case "مفتوحة": return "bg-cyan-100 dark:bg-primary/10 text-cyan-700 dark:text-primary border-cyan-200 dark:border-primary/20";
    default: return "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-white/10";
  }
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case "عاجل": return "bg-red-100 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20";
    case "عالي": return "bg-yellow-100 dark:bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/20";
    case "متوسط": return "bg-blue-100 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20";
    case "منخفض": return "bg-slate-100 dark:bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-500/20";
    default: return "bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-400";
  }
}

const stickyNoteColors: Record<string, string> = {
  yellow: "bg-yellow-50 dark:bg-yellow-500/10 border-yellow-300 dark:border-yellow-500/20",
  pink: "bg-pink-50 dark:bg-pink-500/10 border-pink-300 dark:border-pink-500/20",
  green: "bg-green-50 dark:bg-green-500/10 border-green-300 dark:border-green-500/20",
  blue: "bg-blue-50 dark:bg-blue-500/10 border-blue-300 dark:border-blue-500/20",
  purple: "bg-purple-50 dark:bg-purple-500/10 border-purple-300 dark:border-purple-500/20",
};

const tagColors: Record<string, string> = {
  "VIP": "bg-gradient-to-r from-[#BF953F]/20 to-[#D4AF37]/20 dark:from-[#BF953F]/30 dark:to-[#D4AF37]/30 text-[#B8860B] dark:text-[#D4AF37] border-[#D4AF37]/30",
  "عميل نشط": "bg-green-100 dark:bg-green-500/15 text-green-700 dark:text-green-400 border-green-200 dark:border-green-500/20",
  "مخلص": "bg-cyan-100 dark:bg-primary/15 text-cyan-700 dark:text-primary border-cyan-200 dark:border-primary/20",
  "مؤسسة كبيرة": "bg-blue-100 dark:bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20",
  "فرصة كبيرة": "bg-purple-100 dark:bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-200 dark:border-purple-500/20",
  "عميل راكد": "bg-slate-100 dark:bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-500/20",
};

function getTagColor(tag: string) {
  return tagColors[tag] || "bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-white/10";
}

function getActivityIcon(type: string) {
  switch (type) {
    case "purchase": return <ShoppingBag className="w-4 h-4" />;
    case "call": return <PhoneCall className="w-4 h-4" />;
    case "payment": return <CreditCard className="w-4 h-4" />;
    case "ticket": return <Ticket className="w-4 h-4" />;
    case "sample": return <Box className="w-4 h-4" />;
    case "note": return <StickyNote className="w-4 h-4" />;
    case "follow-up": return <Bell className="w-4 h-4" />;
    default: return <CircleDot className="w-4 h-4" />;
  }
}

// ─── Channel Identity Config ────────────────────────────
const channelConfig: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  whatsapp: {
    label: "واتساب",
    icon: <MessageCircle className="w-3.5 h-3.5" />,
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-100 dark:bg-green-500/15 border-green-200 dark:border-green-500/20",
  },
  instagram: {
    label: "إنستغرام",
    icon: <Camera className="w-3.5 h-3.5" />,
    color: "text-pink-600 dark:text-pink-400",
    bg: "bg-pink-100 dark:bg-pink-500/15 border-pink-200 dark:border-pink-500/20",
  },
  x: {
    label: "X",
    icon: <Hash className="w-3.5 h-3.5" />,
    color: "text-slate-700 dark:text-slate-300",
    bg: "bg-slate-100 dark:bg-slate-500/15 border-slate-200 dark:border-slate-500/20",
  },
  snapchat: {
    label: "سناب شات",
    icon: <AtSign className="w-3.5 h-3.5" />,
    color: "text-yellow-600 dark:text-yellow-400",
    bg: "bg-yellow-100 dark:bg-yellow-500/15 border-yellow-200 dark:border-yellow-500/20",
  },
  tiktok: {
    label: "تيك توك",
    icon: <Music className="w-3.5 h-3.5" />,
    color: "text-slate-800 dark:text-slate-200",
    bg: "bg-slate-100 dark:bg-slate-500/15 border-slate-200 dark:border-slate-500/20",
  },
  telegram: {
    label: "تيليجرام",
    icon: <Send className="w-3.5 h-3.5" />,
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-100 dark:bg-blue-500/15 border-blue-200 dark:border-blue-500/20",
  },
  website: {
    label: "الموقع",
    icon: <Globe className="w-3.5 h-3.5" />,
    color: "text-cyan-600 dark:text-primary",
    bg: "bg-cyan-100 dark:bg-primary/15 border-cyan-200 dark:border-primary/20",
  },
  email: {
    label: "البريد",
    icon: <AtSign className="w-3.5 h-3.5" />,
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-100 dark:bg-red-500/15 border-red-200 dark:border-red-500/20",
  },
  store: {
    label: "المتجر",
    icon: <Store className="w-3.5 h-3.5" />,
    color: "text-purple-600 dark:text-purple-400",
    bg: "bg-purple-100 dark:bg-purple-500/15 border-purple-200 dark:border-purple-500/20",
  },
};

// ─── Tab definitions ────────────────────────────────────
const TABS = [
  { id: "overview", label: "نظرة عامة", icon: LayoutDashboard },
  { id: "calls", label: "المكالمات", icon: PhoneCall },
  { id: "financial", label: "المالية", icon: Banknote },
  { id: "samples", label: "العينات", icon: Box },
  { id: "tickets", label: "التذاكر", icon: Ticket },
  { id: "notes", label: "الملاحظات", icon: StickyNote },
  { id: "followups", label: "المتابعة", icon: Bell },
  { id: "attachments", label: "المرفقات", icon: Paperclip },
] as const;

// ─── Component Props ────────────────────────────────────
interface CustomerDetailDialogProps {
  customer: any;
  open: boolean;
  onClose: () => void;
  profileImage?: string;
}

// ─── Main Component ─────────────────────────────────────
export function CustomerDetailDialog({ customer, open, onClose, profileImage }: CustomerDetailDialogProps) {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [expandedCall, setExpandedCall] = useState<string | null>(null);
  const [expandedSample, setExpandedSample] = useState<string | null>(null);
  const [showInvoiceDialog, setShowInvoiceDialog] = useState(false);
  const [newNoteText, setNewNoteText] = useState("");
  const [selectedNoteColor, setSelectedNoteColor] = useState<"yellow" | "pink" | "green" | "blue" | "purple">("yellow");
  const [addedNotes, setAddedNotes] = useState<StickyNote[]>([]);

  const handleAddNote = () => {
    if (!newNoteText.trim()) return;
    const note: StickyNote = {
      id: `N-${Date.now()}`,
      text: newNoteText.trim(),
      author: "سعود المالكي",
      date: new Date().toISOString(),
      color: selectedNoteColor,
    };
    setAddedNotes((prev) => [note, ...prev]);
    setNewNoteText("");
  };

  const data = useMemo(() => customer ? enrichCustomerData(customer) : null, [customer]);
  const timeSince = useMemo(() => data ? getTimeSinceLastInteraction(data.lastInvoiceDate) : null, [data]);

  if (!data) return null;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="max-w-[95vw] xl:max-w-7xl h-[92vh] p-0 gap-0 overflow-hidden flex flex-col bg-background/95 backdrop-blur-xl border-border/50 [&>button]:hidden text-start"
        dir="rtl"
      >
        <div className="sr-only">
          <DialogTitle>{data.name} - بطاقة العميل</DialogTitle>
          <DialogDescription>عرض تفاصيل شاملة 360° للعميل</DialogDescription>
        </div>

        <div className="flex flex-col h-full bg-[#f8fafc] dark:bg-[#0c0e12]">
          {/* ── Header Banner ── */}
          <div className="h-28 w-full bg-gradient-to-l from-cyan-50 via-cyan-100/50 to-blue-50 dark:from-[#1a1d24] dark:via-[#1c1915] dark:to-[#2a261b] relative shrink-0">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] dark:opacity-[0.04]" />
            {/* Close */}
            <Button
              variant="ghost" size="icon"
              className="absolute top-4 start-4 text-slate-500 dark:text-primary/80 bg-white/80 dark:bg-[#1a1d24]/80 hover:bg-white dark:hover:bg-[#252830] backdrop-blur-sm shadow-sm dark:shadow-none dark:border dark:border-white/5 rounded-full w-9 h-9 z-20"
              onClick={onClose}
            >
              <ArrowRight className="w-4 h-4" />
            </Button>

            {/* Status Indicators */}
            <div className="absolute bottom-3 end-4 flex items-center gap-2 flex-wrap z-10">
              {data.currentStatus.hasOpenInvoice && (
                <Badge className="bg-yellow-100/90 dark:bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-300 dark:border-yellow-500/20 backdrop-blur-sm text-[10px] px-2 py-0.5 gap-1">
                  <AlertCircle className="w-3 h-3" /> فاتورة مفتوحة
                </Badge>
              )}
              {data.currentStatus.hasDelivery && (
                <Badge className="bg-blue-100/90 dark:bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-300 dark:border-blue-500/20 backdrop-blur-sm text-[10px] px-2 py-0.5 gap-1">
                  <Truck className="w-3 h-3" /> قيد التوصيل
                </Badge>
              )}
              {data.currentStatus.hasDraft && (
                <Badge className="bg-slate-100/90 dark:bg-white/10 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-white/10 backdrop-blur-sm text-[10px] px-2 py-0.5 gap-1">
                  <FileText className="w-3 h-3" /> مسودة
                </Badge>
              )}
              {data.currentStatus.overdueInvoices > 0 && (
                <Badge className="bg-red-100/90 dark:bg-red-500/15 text-red-700 dark:text-red-400 border-red-300 dark:border-red-500/20 backdrop-blur-sm text-[10px] px-2 py-0.5 gap-1">
                  <XCircle className="w-3 h-3" /> {data.currentStatus.overdueInvoices} فواتير متأخرة
                </Badge>
              )}
            </div>
          </div>

          {/* ── Body ── */}
          <div className="flex-1 min-h-0 flex flex-col md:flex-row relative">

            {/* ── Sidebar ── */}
            <div className="w-full md:w-[300px] lg:w-[320px] border-e border-slate-100 dark:border-white/5 bg-white/50 dark:bg-[#111318]/50 flex flex-col shrink-0 relative z-10 md:h-full">
              {/* Static header: Avatar + Name + Tags + Buttons */}
              <div className="px-5 pt-3 pb-4 text-center shrink-0 -mt-12 relative z-20">
                {/* Avatar */}
                <div className="flex justify-center mb-3">
                  <div className="relative group">
                    <div className="rounded-full p-1 bg-white dark:bg-[#1a1d24] shadow-md dark:shadow-2xl dark:shadow-black/50">
                      <Avatar className="h-24 w-24 border-[3px] border-white dark:border-[#1a1d24] shadow-sm bg-white dark:bg-[#1a1d24] group-hover:scale-105 transition-transform duration-300">
                        {profileImage ? (
                          <AvatarImage src={profileImage} className="object-cover" />
                        ) : null}
                        <AvatarFallback className="bg-cyan-100 dark:bg-primary/15 text-cyan-600 dark:text-primary text-2xl font-bold">
                          {data.name.split(" ").map((n: string) => n[0]).join("").slice(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                    </div>
                    {data.vipStatus && (
                      <div className="absolute bottom-0 end-0 bg-yellow-400 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] text-white p-1 rounded-full border-[3px] border-white dark:border-[#1a1d24] shadow-md flex items-center justify-center w-7 h-7">
                        <Crown className="w-3.5 h-3.5 fill-current" />
                      </div>
                    )}
                  </div>
                </div>

                {/* Name & ID */}
                <div className="mb-3">
                  <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-1">{data.name}</h2>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 font-mono bg-slate-50 dark:bg-white/5 px-2 py-0.5 rounded-md inline-block border border-slate-100 dark:border-white/5">{data.id}</p>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 justify-center mb-3">
                  {data.tags.map((tag, i) => (
                    <span key={i} className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${getTagColor(tag)}`}>{tag}</span>
                  ))}
                </div>

                {/* Quick Contact Buttons */}
                <div className="flex gap-2 justify-center w-full px-1">
                  <Button className="flex-1 bg-cyan-500 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] hover:bg-cyan-600 dark:hover:from-[#AA771C] dark:hover:to-[#BF953F] text-white shadow-sm rounded-xl h-9 text-xs border-none">
                    <MessageSquare className="w-3.5 h-3.5 me-1.5" /> مراسلة
                  </Button>
                  <Button variant="outline" className="flex-1 border-cyan-200 dark:border-white/10 text-cyan-600 dark:text-slate-300 hover:bg-cyan-50 dark:hover:bg-white/5 rounded-xl h-9 text-xs">
                    <Phone className="w-3.5 h-3.5 me-1.5" /> اتصال
                  </Button>
                  <Button variant="outline" className="border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 rounded-xl h-9 w-9 p-0">
                    <Settings className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>

              <Separator className="bg-slate-100 dark:bg-white/5 shrink-0" />

              {/* Sidebar scrollable content */}
              <ScrollArea className="flex-1 min-h-0" dir="rtl">
                <div className="px-5 py-5 space-y-5">
                  {/* ── Identity Resolution ── */}
                  <div className="text-start space-y-2">
                    <div className="flex items-center justify-between px-1">
                      <span className="text-[9px] bg-cyan-100 dark:bg-primary/10 text-cyan-600 dark:text-primary px-1.5 py-0.5 rounded-md border border-cyan-200 dark:border-primary/20 flex items-center gap-1">
                        <Fingerprint className="w-3 h-3" /> موحّدة
                      </span>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium flex items-center gap-1">
                        <Link2 className="w-3 h-3" /> هوية القنوات
                      </p>
                    </div>
                    <div className="bg-white dark:bg-[#1a1d24] rounded-xl p-3 border border-slate-100 dark:border-white/5 space-y-1.5">
                      {data.channelIdentities.map((identity, i) => {
                        const config = channelConfig[identity.channel];
                        if (!config) return null;
                        return (
                          <div
                            key={i}
                            className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-white/[0.03] transition-colors group cursor-default"
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <div className={`p-1.5 rounded-md border shrink-0 ${config.bg}`}>
                                <span className={config.color}>{config.icon}</span>
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-1">
                                  <p className="text-[11px] font-medium text-slate-700 dark:text-slate-200 truncate" dir={identity.channel === "whatsapp" ? "ltr" : undefined}>
                                    {identity.handle}
                                  </p>
                                  {identity.verified && (
                                    <ShieldCheck className="w-3 h-3 text-cyan-500 dark:text-primary shrink-0" />
                                  )}
                                </div>
                                <p className="text-[9px] text-slate-400 dark:text-slate-500">{config.label}</p>
                              </div>
                            </div>
                            {identity.lastActive && (
                              <span className="text-[8px] text-slate-400 dark:text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap ms-2">
                                {format(new Date(identity.lastActive), "dd/MM", { locale: ar })}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                    <p className="text-[9px] text-slate-400 dark:text-slate-500 text-center px-1">
                      {data.channelIdentities.filter(c => c.verified).length} من {data.channelIdentities.length} قنوات موثقة
                    </p>
                  </div>

                  <Separator className="bg-slate-100 dark:bg-white/5" />

                  {/* Phone Numbers */}
                  <div className="text-start space-y-2">
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium px-1">أرقام الهاتف</p>
                    {data.phones.map((phone, i) => (
                      <div key={i} className="bg-white dark:bg-[#1a1d24] rounded-lg p-2.5 border border-slate-100 dark:border-white/5 flex items-center justify-between group hover:border-cyan-100 dark:hover:border-primary/20 transition-colors">
                        <div className="flex items-center gap-2">
                          <Phone className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                          <span className="text-xs font-mono text-slate-700 dark:text-slate-200" dir="ltr">{phone.number}</span>
                        </div>
                        <span className="text-[9px] text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-white/5 px-1.5 py-0.5 rounded">{phone.label}</span>
                      </div>
                    ))}
                  </div>

                  <Separator className="bg-slate-100 dark:bg-white/5" />

                  {/* Full Address */}
                  <div className="text-start space-y-2">
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium px-1">العنوان الكامل</p>
                    <div className="bg-white dark:bg-[#1a1d24] rounded-lg p-3 border border-slate-100 dark:border-white/5 text-start space-y-1.5">
                      <div className="flex items-start gap-2">
                        <MapPin className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                        <div className="text-xs space-y-0.5">
                          <p className="text-slate-700 dark:text-slate-200 font-medium">{data.address.country}</p>
                          <p className="text-slate-500 dark:text-slate-400">{data.address.state} - {data.address.city}</p>
                          <p className="text-slate-500 dark:text-slate-400">{data.address.district}، {data.address.street}</p>
                          <p className="text-slate-500 dark:text-slate-400">{data.address.building}</p>
                          <p className="text-slate-400 dark:text-slate-500 font-mono text-[10px]">الرمز البريدي: {data.address.postalCode}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator className="bg-slate-100 dark:bg-white/5" />

                  {/* Account Manager */}
                  <div className="text-start space-y-2">
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium px-1">مدير الحساب</p>
                    <div className="bg-white dark:bg-[#1a1d24] rounded-lg p-3 border border-slate-100 dark:border-white/5 flex items-center gap-3">
                      <Avatar className="h-9 w-9 border border-slate-200 dark:border-white/10 shrink-0">
                        <AvatarFallback className="bg-primary/10 text-primary text-xs font-bold">
                          {data.accountManager.name.split(" ").map((n: string) => n[0]).join("").slice(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="text-start min-w-0 flex-1">
                        <p className="text-xs font-bold text-slate-700 dark:text-slate-200 truncate">{data.accountManager.name}</p>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500">{data.accountManager.role}</p>
                      </div>
                    </div>
                  </div>

                  <Separator className="bg-slate-100 dark:bg-white/5" />

                  {/* Quick Info Grid */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white dark:bg-[#1a1d24] rounded-lg p-2.5 border border-slate-100 dark:border-white/5 text-center">
                      <p className="text-[9px] text-slate-400 dark:text-slate-500 mb-0.5">عميل منذ</p>
                      <p className="text-[11px] font-bold text-slate-700 dark:text-slate-200">{format(new Date(data.customerSince), "yyyy/MM/dd")}</p>
                    </div>
                    <div className="bg-white dark:bg-[#1a1d24] rounded-lg p-2.5 border border-slate-100 dark:border-white/5 text-center">
                      <p className="text-[9px] text-slate-400 dark:text-slate-500 mb-0.5">آخر اتصال</p>
                      <p className="text-[11px] font-bold text-slate-700 dark:text-slate-200">{format(new Date(data.lastCall), "yyyy/MM/dd")}</p>
                    </div>
                  </div>

                  <Separator className="bg-slate-100 dark:bg-white/5" />

                  {/* Referral Source */}
                  <div className="text-start space-y-2">
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium px-1">مصدر الإحالة</p>
                    <div className="bg-white dark:bg-[#1a1d24] rounded-lg p-2.5 border border-slate-100 dark:border-white/5 flex items-center gap-2">
                      <Globe className="w-3.5 h-3.5 text-primary shrink-0" />
                      <p className="text-xs text-slate-700 dark:text-slate-200">{data.referralSource}</p>
                    </div>
                  </div>

                  <Separator className="bg-slate-100 dark:bg-white/5" />

                  {/* Shipping & Billing */}
                  <div className="text-start space-y-2">
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium px-1">الشحن والفوترة المفضلة</p>
                    <div className="bg-white dark:bg-[#1a1d24] rounded-lg p-2.5 border border-slate-100 dark:border-white/5 space-y-2">
                      <div className="flex items-start gap-2">
                        <Truck className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                        <div className="text-xs">
                          <p className="text-slate-700 dark:text-slate-200 font-medium">{data.shippingInfo.method}</p>
                          <p className="text-[10px] text-slate-400 dark:text-slate-500">{data.shippingInfo.address}</p>
                        </div>
                      </div>
                      <div className="h-px bg-slate-50 dark:bg-white/5" />
                      <div className="flex items-start gap-2">
                        <CreditCard className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                        <div className="text-xs">
                          <p className="text-slate-700 dark:text-slate-200 font-medium">{data.billingInfo.method}</p>
                          <p className="text-[10px] text-slate-400 dark:text-slate-500">{data.billingInfo.address}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator className="bg-slate-100 dark:bg-white/5" />

                  {/* Location & Shop */}
                  <div className="text-start space-y-2">
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium px-1">الموقع والمتجر</p>
                    <div className="bg-white dark:bg-[#1a1d24] rounded-lg p-2.5 border border-slate-100 dark:border-white/5 flex items-center gap-2">
                      <Store className="w-3.5 h-3.5 text-primary shrink-0" />
                      <p className="text-xs text-slate-700 dark:text-slate-200">{data.shop}</p>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </div>

            {/* ── Main Content Area ── */}
            <div className="flex-1 min-h-0 flex flex-col bg-slate-50/50 dark:bg-black/20">
              {/* Quick Actions Bar */}
              <div className="px-5 pt-4 pb-2 border-b border-slate-100 dark:border-white/5 bg-white/30 dark:bg-white/[0.02] shrink-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium ms-2">إجراءات سريعة:</span>
                  <Button size="sm" className="h-7 text-[11px] rounded-lg gap-1.5 bg-cyan-500 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] text-white hover:bg-cyan-600 dark:hover:from-[#AA771C] dark:hover:to-[#BF953F] border-none shadow-sm" onClick={() => setShowInvoiceDialog(true)}>
                    <Receipt className="w-3 h-3" /> إنشاء فاتورة
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-[11px] rounded-lg gap-1.5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5">
                    <Send className="w-3 h-3" /> إرسال كتالوج
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-[11px] rounded-lg gap-1.5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5">
                    <Ticket className="w-3 h-3" /> فتح تذكرة
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-[11px] rounded-lg gap-1.5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5">
                    <CreditCard className="w-3 h-3" /> تسجيل دفعة
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-[11px] rounded-lg gap-1.5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5">
                    <Bell className="w-3 h-3" /> تعيين متابعة
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-slate-400 dark:text-slate-500 hover:text-primary">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Tab Navigation */}
              <div className="px-5 pt-3 pb-0 shrink-0">
                <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide pb-2">
                  {TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-200 shrink-0 ${
                          isActive
                            ? "bg-cyan-500/10 dark:bg-primary/10 text-cyan-600 dark:text-primary border border-cyan-200 dark:border-primary/20"
                            : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5 border border-transparent"
                        }`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        {tab.label}
                        {tab.id === "tickets" && data.tickets.filter(t => t.status !== "مغلقة").length > 0 && (
                          <span className="min-w-[16px] h-4 rounded-full bg-red-500 text-white text-[9px] flex items-center justify-center px-1">
                            {data.tickets.filter(t => t.status !== "مغلقة").length}
                          </span>
                        )}
                        {tab.id === "followups" && data.followUps.filter(f => f.status !== "مكتمل").length > 0 && (
                          <span className="min-w-[16px] h-4 rounded-full bg-yellow-500 text-white text-[9px] flex items-center justify-center px-1">
                            {data.followUps.filter(f => f.status !== "مكتمل").length}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Tab Content */}
              <ScrollArea className="flex-1" dir="rtl">
                <div className="p-5">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeTab}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }}
                      transition={{ duration: 0.2 }}
                    >
                      {/* ═══════ OVERVIEW TAB ═══════ */}
                      {activeTab === "overview" && (
                        <div className="space-y-6">
                          {/* Stat Cards */}
                          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-4 flex items-center justify-between">
                                <div className="p-2.5 bg-cyan-100 dark:bg-primary/15 text-cyan-600 dark:text-primary rounded-xl">
                                  <Heart className="w-5 h-5" />
                                </div>
                                <div className="text-end">
                                  <p className="text-[10px] text-muted-foreground mb-0.5">القيمة الدائمة</p>
                                  <p className="text-xl font-bold text-cyan-600 dark:text-primary font-mono" dir="ltr">{data.lifetimeValue.toLocaleString()}</p>
                                  <p className="text-[9px] text-muted-foreground">ر.س</p>
                                </div>
                              </CardContent>
                            </Card>
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-4 flex items-center justify-between">
                                <div className="p-2.5 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-400 rounded-xl">
                                  <ShoppingBag className="w-5 h-5" />
                                </div>
                                <div className="text-end">
                                  <p className="text-[10px] text-muted-foreground mb-0.5">إجمالي المشتريات</p>
                                  <p className="text-xl font-bold text-foreground font-mono" dir="ltr">{data.totalPurchases?.toLocaleString()}</p>
                                  <p className="text-[9px] text-muted-foreground">ر.س</p>
                                </div>
                              </CardContent>
                            </Card>
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-4 flex items-center justify-between">
                                <div className="p-2.5 bg-primary/10 dark:bg-primary/15 text-primary rounded-xl">
                                  <Crown className="w-5 h-5" />
                                </div>
                                <div className="text-end">
                                  <p className="text-[10px] text-muted-foreground mb-0.5">نقاط الولاء</p>
                                  <p className="text-xl font-bold text-primary font-mono" dir="ltr">1,450</p>
                                  <p className="text-[9px] text-muted-foreground">نقطة</p>
                                </div>
                              </CardContent>
                            </Card>
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-4 flex items-center justify-between">
                                <div className="p-2.5 bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-400 rounded-xl">
                                  <Package className="w-5 h-5" />
                                </div>
                                <div className="text-end">
                                  <p className="text-[10px] text-muted-foreground mb-0.5">عدد الطلبات</p>
                                  <p className="text-xl font-bold text-foreground font-mono">24</p>
                                  <p className="text-[9px] text-muted-foreground">طلب</p>
                                </div>
                              </CardContent>
                            </Card>
                          </div>

                          {/* Last Interaction Counter */}
                          {timeSince && (
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm overflow-hidden">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <div className="p-2 bg-cyan-100 dark:bg-primary/15 rounded-lg">
                                      <Timer className="w-4 h-4 text-cyan-600 dark:text-primary" />
                                    </div>
                                    <div>
                                      <p className="text-xs font-bold text-slate-700 dark:text-white">آخر تعامل / منذ آخر فاتورة</p>
                                      <p className="text-[10px] text-muted-foreground">{format(new Date(data.lastInvoiceDate), "dd MMMM yyyy", { locale: ar })}</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3" dir="ltr">
                                    {timeSince.years > 0 && (
                                      <div className="text-center">
                                        <p className="text-lg font-bold text-primary font-mono">{timeSince.years}</p>
                                        <p className="text-[9px] text-muted-foreground">سنة</p>
                                      </div>
                                    )}
                                    <div className="text-center">
                                      <p className="text-lg font-bold text-primary font-mono">{timeSince.months}</p>
                                      <p className="text-[9px] text-muted-foreground">شهر</p>
                                    </div>
                                    <div className="text-center">
                                      <p className="text-lg font-bold text-foreground font-mono">{timeSince.days}</p>
                                      <p className="text-[9px] text-muted-foreground">يوم</p>
                                    </div>
                                    <div className="text-center">
                                      <p className="text-lg font-bold text-muted-foreground font-mono">{timeSince.hours}</p>
                                      <p className="text-[9px] text-muted-foreground">ساعة</p>
                                    </div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          )}

                          {/* Preferences & Most Purchased */}
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {/* Customer Preferences */}
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardHeader className="pb-3 border-b border-slate-50 dark:border-white/5">
                                <CardTitle className="text-sm font-bold flex items-center gap-2">
                                  <Star className="w-4 h-4 text-primary" /> تفضيلات العميل
                                </CardTitle>
                              </CardHeader>
                              <CardContent className="pt-4 space-y-3">
                                {[
                                  { label: "العطر المفضل", value: data.favoriteFragrance },
                                  { label: "الوقت المفضل للتسوق", value: data.preferredShoppingTime },
                                  { label: "متوسط السلة", value: `${data.avgBasketValue} ر.س` },
                                ].map((item, i) => (
                                  <div key={i} className="flex justify-between items-center text-sm">
                                    <span className="font-bold text-cyan-600 dark:text-primary text-sm">{item.value}</span>
                                    <span className="text-xs text-muted-foreground">{item.label}</span>
                                  </div>
                                ))}
                              </CardContent>
                            </Card>

                            {/* Most Purchased Items */}
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardHeader className="pb-3 border-b border-slate-50 dark:border-white/5">
                                <CardTitle className="text-sm font-bold flex items-center gap-2">
                                  <TrendingUp className="w-4 h-4 text-primary" /> الأكثر شراءً
                                </CardTitle>
                              </CardHeader>
                              <CardContent className="pt-4 space-y-2">
                                {data.topItems.slice(0, 4).map((item, i) => (
                                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-50/50 dark:bg-white/[0.02] border border-slate-100 dark:border-white/5">
                                    <div className="flex items-center gap-2">
                                      <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px] font-bold">#{i + 1}</span>
                                      <span className="text-xs font-medium text-foreground">{item.name}</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                      <span className="text-[10px] text-muted-foreground">{item.quantity} قطعة</span>
                                      <span className="text-xs font-bold text-primary font-mono">{item.totalSpent.toLocaleString()} ر.س</span>
                                    </div>
                                  </div>
                                ))}
                              </CardContent>
                            </Card>
                          </div>

                          {/* Branches */}
                          {data.branches.length > 0 && (
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardHeader className="pb-3 border-b border-slate-50 dark:border-white/5">
                                <CardTitle className="text-sm font-bold flex items-center gap-2">
                                  <Building className="w-4 h-4 text-primary" /> الفروع
                                </CardTitle>
                              </CardHeader>
                              <CardContent className="pt-4">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                  {data.branches.map((branch, i) => (
                                    <div key={i} className="p-3 rounded-lg bg-slate-50/50 dark:bg-white/[0.02] border border-slate-100 dark:border-white/5">
                                      <p className="text-xs font-bold text-foreground mb-1">{branch.name}</p>
                                      <div className="space-y-1">
                                        <p className="text-[10px] text-muted-foreground flex items-center gap-1.5"><MapPin className="w-3 h-3" /> {branch.location}</p>
                                        <p className="text-[10px] text-muted-foreground flex items-center gap-1.5"><User className="w-3 h-3" /> {branch.manager}</p>
                                        <p className="text-[10px] text-muted-foreground flex items-center gap-1.5 font-mono" dir="ltr"><Phone className="w-3 h-3" /> {branch.phone}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>
                          )}

                          {/* Activity Timeline */}
                          <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                            <CardHeader className="pb-3 border-b border-slate-50 dark:border-white/5">
                              <CardTitle className="text-sm font-bold flex items-center gap-2">
                                <Activity className="w-4 h-4 text-primary" /> الجدول الزمني للنشاط
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-4">
                              <div className="space-y-4 relative">
                                <div className="absolute end-[13px] top-2 bottom-2 w-0.5 bg-slate-100 dark:bg-white/5" />
                                {data.activities.map((act, i) => (
                                  <div key={act.id} className="flex gap-3 relative group">
                                    <div className="w-7 h-7 rounded-full bg-cyan-100 dark:bg-primary/15 text-cyan-600 dark:text-primary flex items-center justify-center ring-4 ring-white dark:ring-[#1a1d24] z-10 shrink-0 group-hover:scale-110 transition-transform">
                                      {getActivityIcon(act.type)}
                                    </div>
                                    <div className="flex-1 pb-3">
                                      <p className="text-xs font-medium text-foreground group-hover:text-primary transition-colors">{act.description}</p>
                                      <div className="flex items-center gap-2 mt-0.5">
                                        <p className="text-[10px] text-muted-foreground">{format(new Date(act.date), "dd MMM yyyy - HH:mm", { locale: ar })}</p>
                                        {act.user && <span className="text-[9px] bg-slate-100 dark:bg-white/5 text-muted-foreground px-1.5 py-0.5 rounded">{act.user}</span>}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      )}

                      {/* ═══════ CALLS TAB ═══════ */}
                      {activeTab === "calls" && (
                        <div className="space-y-3">
                          {data.callLog.map((call) => (
                            <Card key={call.id} className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm overflow-hidden">
                              <CardContent className="p-0">
                                <button
                                  className="w-full p-4 text-start flex items-center gap-4 hover:bg-slate-50/50 dark:hover:bg-white/[0.02] transition-colors"
                                  onClick={() => setExpandedCall(expandedCall === call.id ? null : call.id)}
                                >
                                  <div className={`p-2 rounded-lg shrink-0 ${
                                    call.type === "inbound" ? "bg-green-100 dark:bg-green-500/10 text-green-600 dark:text-green-400" :
                                    call.type === "outbound" ? "bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400" :
                                    "bg-red-100 dark:bg-red-500/10 text-red-600 dark:text-red-400"
                                  }`}>
                                    {call.type === "inbound" ? <PhoneIncoming className="w-4 h-4" /> :
                                     call.type === "outbound" ? <PhoneOutgoing className="w-4 h-4" /> :
                                     <Phone className="w-4 h-4" />}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-0.5">
                                      <p className="text-xs font-bold text-foreground">{call.type === "inbound" ? "مكالمة واردة" : call.type === "outbound" ? "مكالمة صادرة" : "مكالمة فائتة"}</p>
                                      <span className="text-[9px] bg-slate-100 dark:bg-white/5 text-muted-foreground px-1.5 py-0.5 rounded">{call.duration}</span>
                                    </div>
                                    <p className="text-[10px] text-muted-foreground">{call.date} • {call.time} • {call.agent}</p>
                                  </div>
                                  <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${expandedCall === call.id ? "rotate-180" : ""}`} />
                                </button>

                                <AnimatePresence>
                                  {expandedCall === call.id && (
                                    <motion.div
                                      initial={{ height: 0, opacity: 0 }}
                                      animate={{ height: "auto", opacity: 1 }}
                                      exit={{ height: 0, opacity: 0 }}
                                      transition={{ duration: 0.2 }}
                                      className="overflow-hidden"
                                    >
                                      <div className="px-4 pb-4 border-t border-slate-50 dark:border-white/5 pt-3 space-y-3">
                                        <div>
                                          <p className="text-[10px] text-muted-foreground font-medium mb-1">ملاحظات</p>
                                          <p className="text-xs text-foreground bg-slate-50 dark:bg-white/[0.03] p-2.5 rounded-lg border border-slate-100 dark:border-white/5">{call.notes}</p>
                                        </div>
                                        <div>
                                          <p className="text-[10px] text-muted-foreground font-medium mb-1">الإجراء المتخذ</p>
                                          <p className="text-xs text-foreground">{call.action}</p>
                                        </div>
                                        {call.aiSummary && (
                                          <div className="bg-primary/5 dark:bg-primary/10 border border-primary/10 dark:border-primary/20 rounded-lg p-3">
                                            <p className="text-[10px] text-primary font-medium mb-1 flex items-center gap-1"><Sparkles className="w-3 h-3" /> ملخص الذكاء الاصطناعي</p>
                                            <p className="text-xs text-foreground">{call.aiSummary}</p>
                                          </div>
                                        )}
                                      </div>
                                    </motion.div>
                                  )}
                                </AnimatePresence>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}

                      {/* ═══════ FINANCIAL TAB ═══════ */}
                      {activeTab === "financial" && (
                        <div className="space-y-6">
                          {/* Payment Summary */}
                          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-3.5 text-center">
                                <p className="text-[10px] text-muted-foreground mb-1">إجمالي المدفوع</p>
                                <p className="text-lg font-bold text-primary font-mono">{data.paymentTrends.totalPaid.toLocaleString()}</p>
                                <p className="text-[9px] text-muted-foreground">ر.س</p>
                              </CardContent>
                            </Card>
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-3.5 text-center">
                                <p className="text-[10px] text-muted-foreground mb-1">فواتير متأخرة</p>
                                <p className={`text-lg font-bold font-mono ${data.paymentTrends.overdueCount > 0 ? "text-red-500" : "text-green-500"}`}>{data.paymentTrends.overdueCount}</p>
                                <p className="text-[9px] text-muted-foreground">فاتورة</p>
                              </CardContent>
                            </Card>
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-3.5 text-center">
                                <p className="text-[10px] text-muted-foreground mb-1">الخصومات المطبقة</p>
                                <p className="text-lg font-bold text-foreground font-mono">{data.paymentTrends.discountsApplied}</p>
                                <p className="text-[9px] text-muted-foreground">خصم</p>
                              </CardContent>
                            </Card>
                            <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                              <CardContent className="p-3.5 text-center">
                                <p className="text-[10px] text-muted-foreground mb-1">متوسط أيام السداد</p>
                                <p className="text-lg font-bold text-foreground font-mono">{data.paymentTrends.avgPaymentDays}</p>
                                <p className="text-[9px] text-muted-foreground">يوم</p>
                              </CardContent>
                            </Card>
                          </div>

                          {/* Payment Records */}
                          <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                            <CardHeader className="pb-3 border-b border-slate-50 dark:border-white/5">
                              <CardTitle className="text-sm font-bold flex items-center gap-2">
                                <CreditCard className="w-4 h-4 text-primary" /> سجل المدفوعات
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-4 space-y-2">
                              {data.payments.map((pay) => (
                                <div key={pay.id} className="p-3 rounded-lg bg-slate-50/50 dark:bg-white/[0.02] border border-slate-100 dark:border-white/5 hover:border-primary/20 transition-colors">
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs font-bold text-foreground">{pay.amount.toLocaleString()} ر.س</span>
                                      <Badge className={`text-[9px] px-1.5 py-0 border ${getStatusColor(pay.status)}`}>{pay.status}</Badge>
                                    </div>
                                    <span className="text-[10px] font-mono text-muted-foreground">{pay.id}</span>
                                  </div>
                                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[10px] text-muted-foreground">
                                    <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {pay.date}</span>
                                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {pay.time}</span>
                                    <span className="flex items-center gap-1"><User className="w-3 h-3" /> {pay.user}</span>
                                    <span className="flex items-center gap-1"><Store className="w-3 h-3" /> {pay.source}</span>
                                  </div>
                                  <div className="flex items-center gap-2 mt-1.5">
                                    <span className="text-[9px] bg-slate-100 dark:bg-white/5 text-muted-foreground px-1.5 py-0.5 rounded">{pay.method}</span>
                                    <span className="text-[9px] text-muted-foreground">فاتورة: {pay.invoiceId}</span>
                                  </div>
                                </div>
                              ))}
                            </CardContent>
                          </Card>

                          {/* Past Invoices */}
                          <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                            <CardHeader className="pb-3 border-b border-slate-50 dark:border-white/5">
                              <CardTitle className="text-sm font-bold flex items-center gap-2">
                                <Receipt className="w-4 h-4 text-primary" /> الفواتير
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-4 space-y-2">
                              {data.invoices.map((inv) => (
                                <div key={inv.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-50/50 dark:bg-white/[0.02] border border-slate-100 dark:border-white/5 hover:border-primary/20 transition-colors group">
                                  <div className="flex items-center gap-3">
                                    <div className="p-2 bg-slate-100 dark:bg-white/5 rounded-lg">
                                      <Receipt className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                                    </div>
                                    <div>
                                      <p className="text-xs font-bold text-foreground font-mono">{inv.id}</p>
                                      <p className="text-[10px] text-muted-foreground">{inv.date} • {inv.items} عناصر</p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <Badge className={`text-[9px] px-1.5 py-0 border ${getStatusColor(inv.status)}`}>{inv.status}</Badge>
                                    <span className="text-xs font-bold text-foreground font-mono">{inv.amount.toLocaleString()} ر.س</span>
                                    <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                                      <Eye className="w-3.5 h-3.5" />
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </CardContent>
                          </Card>
                        </div>
                      )}

                      {/* ═══════ SAMPLES TAB ═══════ */}
                      {activeTab === "samples" && (
                        <div className="space-y-4">
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {data.samples.map((sample) => (
                              <Card
                                key={sample.id}
                                className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm overflow-hidden cursor-pointer hover:shadow-md hover:border-primary/20 transition-all group"
                                onClick={() => setExpandedSample(expandedSample === sample.id ? null : sample.id)}
                              >
                                <div className="h-32 bg-slate-100 dark:bg-white/5 overflow-hidden relative">
                                  <ImageWithFallback
                                    src={sample.image}
                                    alt={sample.name}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                  />
                                  <div className="absolute top-2 start-2">
                                    <Badge className="bg-primary/90 text-primary-foreground text-[9px] px-1.5 py-0 border-none shadow-sm">
                                      {sample.version}
                                    </Badge>
                                  </div>
                                </div>
                                <CardContent className="p-3">
                                  <p className="text-xs font-bold text-foreground mb-1">{sample.name}</p>
                                  <div className="flex items-center justify-between">
                                    <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                                      <Calendar className="w-3 h-3" /> {format(new Date(sample.dateSent), "dd MMM yyyy", { locale: ar })}
                                    </span>
                                    <span className="text-[9px] font-mono text-muted-foreground">{sample.id}</span>
                                  </div>
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                          {data.samples.length === 0 && (
                            <div className="text-center py-12 text-muted-foreground">
                              <Box className="w-12 h-12 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
                              <p className="text-sm">لم يتم إرسال عينات لهذا العميل</p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* ═══════ TICKETS TAB ═══════ */}
                      {activeTab === "tickets" && (
                        <div className="space-y-3">
                          {data.tickets.map((ticket) => (
                            <Card key={ticket.id} className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm hover:border-primary/20 transition-colors">
                              <CardContent className="p-4">
                                <div className="flex items-start justify-between gap-3">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                      <span className="text-[10px] font-mono text-muted-foreground bg-slate-100 dark:bg-white/5 px-1.5 py-0.5 rounded">{ticket.id}</span>
                                      <Badge className={`text-[9px] px-1.5 py-0 border ${getStatusColor(ticket.status)}`}>{ticket.status}</Badge>
                                      <Badge className={`text-[9px] px-1.5 py-0 border ${getPriorityColor(ticket.priority)}`}>{ticket.priority}</Badge>
                                    </div>
                                    <p className="text-xs font-bold text-foreground mb-1">{ticket.subject}</p>
                                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                                      <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {ticket.date}</span>
                                      <span className="flex items-center gap-1"><User className="w-3 h-3" /> {ticket.assignedTo}</span>
                                    </div>
                                  </div>
                                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary shrink-0">
                                    <Eye className="w-3.5 h-3.5" />
                                  </Button>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                          {data.tickets.length === 0 && (
                            <div className="text-center py-12 text-muted-foreground">
                              <Ticket className="w-12 h-12 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
                              <p className="text-sm">لا توجد تذاكر لهذا العميل</p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* ═══════ NOTES TAB ═══════ */}
                      {activeTab === "notes" && (
                        <div className="space-y-4">
                          {/* Add Note */}
                          <Card className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm">
                            <CardContent className="p-4">
                              <Textarea
                                placeholder="أضف ملاحظة جديدة..."
                                className="mb-3 text-xs bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:border-white/10 min-h-[60px] resize-none"
                                value={newNoteText}
                                onChange={(e) => setNewNoteText(e.target.value)}
                              />
                              <div className="flex items-center justify-between">
                                <div className="flex gap-1.5">
                                  {(["yellow", "pink", "green", "blue", "purple"] as const).map(c => (
                                    <button
                                      key={c}
                                      onClick={() => setSelectedNoteColor(c)}
                                      className={`w-5 h-5 rounded-full border-2 shadow-sm transition-all ${
                                        selectedNoteColor === c
                                          ? "ring-2 ring-primary ring-offset-1 ring-offset-background scale-110"
                                          : "border-white dark:border-[#1a1d24]"
                                      } ${
                                        c === "yellow" ? "bg-yellow-300" :
                                        c === "pink" ? "bg-pink-300" :
                                        c === "green" ? "bg-green-300" :
                                        c === "blue" ? "bg-blue-300" :
                                        "bg-purple-300"
                                      }`}
                                    />
                                  ))}
                                </div>
                                <Button
                                  size="sm"
                                  className="h-7 text-[11px] rounded-lg gap-1.5 bg-cyan-500 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] text-white border-none"
                                  disabled={!newNoteText.trim()}
                                  onClick={handleAddNote}
                                >
                                  <Plus className="w-3 h-3" /> إضافة ملاحظة
                                </Button>
                              </div>
                            </CardContent>
                          </Card>

                          {/* Sticky Notes Grid */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {[...addedNotes, ...data.notes].map((note) => (
                              <div key={note.id} className={`p-4 rounded-xl border-2 shadow-sm relative ${stickyNoteColors[note.color]}`}>
                                <div className={`absolute top-0 end-4 w-3 h-6 rounded-b-sm ${
                                  note.color === "yellow" ? "bg-yellow-400/50" :
                                  note.color === "pink" ? "bg-pink-400/50" :
                                  note.color === "green" ? "bg-green-400/50" :
                                  note.color === "blue" ? "bg-blue-400/50" :
                                  "bg-purple-400/50"
                                }`} />
                                <p className="text-xs text-foreground leading-relaxed mb-3 pt-2">{note.text}</p>
                                <div className="flex items-center justify-between">
                                  <span className="text-[10px] text-muted-foreground flex items-center gap-1"><User className="w-3 h-3" /> {note.author}</span>
                                  <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {format(new Date(note.date), "dd MMM yyyy", { locale: ar })}
                                    <span className="opacity-50">·</span>
                                    {format(new Date(note.date), "hh:mm a", { locale: ar })}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* ═══════ FOLLOW-UPS TAB ═══════ */}
                      {activeTab === "followups" && (
                        <div className="space-y-4">
                          {/* Add Follow-up */}
                          <Card className="bg-primary/5 dark:bg-primary/5 border-primary/10 dark:border-primary/15 shadow-sm">
                            <CardContent className="p-4 flex items-center gap-3">
                              <div className="p-2 bg-primary/10 dark:bg-primary/15 rounded-lg">
                                <Bell className="w-4 h-4 text-primary" />
                              </div>
                              <div className="flex-1">
                                <p className="text-xs font-bold text-foreground">تعيين متابعة جديدة</p>
                                <p className="text-[10px] text-muted-foreground">يمكن للمدراء تعيين متابعات تظهر في قائمة المهام للموظفين</p>
                              </div>
                              <Button size="sm" className="h-8 text-[11px] rounded-lg gap-1.5 bg-cyan-500 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] text-white border-none">
                                <Plus className="w-3 h-3" /> متابعة جديدة
                              </Button>
                            </CardContent>
                          </Card>

                          {/* Follow-up Cards */}
                          {data.followUps.map((fu) => (
                            <Card key={fu.id} className="bg-white dark:bg-[#1a1d24] border-slate-100 dark:border-white/5 shadow-sm hover:border-primary/20 transition-colors overflow-hidden">
                              <div className={`h-1 ${
                                fu.priority === "عاجل" ? "bg-red-500" :
                                fu.priority === "عالي" ? "bg-yellow-500" :
                                fu.priority === "متوسط" ? "bg-blue-500" :
                                "bg-slate-300"
                              }`} />
                              <CardContent className="p-4">
                                <div className="flex items-start justify-between gap-3 mb-3">
                                  <div>
                                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                                      <p className="text-xs font-bold text-foreground">{fu.title}</p>
                                      <Badge className={`text-[9px] px-1.5 py-0 border ${getPriorityColor(fu.priority)}`}>{fu.priority}</Badge>
                                      <Badge className={`text-[9px] px-1.5 py-0 border ${getStatusColor(fu.status)}`}>{fu.status}</Badge>
                                    </div>
                                    <p className="text-[11px] text-muted-foreground">{fu.description}</p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-4 text-[10px] text-muted-foreground flex-wrap">
                                  <span className="flex items-center gap-1"><CalendarCheck className="w-3 h-3" /> الموعد: {format(new Date(fu.dueDate), "dd MMM yyyy", { locale: ar })}</span>
                                  <span className="flex items-center gap-1"><UserCheck className="w-3 h-3" /> مُعيّن إلى: <span className="font-medium text-foreground">{fu.assignedTo}</span></span>
                                  <span className="flex items-center gap-1"><User className="w-3 h-3" /> بواسطة: {fu.assignedBy}</span>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}

                      {/* ═══════ ATTACHMENTS TAB ═══════ */}
                      {activeTab === "attachments" && (
                        <div className="space-y-4">
                          {/* Upload Area */}
                          <div className="border-2 border-dashed border-slate-200 dark:border-white/10 rounded-xl p-6 text-center hover:border-primary/30 transition-colors cursor-pointer group">
                            <Download className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto mb-2 group-hover:text-primary transition-colors rotate-180" />
                            <p className="text-xs text-muted-foreground">اسحب الملفات هنا أو اضغط للرفع</p>
                            <p className="text-[10px] text-muted-foreground mt-1">PDF, JPG, PNG - حد أقصى 10MB</p>
                          </div>

                          {/* Attachment List */}
                          <div className="space-y-2">
                            {data.attachments.map((att) => (
                              <div key={att.id} className="flex items-center justify-between p-3 rounded-lg bg-white dark:bg-[#1a1d24] border border-slate-100 dark:border-white/5 hover:border-primary/20 transition-colors group">
                                <div className="flex items-center gap-3">
                                  <div className="p-2 bg-slate-100 dark:bg-white/5 rounded-lg">
                                    {att.type === "هوية" ? <BadgeCheck className="w-4 h-4 text-blue-500" /> :
                                     att.type === "وثيقة" ? <FileText className="w-4 h-4 text-green-500" /> :
                                     <ClipboardList className="w-4 h-4 text-purple-500" />}
                                  </div>
                                  <div>
                                    <p className="text-xs font-bold text-foreground">{att.name}</p>
                                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                      <span>{att.type}</span>
                                      <span>•</span>
                                      <span>{att.size}</span>
                                      <span>•</span>
                                      <span>{att.date}</span>
                                      <span>•</span>
                                      <span>{att.uploadedBy}</span>
                                    </div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                                    <Eye className="w-3.5 h-3.5" />
                                  </Button>
                                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                                    <Download className="w-3.5 h-3.5" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </ScrollArea>
            </div>
          </div>
        </div>
      </DialogContent>

      {/* Invoice Creation — wired to POS Bridge API */}
      <InvoiceCreationContainer
        open={showInvoiceDialog}
        onClose={() => setShowInvoiceDialog(false)}
        customerName={data.name}
        customerId={data.id}
        customerAddress={`${data.address.city}، ${data.address.district}، ${data.address.street}`}
        customerPhone={data.phones[0]?.number}
      />
    </Dialog>
  );
}
