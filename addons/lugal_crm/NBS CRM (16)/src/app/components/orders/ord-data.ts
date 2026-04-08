// ═══════════════════════════════════════════════════════════
//  Orders & Delivery — Data Model & Mock Data
//  Multi-Branch aware, Delivery integration, Customer-linked
//  Connected to: Customers, Invoices, Delivery Companies, Branches
// ═══════════════════════════════════════════════════════════

// ── Branch Model ────────────────────────────────────────

export interface Branch {
  id: string;
  name: string;
  city: string;
  address: string;
  phone: string;
  manager: string;
  isActive: boolean;
}

export const branches: Branch[] = [
  { id: "br-01", name: "فرع الرياض — النخيل", city: "الرياض", address: "حي النخيل، شارع الملك فهد", phone: "+966 11 200 0001", manager: "أحمد العلي", isActive: true },
  { id: "br-02", name: "فرع جدة — التحلية", city: "جدة", address: "حي الحمراء، شارع التحلية", phone: "+966 12 300 0002", manager: "ياسر المحمدي", isActive: true },
  { id: "br-03", name: "فرع الرياض — العليا", city: "الرياض", address: "حي العليا، طريق الملك فهد", phone: "+966 11 200 0003", manager: "سعود المالكي", isActive: true },
  { id: "br-04", name: "فرع الدمام", city: "الدمام", address: "حي الفيصلية، شارع الأمير محمد", phone: "+966 13 400 0004", manager: "خالد القحطاني", isActive: true },
];

// ── Delivery Company ────────────────────────────────────

export interface DeliveryCompany {
  id: string;
  name: string;
  nameEn: string;
  logo?: string;
  color: string;
  trackingUrlTemplate: string; // e.g. "https://track.aramex.com/{trackingNumber}"
}

export const deliveryCompanies: DeliveryCompany[] = [
  { id: "del-aramex", name: "أرامكس", nameEn: "Aramex", color: "#E2231A", trackingUrlTemplate: "https://www.aramex.com/track/{trackingNumber}" },
  { id: "del-smsa", name: "SMSA إكسبرس", nameEn: "SMSA Express", color: "#0072BC", trackingUrlTemplate: "https://www.smsaexpress.com/track/{trackingNumber}" },
  { id: "del-naqel", name: "ناقل", nameEn: "Naqel Express", color: "#1B3A5C", trackingUrlTemplate: "https://www.naqelexpress.com/track/{trackingNumber}" },
  { id: "del-dhl", name: "DHL", nameEn: "DHL", color: "#FFCC00", trackingUrlTemplate: "https://www.dhl.com/track/{trackingNumber}" },
  { id: "del-self", name: "توصيل ذاتي", nameEn: "Self Delivery", color: "#10b981", trackingUrlTemplate: "" },
];

// ── Order Status ────────────────────────────────────────

export type OrderStatus =
  | "pending"       // new order, not processed
  | "confirmed"     // confirmed by agent
  | "preparing"     // being prepared / packaged
  | "shipped"       // handed to delivery company
  | "in_transit"    // delivery in progress
  | "out_for_delivery" // on the way to customer
  | "delivered"     // delivered successfully
  | "returned"      // returned by customer
  | "cancelled";    // cancelled

export const orderStatusLabels: Record<OrderStatus, string> = {
  pending: "في الانتظار",
  confirmed: "مؤكد",
  preparing: "قيد التجهيز",
  shipped: "تم الشحن",
  in_transit: "في النقل",
  out_for_delivery: "في الطريق للعميل",
  delivered: "تم التوصيل",
  returned: "مُرتجع",
  cancelled: "ملغي",
};

export const orderStatusColors: Record<OrderStatus, string> = {
  pending: "bg-muted/30 text-muted-foreground",
  confirmed: "bg-blue-500/15 text-blue-400",
  preparing: "bg-primary/15 text-primary",
  shipped: "bg-violet-500/15 text-violet-400",
  in_transit: "bg-cyan-500/15 text-cyan-400",
  out_for_delivery: "bg-emerald-500/15 text-emerald-400",
  delivered: "bg-emerald-500/20 text-emerald-500",
  returned: "bg-red-500/15 text-red-400",
  cancelled: "bg-red-500/10 text-red-500/60",
};

