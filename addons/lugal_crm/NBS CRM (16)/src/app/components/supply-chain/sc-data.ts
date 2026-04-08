// ── Supply Chain Types ──────────────────────────────

export type Division = "europe" | "china";
export type Currency = "USD" | "EUR" | "CNY" | "SAR" | "IQD";

export const currencyLabels: Record<Currency, string> = {
  USD: "دولار أمريكي",
  EUR: "يورو",
  CNY: "يوان صيني",
  SAR: "ريال سعودي",
  IQD: "دينار عراقي",
};
export const currencySymbols: Record<Currency, string> = {
  USD: "$",
  EUR: "\u20AC",
  CNY: "\u00A5",
  SAR: "ر.س",
  IQD: "د.ع",
};

export interface Supplier {
  id: string;
  name: string;
  nameEn: string;
  division: Division;
  country: string;
  contactPerson: string;
  contactRole: string;
  phone: string;
  email: string;
  whatsapp?: string;
  wechat?: string;
  address: string;
  currency: Currency;
  avatar: string;
  tags: string[];
  totalOrders: number;
  totalValue: number;
  rating: number;
  status: "active" | "inactive";
  authorizedRep: string;
  notes: string;
}

export interface POItem {
  id: string;
  name: string;
  size: string;
  qty: number;
  unitPrice: number;
  previousPrice?: number;
  cbm?: number;
  weight?: number;
  category: "perfume" | "glass" | "alcohol" | "aluminium" | "other";
}

export interface PurchaseOrder {
  id: string;
  supplierId: string;
  supplierName: string;
  division: Division;
  currency: Currency;
  status: "draft" | "sent" | "confirmed" | "shipped" | "received" | "cancelled";
  items: POItem[];
  totalAmount: number;
  createdAt: string;
  updatedAt: string;
  containerNumber?: string;
  notes: string;
  hasPackingList: boolean;
  createdBy: string;
  dueDate?: string;
}

export interface PackingListItem {
  id: string;
  name: string;
  size: string;
  qty: number;
  cbm: number;
  weight: number;
  category: string;
}

export interface ContainerComment {
  id: string;
  user: string;
  date: string;
  text: string;
}

export interface ContainerAttachment {
  id: string;
  name: string;
  type: string;
  uploadedBy: string;
  uploadedAt: string;
  size: string;
}

export interface Container {
  id: string;
  name: string;
  containerNumber: string;
  type: "20ft" | "40ft" | "40ft-hc";
  status: "active" | "at-port" | "completed" | "arriving-soon";
  departureLocation: string;
  departureDate: string;
  expectedArrival: string;
  blNumber: string;
  invoiceNumber: string;
  containerType: "perfume" | "glass" | "alcohol" | "mixed";
  tags: string[];
  clearanceCompanyId: string;
  clearanceCompanyName: string;
  clearanceDuration: string;
  gracePeriod: string;
  currentLocation: string;
  documentsDelivered: boolean;
  driver?: string;
  driverPhone?: string;
  purchaseOrderIds: string[];
  penalties: { amount: number; reason: string; date: string }[];
  comments: ContainerComment[];
  attachments: ContainerAttachment[];
  reminderDate?: string;
  division: Division;
}

export interface ClearanceCompany {
  id: string;
  name: string;
  address: string;
  email: string;
  phone: string;
  authorizedRep: string;
  activeContainers: number;
  completedContainers: number;
  financialBalance: number;
  financialCurrency: Currency;
  paymentTerms: string;
}

export interface ItemRequest {
  id: string;
  itemName: string;
  picture?: string;
  size: string;
  unit: "ml" | "kg";
  quantity: number;
  category: "perfume" | "glass" | "aluminium" | "mixed";
  division: Division;
  requestedBy: string;
  requestedAt: string;
  status: "pending" | "approved" | "ordered" | "rejected";
  notes: string;
}

export interface Negotiation {
  id: string;
  supplierId: string;
  supplierName: string;
  itemName: string;
  currentPrice: number;
  targetPrice: number;
  lastOffer: number;
  currency: Currency;
  status: "open" | "counter-offer" | "agreed" | "rejected";
  messages: { sender: string; text: string; date: string }[];
  division: Division;
}