export const orderStatusStep: Record<OrderStatus, number> = {
  pending: 0, confirmed: 1, preparing: 2, shipped: 3,
  in_transit: 4, out_for_delivery: 5, delivered: 6,
  returned: -1, cancelled: -2,
};

// ── Order Item ──────────────────────────────────────────

export interface OrderItem {
  id: string;
  itemCode: string;
  name: string;
  quantity: number;
  unitPrice: number;
  currency: string;
  discount: number; // percentage
  total: number;
}

// ── Order ───────────────────────────────────────────────

export interface Order {
  id: string;
  orderNumber: string;
  customerId: string;
  customerName: string;
  customerPhone: string;
  branchId: string;
  branchName: string;
  status: OrderStatus;
  items: OrderItem[];
  subtotal: number;
  discount: number;
  vat: number;
  total: number;
  currency: string;
  invoiceId?: string;
  invoiceNumber?: string;
  // Delivery
  deliveryCompanyId: string | null;
  deliveryCompanyName?: string;
  trackingNumber?: string;
  estimatedDelivery?: string;
  actualDelivery?: string;
  deliveryAddress: string;
  deliveryCity: string;
  // Conversation link
  conversationId?: string;
  channelSource?: string;
  assignedAgent?: string;
  // Timestamps
  createdAt: string;
  confirmedAt?: string;
  shippedAt?: string;
  deliveredAt?: string;
  notes?: string;
}

// ── Sample Boxes ────────────────────────────────────────

export interface SampleBox {
  id: string;
  version: string;
  name: string;
  description: string;
  contents: { itemCode: string; itemName: string; sizeML: number }[];
  createdAt: string;
  totalSent: number;
}

export interface SampleBoxDelivery {
  id: string;
  sampleBoxId: string;
  sampleBoxVersion: string;
  customerId: string;
  customerName: string;
  sentAt: string;
  receivedAt?: string;
  status: "sent" | "received" | "returned";
  sentBy: string;
}

export const sampleBoxes: SampleBox[] = [
  {
    id: "sb-01", version: "V3.2", name: "صندوق تعريفي — عطور رجالية",
    description: "8 عينات من أحدث العطور الرجالية",
    contents: [
      { itemCode: "PERF-001", itemName: "عطر فاخر", sizeML: 5 },
      { itemCode: "PERF-005", itemName: "كلاسيك يورو", sizeML: 5 },
      { itemCode: "PERF-003", itemName: "إسنس غراس", sizeML: 3 },
      { itemCode: "PERF-016", itemName: "فيرمنيتش إليت", sizeML: 3 },
      { itemCode: "PERF-010", itemName: "أورينتال بلند", sizeML: 5 },
      { itemCode: "PERF-004", itemName: "فلورال سيمفوني", sizeML: 5 },
      { itemCode: "PERF-011", itemName: "بريميوم جيفودان", sizeML: 3 },
      { itemCode: "PERF-009", itemName: "سيدار وود", sizeML: 3 },
    ],
    createdAt: "2026-01-15", totalSent: 45,
  },
  {
    id: "sb-02", version: "V2.1", name: "صندوق تعريفي — عطور نسائية",
    description: "6 عينات من العطور النسائية الأكثر طلباً",
    contents: [
      { itemCode: "PERF-002", itemName: "روز أمور", sizeML: 5 },
      { itemCode: "PERF-007", itemName: "فلور نوار", sizeML: 5 },
      { itemCode: "PERF-012", itemName: "جاردان دو باريس", sizeML: 5 },
      { itemCode: "PERF-015", itemName: "ليلة أمور", sizeML: 3 },
      { itemCode: "PERF-008", itemName: "ناتورال أبسوليوت", sizeML: 3 },
      { itemCode: "PERF-014", itemName: "ميديتيرانيان فريش", sizeML: 5 },
    ],
    createdAt: "2026-02-01", totalSent: 28,
  },
];