export interface SCNotification {
  id: string;
  type: "reminder" | "container" | "po" | "request" | "negotiation";
  title: string;
  description: string;
  date: string;
  read: boolean;
  link?: string;
}

export interface SuggestedPO {
  id: string;
  itemName: string;
  category: "perfume" | "glass" | "alcohol" | "aluminium";
  avgAnnualSales: number;
  avgTop6MonthsSales: number;
  currentStock: number;
  suggestedQty: number;
  lastPrice: number;
  supplierId: string;
  supplierName: string;
}

export interface MinMaxItem {
  id: string;
  name: string;
  category: string;
  currentStock: number;
  minStock: number;
  maxStock: number;
}

export interface InternalMessage {
  id: string;
  sender: string;
  senderDivision: Division | "baghdad";
  recipients: string[];
  mentions: string[];
  text: string;
  date: string;
  channel: "internal" | "whatsapp" | "wechat" | "email";
  attachments?: string[];
}

export interface SystemUser {
  id: string;
  name: string;
  role: string;
  division: Division | "baghdad";
  avatar: string;
  online: boolean;
}

export interface SCEmail {
  id: string;
  from: string;
  to: string;
  subject: string;
  body: string;
  date: string;
  read: boolean;
  attachments: string[];
  relatedPO?: string;
  relatedContainer?: string;
}

// ── Mock Data ──────────────────────────────────────

export const suppliers: Supplier[] = [
  {
    id: "SUP-001",
    name: "مصنع الزهور الذهبية",
    nameEn: "Golden Flowers Factory",
    division: "china",
    country: "الصين",
    contactPerson: "وانغ لي",
    contactRole: "مدير التصدير",
    phone: "+86 139 0000 1234",
    email: "wang.li@goldenflowers.cn",
    wechat: "wangli_export",
    address: "قوانغتشو، مقاطعة قوانغدونغ",
    currency: "CNY",
    avatar: "زذ",
    tags: ["زجاجيات", "بلاستيك", "موثوق"],
    totalOrders: 45,
    totalValue: 285000,
    rating: 4.8,
    status: "active",
    authorizedRep: "وانغ لي",
    notes: "مورد رئيسي للزجاجيات — جودة ممتازة",
  },
  {
    id: "SUP-002",
    name: "Parfums de Grasse",
    nameEn: "Parfums de Grasse",
    division: "europe",
    country: "فرنسا",
    contactPerson: "جان بيير مارتان",
    contactRole: "مدير المبيعات",
    phone: "+33 4 93 00 1234",
    email: "jp.martin@grasse-parfums.fr",
    whatsapp: "+33493001234",
    address: "غراس، بروفانس، فرنسا",
    currency: "EUR",
    avatar: "PG",
    tags: ["عطور", "زيوت أساسية", "فاخر"],
    totalOrders: 32,
    totalValue: 520000,
    rating: 4.9,
    status: "active",
    authorizedRep: "جان بيير مارتان",
    notes: "أفضل جودة زيوت عطرية من غراس",
  },
  {
    id: "SUP-003",
    name: "شركة الكحول الصناعي",
    nameEn: "Industrial Alcohol Co.",
    division: "europe",
    country: "ألمانيا",
    contactPerson: "ماركوس فيشر",
    contactRole: "مدير العمليات",
    phone: "+49 69 0000 5678",
    email: "m.fischer@indal.de",
    whatsapp: "+4969000056781",
    address: "فرانكفورت، ألمانيا",
    currency: "EUR",
    avatar: "IA",
    tags: ["كحول", "مواد خام"],
    totalOrders: 18,
    totalValue: 95000,
    rating: 4.5,
    status: "active",
    authorizedRep: "ماركوس فيشر",
    notes: "كحول إيثيلي نقي بمعايير أوروبية",
  },
  {
    id: "SUP-004",
    name: "مصنع نينغبو للألمنيوم",
    nameEn: "Ningbo Aluminium Factory",
    division: "china",
    country: "الصين",
    contactPerson: "تشن وي",
    contactRole: "مسؤول المبيعات",
    phone: "+86 574 0000 4321",
    email: "chen.w@nbalu.cn",
    wechat: "chenwei_alu",
    address: "نينغبو، تشجيانغ، الصين",
    currency: "USD",
    avatar: "NA",
    tags: ["ألمنيوم", "أغطية", "تغليف"],
    totalOrders: 22,
    totalValue: 68000,
    rating: 4.3,
    status: "active",
    authorizedRep: "تشن وي",
    notes: "متخصص في أغطية الألمنيوم والتغليف",
  },
];