export const sampleBoxDeliveries: SampleBoxDelivery[] = [
  { id: "sbd-01", sampleBoxId: "sb-01", sampleBoxVersion: "V3.2", customerId: "C-001", customerName: "أحمد محمد العلي", sentAt: "2026-02-15", receivedAt: "2026-02-17", status: "received", sentBy: "سعود المالكي" },
  { id: "sbd-02", sampleBoxId: "sb-02", sampleBoxVersion: "V2.1", customerId: "C-002", customerName: "فاطمة عبدالله السالم", sentAt: "2026-02-18", status: "sent", sentBy: "منى الشهري" },
  { id: "sbd-03", sampleBoxId: "sb-01", sampleBoxVersion: "V3.2", customerId: "C-006", customerName: "سارة علي الحربي", sentAt: "2026-02-20", receivedAt: "2026-02-22", status: "received", sentBy: "عبدالله الحربي" },
  { id: "sbd-04", sampleBoxId: "sb-02", sampleBoxVersion: "V2.1", customerId: "C-004", customerName: "نورة بدر المالكي", sentAt: "2026-02-21", status: "sent", sentBy: "منى الشهري" },
];

// ── Mock Orders ─────────────────────────────────────────

export const mockOrders: Order[] = [
  {
    id: "ord-001", orderNumber: "ORD-4521",
    customerId: "C-006", customerName: "سارة علي الحربي", customerPhone: "+966 59 555 6666",
    branchId: "br-01", branchName: "فرع الرياض — النخيل",
    status: "in_transit",
    items: [
      { id: "oi-01", itemCode: "PERF-007", name: "فلور نوار 100مل", quantity: 1, unitPrice: 180, currency: "USD", discount: 0, total: 180 },
      { id: "oi-02", itemCode: "PERF-002", name: "روز أمور 50مل", quantity: 2, unitPrice: 95, currency: "USD", discount: 10, total: 171 },
    ],
    subtotal: 370, discount: 19, vat: 52.65, total: 403.65, currency: "USD",
    invoiceId: "inv-2026-0089", invoiceNumber: "INV-2026-0089",
    deliveryCompanyId: "del-aramex", deliveryCompanyName: "أرامكس",
    trackingNumber: "ARX-29384756",
    estimatedDelivery: "2026-02-24",
    deliveryAddress: "حي العليا، طريق الملك فهد", deliveryCity: "الرياض",
    conversationId: "conv-004", channelSource: "instagram", assignedAgent: "سعود المالكي",
    createdAt: "2026-02-20T10:00:00", confirmedAt: "2026-02-20T10:30:00", shippedAt: "2026-02-21T09:00:00",
  },
  {
    id: "ord-002", orderNumber: "ORD-4522",
    customerId: "C-001", customerName: "أحمد محمد العلي", customerPhone: "+966 50 123 4567",
    branchId: "br-01", branchName: "فرع الرياض — النخيل",
    status: "delivered",
    items: [
      { id: "oi-03", itemCode: "PERF-016", name: "فيرمنيتش إليت 100مل", quantity: 1, unitPrice: 250, currency: "USD", discount: 0, total: 250 },
    ],
    subtotal: 250, discount: 0, vat: 37.5, total: 287.5, currency: "USD",
    invoiceId: "inv-2026-0085", invoiceNumber: "INV-2026-0085",
    deliveryCompanyId: "del-self", deliveryCompanyName: "توصيل ذاتي",
    deliveryAddress: "حي النخيل، شارع الملك فهد", deliveryCity: "الرياض",
    assignedAgent: "سعود المالكي",
    createdAt: "2026-02-18T14:00:00", confirmedAt: "2026-02-18T14:15:00", shippedAt: "2026-02-18T15:00:00", deliveredAt: "2026-02-18T17:00:00",
  },
  {
    id: "ord-003", orderNumber: "ORD-4523",
    customerId: "C-002", customerName: "فاطمة عبدالله السالم", customerPhone: "+966 55 987 6543",
    branchId: "br-02", branchName: "فرع جدة — التحلية",
    status: "preparing",
    items: [
      { id: "oi-04", itemCode: "PERF-012", name: "جاردان دو باريس 75مل", quantity: 1, unitPrice: 145, currency: "USD", discount: 15, total: 123.25 },
      { id: "oi-05", itemCode: "PERF-015", name: "ليلة أمور 100مل", quantity: 1, unitPrice: 210, currency: "USD", discount: 0, total: 210 },
      { id: "oi-06", itemCode: "ACC-001", name: "علبة هدية فاخرة", quantity: 1, unitPrice: 35, currency: "USD", discount: 0, total: 35 },
    ],
    subtotal: 390, discount: 21.75, vat: 55.24, total: 423.49, currency: "USD",
    deliveryCompanyId: "del-smsa", deliveryCompanyName: "SMSA إكسبرس",
    deliveryAddress: "حي الحمراء، شارع التحلية", deliveryCity: "جدة",
    conversationId: "conv-003", channelSource: "whatsapp", assignedAgent: "منى الشهري",
    createdAt: "2026-02-22T16:00:00", confirmedAt: "2026-02-22T16:30:00",
  },
  {
    id: "ord-004", orderNumber: "ORD-4524",
    customerId: "C-004", customerName: "نورة بدر المالكي", customerPhone: "+966 53 456 7890",
    branchId: "br-03", branchName: "فرع الرياض — العليا",
    status: "confirmed",
    items: [
      { id: "oi-07", itemCode: "OIL-003", name: "زجاج عود 10مل", quantity: 3, unitPrice: 45, currency: "USD", discount: 0, total: 135 },
    ],
    subtotal: 135, discount: 0, vat: 20.25, total: 155.25, currency: "USD",
    deliveryCompanyId: null,
    deliveryAddress: "حي الورود، الرياض", deliveryCity: "الرياض",
    conversationId: "conv-007", channelSource: "whatsapp2", assignedAgent: "منى الشهري",
    createdAt: "2026-02-23T08:00:00", confirmedAt: "2026-02-23T08:30:00",
  },
  {
    id: "ord-005", orderNumber: "ORD-4525",
    customerId: "C-003", customerName: "خالد سعد القحطاني", customerPhone: "+966 51 654 3210",
    branchId: "br-04", branchName: "فرع الدمام",
    status: "pending",
    items: [
      { id: "oi-08", itemCode: "PERF-001", name: "عطر فاخر 100مل", quantity: 2, unitPrice: 125, currency: "USD", discount: 0, total: 250 },
      { id: "oi-09", itemCode: "PERF-006", name: "عطر ديلوكس 150مل", quantity: 1, unitPrice: 175, currency: "USD", discount: 5, total: 166.25 },
    ],
    subtotal: 425, discount: 8.75, vat: 62.44, total: 478.69, currency: "USD",
    deliveryCompanyId: null,
    deliveryAddress: "حي الفيصلية، الدمام", deliveryCity: "الدمام",
    conversationId: "conv-006", channelSource: "email",
    createdAt: "2026-02-23T09:00:00",
    notes: "العميل VIP — أولوية عالية",
  },
  {
    id: "ord-006", orderNumber: "ORD-4520",
    customerId: "C-007", customerName: "محمد عبدالله العتيبي", customerPhone: "+966 50 777 8888",
    branchId: "br-01", branchName: "فرع الرياض — النخيل",
    status: "cancelled",
    items: [
      { id: "oi-10", itemCode: "PERF-013", name: "مسك بروفنس 75مل", quantity: 1, unitPrice: 185, currency: "USD", discount: 0, total: 185 },
    ],
    subtotal: 185, discount: 0, vat: 27.75, total: 212.75, currency: "USD",
    deliveryCompanyId: null,
    deliveryAddress: "حي العزيزية، مكة", deliveryCity: "مكة",
    createdAt: "2026-02-19T11:00:00",
    notes: "العميل ألغى الطلب — المنتج غير متوفر",
  },
];