export const purchaseOrders: PurchaseOrder[] = [
  {
    id: "PO-2026-001",
    supplierId: "SUP-001",
    supplierName: "مصنع الزهور الذهبية",
    division: "china",
    currency: "CNY",
    status: "shipped",
    items: [
      { id: "pi1", name: "قارورة كريستال 100مل", size: "100ml", qty: 5000, unitPrice: 4.5, previousPrice: 4.2, cbm: 2.8, weight: 850, category: "glass" },
      { id: "pi2", name: "زجاجة عطر ذهبية 50مل", size: "50ml", qty: 8000, unitPrice: 3.2, previousPrice: 3.5, cbm: 3.2, weight: 640, category: "glass" },
      { id: "pi3", name: "عبوة رذاذ فاخرة 30مل", size: "30ml", qty: 10000, unitPrice: 2.1, previousPrice: 2.1, cbm: 2.5, weight: 500, category: "glass" },
    ],
    totalAmount: 69100,
    createdAt: "2026-01-15",
    updatedAt: "2026-02-10",
    containerNumber: "CSLU2345678",
    notes: "شحنة زجاجيات Q1 — تم الشحن",
    hasPackingList: true,
    createdBy: "أحمد المالكي",
    dueDate: "2026-03-01",
  },
  {
    id: "PO-2026-002",
    supplierId: "SUP-002",
    supplierName: "Parfums de Grasse",
    division: "europe",
    currency: "EUR",
    status: "confirmed",
    items: [
      { id: "pi4", name: "زيت عود طبيعي", size: "1kg", qty: 10, unitPrice: 2800, previousPrice: 2650, cbm: 0.05, weight: 12, category: "perfume" },
      { id: "pi5", name: "زيت مسك أبيض", size: "500g", qty: 20, unitPrice: 450, previousPrice: 480, cbm: 0.08, weight: 12, category: "perfume" },
      { id: "pi6", name: "زيت ورد بلغاري", size: "250g", qty: 15, unitPrice: 1200, previousPrice: 1200, cbm: 0.04, weight: 5, category: "perfume" },
    ],
    totalAmount: 55000,
    createdAt: "2026-02-01",
    updatedAt: "2026-02-15",
    notes: "طلب زيوت عطرية فاخرة — بانتظار الشحن",
    hasPackingList: false,
    createdBy: "سارة النعيمي",
    dueDate: "2026-03-15",
  },
  {
    id: "PO-2026-003",
    supplierId: "SUP-003",
    supplierName: "شركة الكحول الصناعي",
    division: "europe",
    currency: "EUR",
    status: "draft",
    items: [
      { id: "pi7", name: "كحول إيثيلي نقي 96%", size: "200L", qty: 10, unitPrice: 320, previousPrice: 300, cbm: 2.2, weight: 1600, category: "alcohol" },
      { id: "pi8", name: "DPG - ديبروبيلين غلايكول", size: "25kg", qty: 20, unitPrice: 85, previousPrice: 90, cbm: 0.6, weight: 500, category: "alcohol" },
    ],
    totalAmount: 4900,
    createdAt: "2026-02-20",
    updatedAt: "2026-02-20",
    notes: "مسودة — بحاجة مراجعة الأسعار",
    hasPackingList: false,
    createdBy: "أحمد المالكي",
  },
  {
    id: "PO-2026-004",
    supplierId: "SUP-004",
    supplierName: "مصنع نينغبو للألمنيوم",
    division: "china",
    currency: "USD",
    status: "sent",
    items: [
      { id: "pi9", name: "غطاء ألمنيوم ذهبي 50مل", size: "50ml cap", qty: 15000, unitPrice: 0.35, previousPrice: 0.32, cbm: 1.8, weight: 300, category: "aluminium" },
      { id: "pi10", name: "غطاء ألمنيوم فضي 100مل", size: "100ml cap", qty: 10000, unitPrice: 0.45, previousPrice: 0.45, cbm: 1.5, weight: 250, category: "aluminium" },
    ],
    totalAmount: 9750,
    createdAt: "2026-02-18",
    updatedAt: "2026-02-19",
    containerNumber: "",
    notes: "بانتظار تأكيد المورد",
    hasPackingList: false,
    createdBy: "سارة النعيمي",
  },
];

export const containers: Container[] = [
  {
    id: "CNT-001",
    name: "شحنة زجاجيات Q1",
    containerNumber: "CSLU2345678",
    type: "40ft",
    status: "active",
    departureLocation: "ميناء شنغهاي، الصين",
    departureDate: "2026-02-10",
    expectedArrival: "2026-03-12",
    blNumber: "BL-2026-00145",
    invoiceNumber: "INV-GF-2026-012",
    containerType: "glass",
    tags: ["زجاجيات", "Q1", "عاجل"],
    clearanceCompanyId: "CLR-001",
    clearanceCompanyName: "شركة الفجر للتخليص",
    clearanceDuration: "5-7 أيام",
    gracePeriod: "14 يوم",
    currentLocation: "بحر العرب — 65% من المسار",
    documentsDelivered: true,
    driver: "علي حسن",
    driverPhone: "+964 770 123 4567",
    purchaseOrderIds: ["PO-2026-001"],
    penalties: [],
    comments: [
      { id: "c1", user: "أحمد المالكي", date: "2026-02-12", text: "تم تأكيد الشحن من المورد" },
      { id: "c2", user: "سارة النعيمي", date: "2026-02-15", text: "تم إرسال المستندات للمخلص" },
    ],
    attachments: [
      { id: "a1", name: "بوليصة الشحن.pdf", type: "pdf", uploadedBy: "أحمد المالكي", uploadedAt: "2026-02-11", size: "2.4 MB" },
      { id: "a2", name: "فاتورة المورد.pdf", type: "pdf", uploadedBy: "سارة النعيمي", uploadedAt: "2026-02-12", size: "1.8 MB" },
    ],
    reminderDate: "2026-03-10",
    division: "china",
  },
  {
    id: "CNT-002",
    name: "شحنة عطور فرنسية",
    containerNumber: "MSKU9876543",
    type: "20ft",
    status: "arriving-soon",
    departureLocation: "ميناء مرسيليا، فرنسا",
    departureDate: "2026-01-28",
    expectedArrival: "2026-02-25",
    blNumber: "BL-2026-00098",
    invoiceNumber: "INV-PG-2026-008",
    containerType: "perfume",
    tags: ["عطور", "زيوت", "فاخر"],
    clearanceCompanyId: "CLR-001",
    clearanceCompanyName: "شركة الفجر للتخليص",
    clearanceDuration: "3-5 أيام",
    gracePeriod: "7 أيام",
    currentLocation: "قناة السويس — 90% من المسار",
    documentsDelivered: true,
    purchaseOrderIds: ["PO-2026-002"],
    penalties: [],
    comments: [
      { id: "c3", user: "سارة النعيمي", date: "2026-02-20", text: "الحاوية ستصل خلال أيام — جاهزية المخلص مؤكدة" },
    ],
    attachments: [
      { id: "a3", name: "شهادة المنشأ.pdf", type: "pdf", uploadedBy: "سارة النعيمي", uploadedAt: "2026-01-30", size: "1.2 MB" },
    ],
    reminderDate: "2026-02-24",
    division: "europe",
  },
  {
    id: "CNT-003",
    name: "شحنة ألمنيوم Q4-2025",
    containerNumber: "TGHU1234567",
    type: "20ft",
    status: "completed",
    departureLocation: "ميناء نينغبو، الصين",
    departureDate: "2025-11-15",
    expectedArrival: "2025-12-20",
    blNumber: "BL-2025-00312",
    invoiceNumber: "INV-NA-2025-045",
    containerType: "mixed",
    tags: ["ألمنيوم", "أغطية", "Q4"],
    clearanceCompanyId: "CLR-002",
    clearanceCompanyName: "مؤسسة الأمين للتخليص",
    clearanceDuration: "4 أيام",
    gracePeriod: "14 يوم",
    currentLocation: "تم التسليم",
    documentsDelivered: true,
    driver: "محمد عباس",
    driverPhone: "+964 771 987 6543",
    purchaseOrderIds: [],
    penalties: [
      { amount: 150, reason: "تأخر يوم واحد في التفريغ", date: "2025-12-22" },
    ],
    comments: [
      { id: "c4", user: "أحمد المالكي", date: "2025-12-21", text: "تم الاستلام بنجاح — غرامة تأخر بسيطة" },
    ],
    attachments: [],
    division: "china",
  },
  {
    id: "CNT-004",
    name: "شحنة كحول صناعي",
    containerNumber: "OOLU5678901",
    type: "20ft",
    status: "at-port",
    departureLocation: "ميناء هامبورغ، ألمانيا",
    departureDate: "2026-01-10",
    expectedArrival: "2026-02-18",
    blNumber: "BL-2026-00067",
    invoiceNumber: "INV-IA-2026-003",
    containerType: "alcohol",
    tags: ["كحول", "مواد خام", "خطر"],
    clearanceCompanyId: "CLR-001",
    clearanceCompanyName: "شركة الفجر للتخليص",
    clearanceDuration: "7-10 أيام",
    gracePeriod: "10 أيام",
    currentLocation: "ميناء أم قصر — بانتظار التخليص",
    documentsDelivered: false,
    purchaseOrderIds: [],
    penalties: [],
    comments: [
      { id: "c5", user: "أحمد المالكي", date: "2026-02-19", text: "بحاجة لإرسال المستندات للمخلص فوراً!" },
    ],
    attachments: [],
    reminderDate: "2026-02-23",
    division: "europe",
  },
];