// ── Forecasting / Inventory Data ────────────────────────

export type UrgencyLevel = "critical" | "warning" | "normal" | "surplus";

export interface ProductInventory {
  itemCode: string;
  name: string;
  category: "perfume" | "oil" | "accessory";
  sizeML: number | null;
  currentStock: number;
  reorderPoint: number;
  maxStock: number;
  unitCost: number;
  unitPrice: number;
  avgDailySales: number;           // rolling 30-day avg
  last30DaysSold: number;
  last60DaysSold: number;          // for trend comparison
  leadTimeDays: number;            // supplier lead time
  daysOfStockLeft: number;         // currentStock / avgDailySales
  suggestedOrderQty: number;
  urgency: UrgencyLevel;
  topBranch: string;               // branch with highest demand
  monthlyTrend: number[];          // last 6 months sold qty
  seasonalIndex: number;           // >1 = high season, <1 = low season
  supplierName: string;
  lastRestockedAt: string;
}

export const productInventory: ProductInventory[] = [
  {
    itemCode: "PERF-001", name: "عطر فاخر 100مل", category: "perfume", sizeML: 100,
    currentStock: 8, reorderPoint: 25, maxStock: 100, unitCost: 55, unitPrice: 125,
    avgDailySales: 2.8, last30DaysSold: 84, last60DaysSold: 148, leadTimeDays: 14,
    daysOfStockLeft: 3, suggestedOrderQty: 92,
    urgency: "critical", topBranch: "فرع الرياض — النخيل",
    monthlyTrend: [62, 70, 75, 82, 84, 91],
    seasonalIndex: 1.3, supplierName: "جيفودان", lastRestockedAt: "2026-01-28",
  },
  {
    itemCode: "PERF-002", name: "روز أمور 50مل", category: "perfume", sizeML: 50,
    currentStock: 12, reorderPoint: 20, maxStock: 80, unitCost: 42, unitPrice: 95,
    avgDailySales: 2.1, last30DaysSold: 63, last60DaysSold: 110, leadTimeDays: 14,
    daysOfStockLeft: 6, suggestedOrderQty: 68,
    urgency: "critical", topBranch: "فرع جدة — التحلية",
    monthlyTrend: [45, 50, 55, 58, 63, 68],
    seasonalIndex: 1.2, supplierName: "فيرمنيتش", lastRestockedAt: "2026-02-01",
  },
  {
    itemCode: "PERF-003", name: "إسنس غراس 75مل", category: "perfume", sizeML: 75,
    currentStock: 18, reorderPoint: 15, maxStock: 60, unitCost: 65, unitPrice: 145,
    avgDailySales: 1.5, last30DaysSold: 45, last60DaysSold: 82, leadTimeDays: 21,
    daysOfStockLeft: 12, suggestedOrderQty: 42,
    urgency: "warning", topBranch: "فرع الرياض — العليا",
    monthlyTrend: [35, 38, 40, 42, 45, 50],
    seasonalIndex: 1.1, supplierName: "غراس فرنسا", lastRestockedAt: "2026-02-05",
  },
  {
    itemCode: "PERF-005", name: "كلاسيك يورو 100مل", category: "perfume", sizeML: 100,
    currentStock: 35, reorderPoint: 20, maxStock: 80, unitCost: 80, unitPrice: 180,
    avgDailySales: 1.2, last30DaysSold: 36, last60DaysSold: 70, leadTimeDays: 18,
    daysOfStockLeft: 29, suggestedOrderQty: 0,
    urgency: "normal", topBranch: "فرع الرياض — النخيل",
    monthlyTrend: [30, 32, 33, 35, 36, 38],
    seasonalIndex: 1.0, supplierName: "جيفودان", lastRestockedAt: "2026-02-10",
  },
  {
    itemCode: "PERF-007", name: "فلور نوار 100مل", category: "perfume", sizeML: 100,
    currentStock: 5, reorderPoint: 15, maxStock: 60, unitCost: 78, unitPrice: 180,
    avgDailySales: 1.8, last30DaysSold: 54, last60DaysSold: 90, leadTimeDays: 14,
    daysOfStockLeft: 3, suggestedOrderQty: 55,
    urgency: "critical", topBranch: "فرع جدة — التحلية",
    monthlyTrend: [38, 42, 45, 48, 54, 58],
    seasonalIndex: 1.15, supplierName: "فيرمنيتش", lastRestockedAt: "2026-01-20",
  },
  {
    itemCode: "PERF-012", name: "جاردان دو باريس 75مل", category: "perfume", sizeML: 75,
    currentStock: 22, reorderPoint: 12, maxStock: 50, unitCost: 62, unitPrice: 145,
    avgDailySales: 1.0, last30DaysSold: 30, last60DaysSold: 55, leadTimeDays: 21,
    daysOfStockLeft: 22, suggestedOrderQty: 0,
    urgency: "normal", topBranch: "فرع الرياض — العليا",
    monthlyTrend: [22, 24, 26, 28, 30, 32],
    seasonalIndex: 1.05, supplierName: "غراس فرنسا", lastRestockedAt: "2026-02-08",
  },
  {
    itemCode: "PERF-015", name: "ليلة أمور 100مل", category: "perfume", sizeML: 100,
    currentStock: 14, reorderPoint: 18, maxStock: 70, unitCost: 92, unitPrice: 210,
    avgDailySales: 1.6, last30DaysSold: 48, last60DaysSold: 80, leadTimeDays: 14,
    daysOfStockLeft: 9, suggestedOrderQty: 56,
    urgency: "warning", topBranch: "فرع الدمام",
    monthlyTrend: [32, 36, 40, 44, 48, 52],
    seasonalIndex: 1.25, supplierName: "فيرمنيتش", lastRestockedAt: "2026-02-03",
  },
  {
    itemCode: "PERF-016", name: "فيرمنيتش إليت 100مل", category: "perfume", sizeML: 100,
    currentStock: 28, reorderPoint: 10, maxStock: 40, unitCost: 110, unitPrice: 250,
    avgDailySales: 0.8, last30DaysSold: 24, last60DaysSold: 44, leadTimeDays: 21,
    daysOfStockLeft: 35, suggestedOrderQty: 0,
    urgency: "normal", topBranch: "فرع الرياض — النخيل",
    monthlyTrend: [18, 20, 21, 22, 24, 26],
    seasonalIndex: 0.95, supplierName: "فيرمنيتش", lastRestockedAt: "2026-02-12",
  },
  {
    itemCode: "OIL-003", name: "زجاج عود 10مل", category: "oil", sizeML: 10,
    currentStock: 45, reorderPoint: 30, maxStock: 120, unitCost: 18, unitPrice: 45,
    avgDailySales: 3.5, last30DaysSold: 105, last60DaysSold: 190, leadTimeDays: 7,
    daysOfStockLeft: 13, suggestedOrderQty: 75,
    urgency: "warning", topBranch: "فرع الدمام",
    monthlyTrend: [80, 85, 90, 95, 105, 112],
    seasonalIndex: 1.35, supplierName: "عود المشرق", lastRestockedAt: "2026-02-15",
  },
  {
    itemCode: "ACC-001", name: "علبة هدية فاخرة", category: "accessory", sizeML: null,
    currentStock: 150, reorderPoint: 40, maxStock: 300, unitCost: 12, unitPrice: 35,
    avgDailySales: 2.0, last30DaysSold: 60, last60DaysSold: 115, leadTimeDays: 10,
    daysOfStockLeft: 75, suggestedOrderQty: 0,
    urgency: "surplus", topBranch: "فرع الرياض — النخيل",
    monthlyTrend: [50, 52, 55, 58, 60, 60],
    seasonalIndex: 1.1, supplierName: "مصنع الأناقة", lastRestockedAt: "2026-02-18",
  },
  {
    itemCode: "PERF-004", name: "فلورال سيمفوني 75مل", category: "perfume", sizeML: 75,
    currentStock: 10, reorderPoint: 12, maxStock: 50, unitCost: 58, unitPrice: 135,
    avgDailySales: 1.1, last30DaysSold: 33, last60DaysSold: 58, leadTimeDays: 18,
    daysOfStockLeft: 9, suggestedOrderQty: 40,
    urgency: "warning", topBranch: "فرع جدة — التحلية",
    monthlyTrend: [24, 26, 28, 30, 33, 36],
    seasonalIndex: 1.1, supplierName: "غراس فرنسا", lastRestockedAt: "2026-01-25",
  },
  {
    itemCode: "PERF-009", name: "سيدار وود 75مل", category: "perfume", sizeML: 75,
    currentStock: 42, reorderPoint: 15, maxStock: 60, unitCost: 48, unitPrice: 120,
    avgDailySales: 0.7, last30DaysSold: 21, last60DaysSold: 40, leadTimeDays: 14,
    daysOfStockLeft: 60, suggestedOrderQty: 0,
    urgency: "surplus", topBranch: "فرع الرياض — العليا",
    monthlyTrend: [20, 20, 21, 21, 21, 22],
    seasonalIndex: 0.85, supplierName: "جيفودان", lastRestockedAt: "2026-02-10",
  },
];

export const urgencyLabels: Record<UrgencyLevel, string> = {
  critical: "حرج — اطلب فوراً",
  warning: "تحذير — اطلب قريباً",
  normal: "طبيعي",
  surplus: "فائض",
};

export const urgencyColors: Record<UrgencyLevel, string> = {
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
  warning: "bg-primary/15 text-primary border-primary/30",
  normal: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  surplus: "bg-blue-500/10 text-blue-300 border-blue-500/20",
};