export const clearanceCompanies: ClearanceCompany[] = [
  {
    id: "CLR-001",
    name: "شركة الفجر للتخليص الجمركي",
    address: "البصرة، شارع المعقل، مبنى رقم 45",
    email: "info@alfajr-clearance.iq",
    phone: "+964 780 111 2222",
    authorizedRep: "حسين كريم المالكي",
    activeContainers: 3,
    completedContainers: 28,
    financialBalance: 5000,
    financialCurrency: "IQD",
    paymentTerms: "30 يوماً من استلام البضائع",
  },
  {
    id: "CLR-002",
    name: "مؤسسة الأمين للتخليص الجمركي",
    address: "بغداد، الكرادة، شارع أبو نؤاس",
    email: "contact@alameen-customs.iq",
    phone: "+964 790 333 4444",
    authorizedRep: "عمار جاسم العبيدي",
    activeContainers: 1,
    completedContainers: 15,
    financialBalance: 3000,
    financialCurrency: "IQD",
    paymentTerms: "45 يوماً من استلام البضائع",
  },
];

export const itemRequests: ItemRequest[] = [
  {
    id: "REQ-001",
    itemName: "قارورة عطر بيضاوية",
    size: "100",
    unit: "ml",
    quantity: 5000,
    category: "glass",
    division: "china",
    requestedBy: "خالد المشهداني",
    requestedAt: "2026-02-20",
    status: "pending",
    notes: "نحتاج عينات أولاً قبل الطلب الكبير",
  },
  {
    id: "REQ-002",
    itemName: "زيت عنبر طبيعي",
    size: "500",
    unit: "kg",
    quantity: 50,
    category: "perfume",
    division: "europe",
    requestedBy: "سارة النعيمي",
    requestedAt: "2026-02-18",
    status: "approved",
    notes: "من مورد فرنسي معتمد",
  },
  {
    id: "REQ-003",
    itemName: "غطاء ألمنيوم مربع",
    size: "50",
    unit: "ml",
    quantity: 20000,
    category: "aluminium",
    division: "china",
    requestedBy: "أحمد المالكي",
    requestedAt: "2026-02-15",
    status: "ordered",
    notes: "تم الطلب ضمن PO-2026-004",
  },
  {
    id: "REQ-004",
    itemName: "كحول عطري مخصص",
    size: "25",
    unit: "kg",
    quantity: 100,
    category: "mixed",
    division: "europe",
    requestedBy: "محمد البغدادي",
    requestedAt: "2026-02-22",
    status: "pending",
    notes: "بحاجة لمفاوضة السعر مع المورد الألماني",
  },
];

export const negotiations: Negotiation[] = [
  {
    id: "NEG-001",
    supplierId: "SUP-001",
    supplierName: "مصنع الزهور الذهبية",
    itemName: "قارورة كريستال 100مل",
    currentPrice: 4.5,
    targetPrice: 4.0,
    lastOffer: 4.2,
    currency: "CNY",
    status: "counter-offer",
    messages: [
      { sender: "أحمد المالكي", text: "نحتاج سعر أفضل للكمية الكبيرة — 10,000 قطعة", date: "2026-02-18" },
      { sender: "وانغ لي", text: "أفضل سعر 4.2 يوان للقطعة مع حد أدنى 8,000", date: "2026-02-19" },
      { sender: "أحمد المالكي", text: "هل ممكن 4.0 مع طلب 12,000 قطعة؟", date: "2026-02-20" },
    ],
    division: "china",
  },
  {
    id: "NEG-002",
    supplierId: "SUP-002",
    supplierName: "Parfums de Grasse",
    itemName: "زيت عود طبيعي",
    currentPrice: 2800,
    targetPrice: 2500,
    lastOffer: 2700,
    currency: "EUR",
    status: "open",
    messages: [
      { sender: "سارة النعيمي", text: "نريد تخفيض على الكمية — هل ممكن 2,500 يورو؟", date: "2026-02-21" },
    ],
    division: "europe",
  },
];

export const suggestedPOs: SuggestedPO[] = [
  { id: "spo1", itemName: "قارورة كريستال 100مل", category: "glass", avgAnnualSales: 12000, avgTop6MonthsSales: 8500, currentStock: 1200, suggestedQty: 6000, lastPrice: 4.5, supplierId: "SUP-001", supplierName: "مصنع الزهور الذهبية" },
  { id: "spo2", itemName: "كحول إيثيلي نقي 96%", category: "alcohol", avgAnnualSales: 2400, avgTop6MonthsSales: 1800, currentStock: 200, suggestedQty: 800, lastPrice: 320, supplierId: "SUP-003", supplierName: "شركة الكحول الصناعي" },
  { id: "spo3", itemName: "زيت مسك أبيض", category: "perfume", avgAnnualSales: 150, avgTop6MonthsSales: 100, currentStock: 8, suggestedQty: 45, lastPrice: 450, supplierId: "SUP-002", supplierName: "Parfums de Grasse" },
  { id: "spo4", itemName: "غطاء ألمنيوم ذهبي 50مل", category: "aluminium", avgAnnualSales: 30000, avgTop6MonthsSales: 20000, currentStock: 5000, suggestedQty: 12000, lastPrice: 0.35, supplierId: "SUP-004", supplierName: "مصنع نينغبو للألمنيوم" },
  { id: "spo5", itemName: "عبوة رذاذ فاخرة 30مل", category: "glass", avgAnnualSales: 18000, avgTop6MonthsSales: 12000, currentStock: 3000, suggestedQty: 8000, lastPrice: 2.1, supplierId: "SUP-001", supplierName: "مصنع الزهور الذهبية" },
];

export const scNotifications: SCNotification[] = [
  { id: "n1", type: "container", title: "حاوية تصل قريباً", description: "الحاوية MSKU9876543 ستصل خلال يومين", date: "2026-02-23", read: false },
  { id: "n2", type: "container", title: "مستندات لم تُسلّم!", description: "الحاوية OOLU5678901 في الميناء — المستندات لم تصل للمخلص", date: "2026-02-23", read: false },
  { id: "n3", type: "po", title: "أمر شراء بحاجة مراجعة", description: "PO-2026-003 مسودة منذ 3 أيام", date: "2026-02-23", read: false },
  { id: "n4", type: "negotiation", title: "رد جديد في المفاوضات", description: "وانغ لي رد على عرض قارورة كريستال", date: "2026-02-20", read: true },
  { id: "n5", type: "request", title: "طلب صنف جديد", description: "محمد البغدادي طلب كحول عطري مخصص", date: "2026-02-22", read: false },
  { id: "n6", type: "reminder", title: "تذكير: متابعة المورد", description: "متابعة تأكيد PO-2026-004 مع مصنع نينغبو", date: "2026-02-24", read: false },
];

export const minMaxItems: MinMaxItem[] = [
  { id: "mm1", name: "قارورة كريستال 100مل", category: "زجاجيات", currentStock: 1200, minStock: 2000, maxStock: 15000 },
  { id: "mm2", name: "زجاجة عطر ذهبية 50مل", category: "زجاجيات", currentStock: 3500, minStock: 2000, maxStock: 12000 },
  { id: "mm3", name: "عبوة رذاذ فاخرة 30مل", category: "زجاجيات", currentStock: 3000, minStock: 3000, maxStock: 20000 },
  { id: "mm4", name: "كحول إيثيلي نقي 96%", category: "كحول", currentStock: 200, minStock: 500, maxStock: 2500 },
  { id: "mm5", name: "DPG - ديبروبيلين غلايكول", category: "كحول", currentStock: 800, minStock: 300, maxStock: 1500 },
  { id: "mm6", name: "زيت عود طبيعي", category: "عطور", currentStock: 8, minStock: 15, maxStock: 50 },
  { id: "mm7", name: "زيت مسك أبيض", category: "عطور", currentStock: 25, minStock: 10, maxStock: 80 },
  { id: "mm8", name: "غطاء ألمنيوم ذهبي 50مل", category: "ألمنيوم", currentStock: 5000, minStock: 8000, maxStock: 40000 },
  { id: "mm9", name: "غطاء ألمنيوم فضي 100مل", category: "ألمنيوم", currentStock: 12000, minStock: 5000, maxStock: 25000 },
  { id: "mm10", name: "زيت ورد بلغاري", category: "عطور", currentStock: 12, minStock: 8, maxStock: 30 },
];

export const systemUsers: SystemUser[] = [
  { id: "u1", name: "أحمد المالكي", role: "مدير المشتريات", division: "baghdad", avatar: "أم", online: true },
  { id: "u2", name: "سارة النعيمي", role: "مسؤولة قسم أوروبا", division: "europe", avatar: "سن", online: true },
  { id: "u3", name: "خالد المشهداني", role: "مسؤول قسم الصين", division: "china", avatar: "خم", online: false },
  { id: "u4", name: "محمد البغدادي", role: "محاسب", division: "baghdad", avatar: "مب", online: true },
  { id: "u5", name: "نور الهاشمي", role: "مسؤول المستودع", division: "baghdad", avatar: "نه", online: false },
  { id: "u6", name: "ليلى الكاظمي", role: "مسؤولة التخليص", division: "baghdad", avatar: "لك", online: true },
];

export const internalMessages: InternalMessage[] = [
  { id: "msg1", sender: "أحمد المالكي", senderDivision: "baghdad", recipients: ["خالد المشهداني"], mentions: ["@خالد"], text: "@خالد — أرجو متابعة تأكيد PO-2026-004 مع مصنع نينغبو. هل وصلت العينات؟", date: "2026-02-22 10:30", channel: "internal" },
  { id: "msg2", sender: "خالد المشهداني", senderDivision: "china", recipients: ["أحمد المالكي"], mentions: [], text: "نعم العينات وصلت أمس. الجودة ممتازة. سأرسل التقرير اليوم.", date: "2026-02-22 11:15", channel: "internal" },
  { id: "msg3", sender: "سارة النعيمي", senderDivision: "europe", recipients: ["أحمد المالكي", "محمد البغدادي"], mentions: ["@أحمد", "@محمد"], text: "@أحمد @محمد — Parfums de Grasse أرسلوا عرض سعر جديد لزيت العود. السعر 2,700 يورو. هل نوافق؟", date: "2026-02-22 14:00", channel: "email" },
  { id: "msg4", sender: "ليلى الكاظمي", senderDivision: "baghdad", recipients: ["أحمد المالكي"], mentions: ["@أحمد"], text: "@أحمد — الحاوية OOLU5678901 في الميناء ولم تصل المستندات بعد! المخلص ينتظر.", date: "2026-02-23 08:45", channel: "internal" },
  { id: "msg5", sender: "أحمد المالكي", senderDivision: "baghdad", recipients: ["ليلى الكاظمي", "سارة النعيمي"], mentions: ["@ليلى", "@سارة"], text: "@سارة أرجو إرسال مستندات حاوية الكحول فوراً @ليلى — سنرسلها للمخلص اليوم.", date: "2026-02-23 09:00", channel: "internal" },
];

export const scEmails: SCEmail[] = [
  { id: "em1", from: "jp.martin@grasse-parfums.fr", to: "purchasing@nooranibras.iq", subject: "RE: Price Quote - Oud Oil 2026", body: "Dear Ahmed,\n\nPlease find attached our updated price list for Q1 2026. The Oud oil price has been revised to EUR 2,700/kg for orders above 10kg.\n\nBest regards,\nJean-Pierre Martin", date: "2026-02-21 09:30", read: true, attachments: ["Price_List_Q1_2026.pdf"], relatedPO: "PO-2026-002" },
  { id: "em2", from: "wang.li@goldenflowers.cn", to: "purchasing@nooranibras.iq", subject: "Container Shipment Confirmation - CSLU2345678", body: "Dear Sir,\n\nWe confirm the container CSLU2345678 has been shipped from Shanghai port on Feb 10. ETA: March 12.\n\nAttached: Bill of Lading and Commercial Invoice.\n\nBest,\nWang Li", date: "2026-02-10 16:00", read: true, attachments: ["BL_2026_00145.pdf", "Invoice_GF_2026_012.pdf"], relatedContainer: "CNT-001" },
  { id: "em3", from: "m.fischer@indal.de", to: "purchasing@nooranibras.iq", subject: "RE: PO-2026-003 Draft Review", body: "Hallo,\n\nWe reviewed the draft PO-2026-003. The price for Ethanol 96% has increased to EUR 320/unit. DPG price reduced to EUR 85/25kg.\n\nPlease confirm.\n\nMarkus Fischer", date: "2026-02-20 11:00", read: false, attachments: [], relatedPO: "PO-2026-003" },
  { id: "em4", from: "purchasing@nooranibras.iq", to: "info@alfajr-clearance.iq", subject: "Container Documents - OOLU5678901", body: "السيد حسين المالكي المحترم،\n\nمرفق مستندات الحاوية OOLU5678901 للتخليص.\n\nأرجو البدء بالإجراءات فوراً.\n\nمع التقدير،\nنور النبراس للعطور", date: "2026-02-23 09:30", read: true, attachments: ["Container_Docs_OOLU5678901.pdf"], relatedContainer: "CNT-004" },
];

// ── Helpers ─────────────────────────────────────────

export const poStatusConfig: Record<PurchaseOrder["status"], { label: string; color: string }> = {
  draft: { label: "مسودة", color: "bg-muted text-muted-foreground" },
  sent: { label: "مُرسل", color: "bg-blue-500/15 text-blue-500" },
  confirmed: { label: "مؤكد", color: "bg-primary/15 text-primary" },
  shipped: { label: "تم الشحن", color: "bg-indigo-500/15 text-indigo-500" },
  received: { label: "مُستلم", color: "bg-emerald-500/15 text-emerald-500" },
  cancelled: { label: "ملغي", color: "bg-red-500/15 text-red-500" },
};

export const containerStatusConfig: Record<Container["status"], { label: string; color: string }> = {
  active: { label: "نشطة", color: "bg-blue-500/15 text-blue-500" },
  "at-port": { label: "في الميناء", color: "bg-primary/15 text-primary" },
  completed: { label: "مكتملة", color: "bg-emerald-500/15 text-emerald-500" },
  "arriving-soon": { label: "تصل قريباً", color: "bg-violet-500/15 text-violet-500" },
};

export const requestStatusConfig: Record<ItemRequest["status"], { label: string; color: string }> = {
  pending: { label: "قيد الانتظار", color: "bg-primary/15 text-primary" },
  approved: { label: "موافق عليه", color: "bg-emerald-500/15 text-emerald-500" },
  ordered: { label: "تم الطلب", color: "bg-blue-500/15 text-blue-500" },
  rejected: { label: "مرفوض", color: "bg-red-500/15 text-red-500" },
};

export const negStatusConfig: Record<Negotiation["status"], { label: string; color: string }> = {
  open: { label: "مفتوح", color: "bg-blue-500/15 text-blue-500" },
  "counter-offer": { label: "عرض مضاد", color: "bg-primary/15 text-primary" },
  agreed: { label: "متفق عليه", color: "bg-emerald-500/15 text-emerald-500" },
  rejected: { label: "مرفوض", color: "bg-red-500/15 text-red-500" },
};