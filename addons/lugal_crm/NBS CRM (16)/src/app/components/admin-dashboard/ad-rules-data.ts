// ═══════════════════════════════════════════════════════════
//  Rule Engine — Data Model & Mock Rules
//  No hardcoded logic: everything is configurable via tables
// ═══════════════════════════════════════════════════════════

// ── Category Definitions ─────────────────────────────────

export type RuleCategory =
  | "sla"
  | "routing"
  | "escalation"
  | "qa"
  | "attendance"
  | "notifications"
  | "vip"
  | "automation"
  | "products";

export interface RuleCategoryMeta {
  id: RuleCategory;
  label: string;
  description: string;
  icon: string; // lucide icon name — resolved in the component
  color: string;
}

export const ruleCategories: RuleCategoryMeta[] = [
  {
    id: "sla",
    label: "SLA وأوقات الاستجابة",
    description: "حدود أوقات الرد والتحذيرات ومعايير المخالفة",
    icon: "Timer",
    color: "text-blue-500",
  },
  {
    id: "routing",
    label: "التوجيه والتعيين",
    description: "قواعد توزيع المحادثات والمكالمات على الموظفين",
    icon: "Route",
    color: "text-violet-500",
  },
  {
    id: "escalation",
    label: "التصعيد",
    description: "شروط تصعيد التكتات والشكاوى تلقائياً",
    icon: "ArrowUpCircle",
    color: "text-red-500",
  },
  {
    id: "qa",
    label: "الجودة والتدقيق",
    description: "معايير التقييم وحد الاستماع الأدنى وتعريف «فتح وطلع»",
    icon: "ShieldCheck",
    color: "text-cyan-500",
  },
  {
    id: "attendance",
    label: "الحضور والدوام",
    description: "ساعات العمل وحد التأخير ومراقبة الخمول",
    icon: "CalendarCheck",
    color: "text-emerald-500",
  },
  {
    id: "notifications",
    label: "التنبيهات والإشعارات",
    description: "متى وأين ترسل تنبيهاً للمشرف أو الموظف",
    icon: "Bell",
    color: "text-yellow-500",
  },
  {
    id: "vip",
    label: "VIP والتصنيفات",
    description: "شروط الترقية والتخفيض ومعايير التصنيف",
    icon: "Crown",
    color: "text-primary",
  },
  {
    id: "automation",
    label: "الأتمتة",
    description: "إجراءات تلقائية بناءً على أحداث النظام",
    icon: "Zap",
    color: "text-pink-500",
  },
  {
    id: "products",
    label: "منتجات",
    description: "قواعد تخصيص المنتجات وتنظيمها",
    icon: "Package",
    color: "text-gray-500",
  },
];

// ── Condition / Action primitives ────────────────────────

export type ConditionOperator =
  | "equals"
  | "not_equals"
  | "greater_than"
  | "less_than"
  | "greater_equal"
  | "less_equal"
  | "contains"
  | "not_contains"
  | "in"
  | "not_in"
  | "is_true"
  | "is_false";

export const operatorLabels: Record<ConditionOperator, string> = {
  equals: "يساوي",
  not_equals: "لا يساوي",
  greater_than: "أكبر من",
  less_than: "أقل من",
  greater_equal: "أكبر أو يساوي",
  less_equal: "أقل أو يساوي",
  contains: "يحتوي",
  not_contains: "لا يحتوي",
  in: "ضمن",
  not_in: "ليس ضمن",
  is_true: "✓ نعم",
  is_false: "✗ لا",
};

export interface RuleCondition {
  id: string;
  field: string;        // e.g. "response_time", "customer.segment"
  fieldLabel: string;   // Arabic display
  operator: ConditionOperator;
  value: string | number | boolean | string[];
  valueLabel?: string;  // Arabic display for the value
  unit?: string;        // "دقيقة" | "ساعة" | "ر.س" etc.
}

export type ActionType =
  | "set_status"
  | "assign_to"
  | "notify"
  | "escalate"
  | "tag"
  | "create_task"
  | "change_priority"
  | "send_message"
  | "log_event"
  | "block"
  | "auto_reply"
  | "transfer";

export const actionLabels: Record<ActionType, string> = {
  set_status: "تغيير الحالة",
  assign_to: "تعيين إلى",
  notify: "إرسال تنبيه",
  escalate: "تصعيد",
  tag: "إضافة وسم",
  create_task: "إنشاء مهمة",
  change_priority: "تغيير الأولوية",
  send_message: "إرسال رسالة",
  log_event: "تسجيل حدث",
  block: "حظر الإجراء",
  auto_reply: "رد تلقائي",
  transfer: "نقل",
};

export interface RuleAction {
  id: string;
  type: ActionType;
  typeLabel: string;
  params: Record<string, string | number | boolean>;
  paramsLabel: string; // readable Arabic summary
}

// ── Rule Definition ──────────────────────────────────────

export interface Rule {
  id: string;
  name: string;
  description: string;
  category: RuleCategory;
  enabled: boolean;
  priority: number;       // lower = runs first
  conditions: RuleCondition[];
  conditionLogic: "AND" | "OR"; // how conditions combine
  actions: RuleAction[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  appliesTo?: string;     // target scope, e.g. "agents", "qa", "all"
  schedule?: string;      // optional cron-like description
}

// ── Field Catalog (available fields per category) ────────

export interface FieldOption {
  value: string;
  label: string;
  type: "number" | "string" | "boolean" | "select";
  unit?: string;
  options?: { value: string; label: string }[];
}

export const fieldCatalog: Record<RuleCategory, FieldOption[]> = {
  sla: [
    { value: "response_time", label: "وقت الاستجابة", type: "number", unit: "دقيقة" },
    { value: "first_response_time", label: "وقت أول رد", type: "number", unit: "دقيقة" },
    { value: "resolution_time", label: "وقت الحل", type: "number", unit: "ساعة" },
    { value: "channel", label: "القناة", type: "select", options: [
      { value: "phone", label: "هاتف" }, { value: "whatsapp", label: "واتساب" },
      { value: "email", label: "بريد" }, { value: "live-chat", label: "محادثة مباشرة" },
      { value: "instagram", label: "إنستقرام" }, { value: "x", label: "X" },
    ]},
    { value: "customer.vip", label: "عميل VIP", type: "boolean" },
    { value: "priority", label: "الأولوية", type: "select", options: [
      { value: "urgent", label: "عاجل" }, { value: "high", label: "عالي" },
      { value: "normal", label: "عادي" }, { value: "low", label: "منخفض" },
    ]},
  ],
  routing: [
    { value: "channel", label: "القناة", type: "select", options: [
      { value: "phone", label: "هاتف" }, { value: "whatsapp", label: "واتساب" },
      { value: "email", label: "بريد" }, { value: "live-chat", label: "محادثة" },
    ]},
    { value: "customer.segment", label: "شريحة العميل", type: "select", options: [
      { value: "platinum", label: "بلاتيني" }, { value: "gold", label: "ذهبي" },
      { value: "silver", label: "فضي" }, { value: "regular", label: "عادي" },
    ]},
    { value: "customer.vip", label: "عميل VIP", type: "boolean" },
    { value: "agent.status", label: "حالة الوكيل", type: "select", options: [
      { value: "available", label: "متاح" }, { value: "busy", label: "مشغول" },
    ]},
    { value: "agent.open_conversations", label: "محادثات الوكيل المفتوحة", type: "number" },
    { value: "agent.skill", label: "مهارة الوكيل", type: "select", options: [
      { value: "general", label: "عام" }, { value: "vip", label: "VIP" },
      { value: "complaints", label: "شكاوى" }, { value: "sales", label: "مبيعات" },
    ]},
    { value: "language", label: "لغة المحادثة", type: "select", options: [
      { value: "ar", label: "عربي" }, { value: "en", label: "إنجليزي" },
    ]},
  ],
  escalation: [
    { value: "ticket.age", label: "عمر التكت", type: "number", unit: "ساعة" },
    { value: "ticket.severity", label: "خطورة التكت", type: "select", options: [
      { value: "critical", label: "حرجة" }, { value: "high", label: "عالية" },
      { value: "medium", label: "متوسطة" }, { value: "low", label: "منخفضة" },
    ]},
    { value: "ticket.reopened_count", label: "عدد مرات إعادة الفتح", type: "number" },
    { value: "customer.vip", label: "عميل VIP", type: "boolean" },
    { value: "sla.breached", label: "SLA منتهك", type: "boolean" },
    { value: "customer.complaints_count", label: "عدد شكاوى العميل", type: "number" },
  ],
  qa: [
    { value: "listen_duration", label: "مدة الاستماع", type: "number", unit: "ثانية" },
    { value: "has_notes", label: "كتب ملاحظات", type: "boolean" },
    { value: "has_score", label: "أعطى درجة", type: "boolean" },
    { value: "score", label: "الدرجة", type: "number" },
    { value: "idle_time", label: "وقت الخمول", type: "number", unit: "دقيقة" },
    { value: "evaluations_per_day", label: "تقييمات اليوم", type: "number" },
    { value: "opened_without_eval", label: "فتح بدون تقييم", type: "number" },
  ],
  attendance: [
    { value: "login_time", label: "وقت الدخول", type: "number", unit: "دقيقة بعد بداية الدوام" },
    { value: "idle_time", label: "وقت الخمول", type: "number", unit: "دقيقة" },
    { value: "active_time_ratio", label: "نسبة النشاط", type: "number", unit: "%" },
    { value: "is_remote", label: "عمل عن بعد", type: "boolean" },
    { value: "device_type", label: "نوع الجهاز", type: "select", options: [
      { value: "desktop", label: "مكتبي" }, { value: "laptop", label: "محمول" },
      { value: "mobile", label: "جوال" }, { value: "tablet", label: "لوحي" },
    ]},
    { value: "break_duration", label: "مدة الاستراحة", type: "number", unit: "دقيقة" },
    { value: "shift_hours", label: "ساعات الدوام", type: "number", unit: "ساعة" },
  ],
  notifications: [
    { value: "event", label: "الحدث", type: "select", options: [
      { value: "sla_warning", label: "تحذير SLA" }, { value: "sla_breach", label: "مخالفة SLA" },
      { value: "vip_waiting", label: "VIP ينتظر" }, { value: "new_complaint", label: "شكوى جديدة" },
      { value: "escalation", label: "تصعيد" }, { value: "long_idle", label: "خمول طويل" },
      { value: "missed_call", label: "مكالمة فائتة" },
    ]},
    { value: "recipient_role", label: "دور المستلم", type: "select", options: [
      { value: "agent", label: "وكيل" }, { value: "supervisor", label: "مشرف" },
      { value: "manager", label: "مدير" }, { value: "qa-supervisor", label: "مشرف مدققين" },
    ]},
    { value: "channel", label: "وسيلة التنبيه", type: "select", options: [
      { value: "in_app", label: "داخل النظام" }, { value: "email", label: "بريد" },
      { value: "sms", label: "رسالة قصيرة" }, { value: "whatsapp", label: "واتساب" },
    ]},
  ],
  vip: [
    { value: "total_spent", label: "إجمالي الإنفاق", type: "number", unit: "ر.س" },
    { value: "orders_count", label: "عدد الطلبات", type: "number" },
    { value: "months_active", label: "أشهر النشاط", type: "number", unit: "شهر" },
    { value: "satisfaction_avg", label: "متوسط الرضا", type: "number" },
    { value: "referrals_count", label: "عدد الإحالات", type: "number" },
    { value: "last_order_age", label: "عمر آخر طلب", type: "number", unit: "يوم" },
  ],
  automation: [
    { value: "trigger_event", label: "الحدث المحفز", type: "select", options: [
      { value: "new_conversation", label: "محادثة جديدة" },
      { value: "no_reply", label: "بدون رد" },
      { value: "call_ended", label: "انتهاء مكالمة" },
      { value: "ticket_created", label: "تكت جديد" },
      { value: "order_placed", label: "طلب جديد" },
      { value: "customer_inactive", label: "عميل خامل" },
    ]},
    { value: "time_elapsed", label: "الوقت المنقضي", type: "number", unit: "دقيقة" },
    { value: "customer.vip", label: "عميل VIP", type: "boolean" },
  ],
  products: [
    { value: "item.release_age", label: "عمر المنتج منذ الإصدار", type: "number", unit: "يوم" },
    { value: "item.price", label: "سعر المنتج", type: "number", unit: "ر.س" },
    { value: "item.in_stock", label: "متوفر في المخزون", type: "boolean" },
    { value: "item.section", label: "القسم", type: "select", options: [
      { value: "perfumes", label: "العطور" }, { value: "oils", label: "زجاج" },
      { value: "diffusers", label: "المعطرات" }, { value: "machines", label: "الأجهزة" },
      { value: "accessories", label: "الإكسسوارات" }, { value: "incense", label: "البخور" },
    ]},
    { value: "item.currency", label: "العملة", type: "select", options: [
      { value: "USD", label: "دولار" }, { value: "SAR", label: "ريال" },
      { value: "EUR", label: "يورو" }, { value: "AED", label: "درهم" },
    ]},
    { value: "brand.active", label: "العلامة نشطة", type: "boolean" },
  ],
};

// ── Mock Rules ───────────────────────────────────────────

export const defaultRules: Rule[] = [
  // ── SLA ─────────────────────────────────────────
  {
    id: "r-sla-01",
    name: "SLA — أول رد (عام)",
    description: "إذا لم يتم الرد على المحادثة خلال 3 دقائق → تحذير",
    category: "sla",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "first_response_time", fieldLabel: "وقت أول رد", operator: "greater_than", value: 3, unit: "دقيقة" },
    ],
    actions: [
      { id: "a1", type: "set_status", typeLabel: "تغيير الحالة", params: { status: "warning" }, paramsLabel: "SLA → تحذير" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor", channel: "in_app" }, paramsLabel: "تنبيه المشرف داخل النظام" },
    ],
    createdAt: "2026-01-15", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-sla-02",
    name: "SLA — أول رد (VIP)",
    description: "عميل VIP يجب الرد عليه خلال دقيقة واحدة",
    category: "sla",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "first_response_time", fieldLabel: "وقت أول رد", operator: "greater_than", value: 1, unit: "دقيقة" },
      { id: "c2", field: "customer.vip", fieldLabel: "عميل VIP", operator: "is_true", value: true },
    ],
    actions: [
      { id: "a1", type: "set_status", typeLabel: "تغيير الحالة", params: { status: "warning" }, paramsLabel: "SLA → تحذير" },
      { id: "a2", type: "notify", typeLabel: "إرسال تبيه", params: { to: "supervisor", channel: "in_app" }, paramsLabel: "تنبيه فوري للمشرف" },
      { id: "a3", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "manager", channel: "sms" }, paramsLabel: "رسالة SMS للمدير" },
    ],
    createdAt: "2026-01-15", updatedAt: "2026-02-22", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-sla-03",
    name: "SLA — مخالفة",
    description: "إذا تجاوز وقت الرد 5 دقائق → مخالفة SLA",
    category: "sla",
    enabled: true,
    priority: 2,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "response_time", fieldLabel: "وقت الاستجابة", operator: "greater_than", value: 5, unit: "دقيقة" },
    ],
    actions: [
      { id: "a1", type: "set_status", typeLabel: "تغيير الحالة", params: { status: "breached" }, paramsLabel: "SLA → مخالفة" },
      { id: "a2", type: "escalate", typeLabel: "تصعيد", params: { to: "supervisor" }, paramsLabel: "تصعيد للمشرف" },
      { id: "a3", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "sla_breach" }, paramsLabel: "تسجيل في Audit Log" },
    ],
    createdAt: "2026-01-15", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-sla-04",
    name: "SLA — وقت حل التكت",
    description: "التكت يجب أن يُحل خلال 24 ساعة",
    category: "sla",
    enabled: true,
    priority: 3,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "resolution_time", fieldLabel: "وقت الحل", operator: "greater_than", value: 24, unit: "ساعة" },
    ],
    actions: [
      { id: "a1", type: "escalate", typeLabel: "تصعيد", params: { to: "manager" }, paramsLabel: "تصعيد للمدير" },
      { id: "a2", type: "change_priority", typeLabel: "تغيير الأولوية", params: { priority: "high" }, paramsLabel: "رفع الأولوية → عالي" },
    ],
    createdAt: "2026-01-20", updatedAt: "2026-02-18", createdBy: "فهد الراشد",
    appliesTo: "all",
  },

  // ── Routing ────────────────────────────────────
  {
    id: "r-route-01",
    name: "توجيه VIP → وكيل VIP",
    description: "المحادثات من عملاء VIP تذهب لوكيل لديه مهارة VIP",
    category: "routing",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "customer.vip", fieldLabel: "عميل VIP", operator: "is_true", value: true },
      { id: "c2", field: "agent.status", fieldLabel: "حالة الوكيل", operator: "equals", value: "available", valueLabel: "متاح" },
      { id: "c3", field: "agent.skill", fieldLabel: "مهارة الوكيل", operator: "equals", value: "vip", valueLabel: "VIP" },
    ],
    actions: [
      { id: "a1", type: "assign_to", typeLabel: "تعيين إلى", params: { strategy: "least_busy" }, paramsLabel: "الأقل انشغالاً من وكلاء VIP" },
    ],
    createdAt: "2026-01-15", updatedAt: "2026-02-10", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-route-02",
    name: "توجيه الأقل محادثات",
    description: "توزيع على الوكيل ذو أقل عدد محادثات مفتوحة",
    category: "routing",
    enabled: true,
    priority: 5,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "agent.status", fieldLabel: "حالة الوكيل", operator: "equals", value: "available", valueLabel: "متاح" },
    ],
    actions: [
      { id: "a1", type: "assign_to", typeLabel: "تعيين إلى", params: { strategy: "least_conversations" }, paramsLabel: "الأقل محادثات مفتوحة" },
    ],
    createdAt: "2026-01-18", updatedAt: "2026-02-15", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-route-03",
    name: "توجيه الشكاوى → وكيل شكاوى",
    description: "الشكاوى توجّه لوكيل مختص",
    category: "routing",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "agent.skill", fieldLabel: "مهارة الوكيل", operator: "equals", value: "complaints", valueLabel: "شكاوى" },
    ],
    actions: [
      { id: "a1", type: "assign_to", typeLabel: "تعيين إلى", params: { strategy: "round_robin" }, paramsLabel: "توزيع دائري بين وكلاء الشكاوى" },
    ],
    createdAt: "2026-01-20", updatedAt: "2026-02-12", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },

  // ── Escalation ─────────────────────────────────
  {
    id: "r-esc-01",
    name: "تصعيد تلقائي — VIP منتظر",
    description: "إذا تكت عميل VIP لم يُحل خلال 4 ساعات",
    category: "escalation",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "ticket.age", fieldLabel: "عمر التكت", operator: "greater_than", value: 4, unit: "ساعة" },
      { id: "c2", field: "customer.vip", fieldLabel: "عميل VIP", operator: "is_true", value: true },
    ],
    actions: [
      { id: "a1", type: "escalate", typeLabel: "تصعيد", params: { to: "manager" }, paramsLabel: "تصعيد للمدير فوراً" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "manager", channel: "sms" }, paramsLabel: "SMS للمدير" },
    ],
    createdAt: "2026-01-20", updatedAt: "2026-02-18", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-esc-02",
    name: "تصعيد — إعادة فتح متكررة",
    description: "تكت أُعيد فتحه أكثر من مرتين → تصعيد",
    category: "escalation",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "ticket.reopened_count", fieldLabel: "عدد مرات إعادة الفتح", operator: "greater_than", value: 2 },
    ],
    actions: [
      { id: "a1", type: "escalate", typeLabel: "تصعيد", params: { to: "supervisor" }, paramsLabel: "تصعيد للمشرف" },
      { id: "a2", type: "change_priority", typeLabel: "تغيير الأولوية", params: { priority: "high" }, paramsLabel: "رفع الأولوية" },
    ],
    createdAt: "2026-02-01", updatedAt: "2026-02-15", createdBy: "فهد الراشد",
    appliesTo: "all",
  },

  // ── QA ──────────────────────────────────────────
  {
    id: "r-qa-01",
    name: "حد أدنى للاستماع",
    description: "المدقق يجب أن يستمع 60 ثانية على الأقل قبل التقييم",
    category: "qa",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "listen_duration", fieldLabel: "مدة الاستماع", operator: "less_than", value: 60, unit: "ثانية" },
    ],
    actions: [
      { id: "a1", type: "block", typeLabel: "حظر الإجراء", params: { action: "submit_evaluation" }, paramsLabel: "منع إرسال التقييم" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { message: "يجب الاستماع 60 ثانية على الأقل" }, paramsLabel: "تنبيه المدقق" },
    ],
    createdAt: "2026-01-25", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "qa",
  },
  {
    id: "r-qa-02",
    name: "تعريف «فتح وطلع»",
    description: "فتح مكالمة واستمع أقل من 15 ثانية بدون تقييم",
    category: "qa",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "listen_duration", fieldLabel: "مدة الاستماع", operator: "less_than", value: 15, unit: "ثانية" },
      { id: "c2", field: "has_score", fieldLabel: "أعطى درجة", operator: "is_false", value: false },
    ],
    actions: [
      { id: "a1", type: "tag", typeLabel: "إضافة وسم", params: { tag: "فتح_وطلع" }, paramsLabel: "وسم «فتح وطلع»" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "qa-supervisor" }, paramsLabel: "تنبيه مشرف المدققين" },
      { id: "a3", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "qa_opened_and_left" }, paramsLabel: "تسجيل في Audit Log" },
    ],
    createdAt: "2026-01-25", updatedAt: "2026-02-22", createdBy: "فهد الراشد",
    appliesTo: "qa",
  },
  {
    id: "r-qa-03",
    name: "حد أدنى للتقييمات اليومية",
    description: "المدقق يجب أن يُنجز 6 تقييمات في اليوم",
    category: "qa",
    enabled: true,
    priority: 2,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "evaluations_per_day", fieldLabel: "تقييمات اليوم", operator: "less_than", value: 6 },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "qa-supervisor", message: "إنتاجية منخفضة" }, paramsLabel: "تنبيه مشرف المدققين" },
    ],
    createdAt: "2026-02-01", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "qa",
  },

  // ── Attendance ──────────────────────────────────
  {
    id: "r-att-01",
    name: "حد التأخير",
    description: "إذا دخل بعد 5 دقائق من بداية الدوام → متأخر",
    category: "attendance",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "login_time", fieldLabel: "وقت الدخول", operator: "greater_than", value: 5, unit: "دقيقة بعد بداية الدوام" },
    ],
    actions: [
      { id: "a1", type: "set_status", typeLabel: "تغيير الحالة", params: { status: "late" }, paramsLabel: "حالة الحضور → متأخر" },
      { id: "a2", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "late_arrival" }, paramsLabel: "تسجيل في Audit Log" },
    ],
    createdAt: "2026-01-10", updatedAt: "2026-02-15", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-att-02",
    name: "تنبيه خمول طويل",
    description: "إذا كان الخمول أكثر من 15 دقيقة متواصلة",
    category: "attendance",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "idle_time", fieldLabel: "وقت الخمول", operator: "greater_than", value: 15, unit: "دقيقة" },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor" }, paramsLabel: "تنبيه المشرف" },
      { id: "a2", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "long_idle" }, paramsLabel: "تسجيل في Audit Log" },
    ],
    createdAt: "2026-01-15", updatedAt: "2026-02-18", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-att-03",
    name: "حد الاستراحة",
    description: "الاستراحة يجب ألا تتجاوز 30 دقيقة",
    category: "attendance",
    enabled: true,
    priority: 2,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "break_duration", fieldLabel: "مدة الاستراحة", operator: "greater_than", value: 30, unit: "دقيقة" },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor", message: "تجاوز وقت الاستراحة" }, paramsLabel: "تنبيه المشرف" },
      { id: "a2", type: "set_status", typeLabel: "تغيير الحالة", params: { status: "break_exceeded" }, paramsLabel: "استراحة متجاوزة" },
    ],
    createdAt: "2026-02-01", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "all",
  },

  // ── Notifications ───────────────────────────────
  {
    id: "r-notif-01",
    name: "تنبيه VIP ينتظر",
    description: "عميل VIP بالانتظار أكثر من 30 ثانية → تنبيه فوري",
    category: "notifications",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "event", fieldLabel: "الحدث", operator: "equals", value: "vip_waiting", valueLabel: "VIP ينتظر" },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor", channel: "in_app", sound: true }, paramsLabel: "تنبيه صوتي للمشرف" },
    ],
    createdAt: "2026-01-20", updatedAt: "2026-02-10", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-notif-02",
    name: "تنبيه شكوى جديدة",
    description: "عند فتح شكوى جديدة → تنبيه المشرف",
    category: "notifications",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "event", fieldLabel: "الحدث", operator: "equals", value: "new_complaint", valueLabel: "شكوى جديدة" },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor", channel: "in_app" }, paramsLabel: "تنبيه المشرف" },
    ],
    createdAt: "2026-02-01", updatedAt: "2026-02-15", createdBy: "فهد الراشد",
    appliesTo: "all",
  },

  // ── VIP ─────────────────────────────────────────
  {
    id: "r-vip-01",
    name: "ترقية لـ ذهبي",
    description: "إنفاق أكثر من 10,000 ر.س + 5 طلبات → ذهبي",
    category: "vip",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "total_spent", fieldLabel: "إجمالي الإنفاق", operator: "greater_equal", value: 10000, unit: "ر.س" },
      { id: "c2", field: "orders_count", fieldLabel: "عدد الطلبات", operator: "greater_equal", value: 5 },
    ],
    actions: [
      { id: "a1", type: "tag", typeLabel: "إضافة وسم", params: { segment: "gold" }, paramsLabel: "ترقية → ذهبي" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "agent", message: "عميل جديد بالشريحة الذهبية" }, paramsLabel: "إشعار الوكيل" },
    ],
    createdAt: "2026-01-10", updatedAt: "2026-02-10", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-vip-02",
    name: "ترقية لـ بلاتيني",
    description: "إنفاق أكثر من 40,000 ر.س + 15 طلب + 6 أشهر نشاط",
    category: "vip",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "total_spent", fieldLabel: "إجمالي الإنفاق", operator: "greater_equal", value: 40000, unit: "ر.س" },
      { id: "c2", field: "orders_count", fieldLabel: "عدد الطلبات", operator: "greater_equal", value: 15 },
      { id: "c3", field: "months_active", fieldLabel: "أشهر النشاط", operator: "greater_equal", value: 6, unit: "شهر" },
    ],
    actions: [
      { id: "a1", type: "tag", typeLabel: "إضافة وسم", params: { segment: "platinum" }, paramsLabel: "ترقية → بلاتيني" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor" }, paramsLabel: "إشعار المشرف" },
    ],
    createdAt: "2026-01-10", updatedAt: "2026-02-10", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-vip-03",
    name: "تخفيض — عدم نشاط",
    description: "عميل ذهبي/بلاتيني لم يطلب منذ 180 يوم → مراجعة",
    category: "vip",
    enabled: true,
    priority: 3,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "last_order_age", fieldLabel: "عمر آخر طلب", operator: "greater_than", value: 180, unit: "يوم" },
    ],
    actions: [
      { id: "a1", type: "create_task", typeLabel: "إنشاء مهمة", params: { title: "مراجعة تصنيف عميل خامل" }, paramsLabel: "مهمة مراجعة" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor" }, paramsLabel: "إشعار المشرف" },
    ],
    createdAt: "2026-02-01", updatedAt: "2026-02-18", createdBy: "ف��د الراشد",
    appliesTo: "all",
  },

  // ── Automation ──────────────────────────────────
  {
    id: "r-auto-01",
    name: "رد تلقائي — خارج الدوام",
    description: "رسائل خارج ساعات العمل → رد تلقائي",
    category: "automation",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "trigger_event", fieldLabel: "الحدث المحفز", operator: "equals", value: "new_conversation", valueLabel: "محادثة جديدة" },
    ],
    actions: [
      { id: "a1", type: "auto_reply", typeLabel: "رد تلقائي", params: { message: "شكراً لتواصلك مع نور النبراس. نحن خارج أوقات العمل حالياً. سنرد عليك في أقرب وقت خلال ساعات الدوام." }, paramsLabel: "رسالة خارج الدوام" },
    ],
    createdAt: "2026-01-15", updatedAt: "2026-02-15", createdBy: "فهد الراشد",
    appliesTo: "all",
    schedule: "خارج 08:00–20:00",
  },
  {
    id: "r-auto-02",
    name: "مهمة متابعة تلقائية بعد المكالمة",
    description: "بعد انتهاء مكالمة → إنشاء مهمة متابعة تلقائياً",
    category: "automation",
    enabled: false,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "trigger_event", fieldLabel: "الحدث المحفز", operator: "equals", value: "call_ended", valueLabel: "انتهاء مكالمة" },
    ],
    actions: [
      { id: "a1", type: "create_task", typeLabel: "إنشاء مهمة", params: { title: "متابعة بعد المكالمة", due: "24h" }, paramsLabel: "مهمة متابعة خلال 24 ساعة" },
    ],
    createdAt: "2026-02-10", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-auto-03",
    name: "إعادة تنشيط عميل خامل",
    description: "عميل لم يطلب منذ 90 يوم → إنشاء مهمة تواصل",
    category: "automation",
    enabled: true,
    priority: 2,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "trigger_event", fieldLabel: "الحدث المحفز", operator: "equals", value: "customer_inactive", valueLabel: "عميل خامل" },
      { id: "c2", field: "time_elapsed", fieldLabel: "الوقت المنقضي", operator: "greater_than", value: 129600, unit: "دقيقة" },
    ],
    actions: [
      { id: "a1", type: "create_task", typeLabel: "إنشاء مهمة", params: { title: "إعادة تنشيط عميل" }, paramsLabel: "مهمة تواصل مع عميل خامل" },
      { id: "a2", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "agent" }, paramsLabel: "إشعار الوكيل المسؤول" },
    ],
    createdAt: "2026-02-05", updatedAt: "2026-02-18", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },

  // ── Products ───────────────────────────────────
  {
    id: "r-prod-01",
    name: "عتبة «منتج جديد» — قائمة الأسعار",
    description: "المنتج يُعبر جديداً ويُميَّز ويُثبَّت أعلى القائمة إذا صدر خلال آخر 60 يوماً",
    category: "products",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "item.release_age", fieldLabel: "عمر المنتج منذ الإصدار", operator: "less_equal", value: 60, unit: "يوم" },
    ],
    actions: [
      { id: "a1", type: "tag", typeLabel: "إضافة وسم", params: { tag: "NEW" }, paramsLabel: "تمييز المنتج بعلامة NEW" },
      { id: "a2", type: "set_status", typeLabel: "تغيير الحالة", params: { pinned: true }, paramsLabel: "تثبيت أعلى القائمة" },
    ],
    createdAt: "2026-01-15", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-prod-02",
    name: "تنبيه نفاد المخزون",
    description: "إذا نفذ منتج من المخزون → تنبيه المشرف",
    category: "products",
    enabled: true,
    priority: 1,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "item.in_stock", fieldLabel: "متوفر في المخزون", operator: "is_false", value: false },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "supervisor" }, paramsLabel: "تنبيه المشرف بنفاد المنتج" },
      { id: "a2", type: "tag", typeLabel: "إضافة وسم", params: { tag: "out_of_stock" }, paramsLabel: "وسم «نفذ»" },
    ],
    createdAt: "2026-02-01", updatedAt: "2026-02-15", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
  {
    id: "r-prod-03",
    name: "منتج مرتفع السعر — مراجعة",
    description: "منتج سعره أكثر من 1000 ر.س يحتاج موافقة إضافية عند التعديل",
    category: "products",
    enabled: true,
    priority: 2,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "item.price", fieldLabel: "سعر المنتج", operator: "greater_than", value: 1000, unit: "ر.س" },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "manager" }, paramsLabel: "طلب موافقة المدير" },
      { id: "a2", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "high_price_edit" }, paramsLabel: "تسجيل في Audit Log" },
    ],
    createdAt: "2026-02-10", updatedAt: "2026-02-20", createdBy: "فهد الراشد",
    appliesTo: "all",
  },
];

// ── Omni-Channel + Ticket + Follow-up Rules (appended) ──
// These connect the Rule Engine to the new modules

export const omniChannelRules: Rule[] = [
  {
    id: "r-oc-01",
    name: "قفل المحادثة — موظف يكتب",
    description: "عند بدء موظف الكتابة في محادثة → قفل المحادثة للبقية",
    category: "automation",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "trigger_event", fieldLabel: "الحدث المحفز", operator: "equals", value: "agent_typing", valueLabel: "موظف بدأ الكتابة" },
    ],
    actions: [
      { id: "a1", type: "block", typeLabel: "حظر الإجراء", params: { action: "other_agents_write" }, paramsLabel: "منع الوكلاء الآخرين من الكتابة" },
      { id: "a2", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "conversation_locked" }, paramsLabel: "تسجيل القفل في Audit Log" },
    ],
    createdAt: "2026-02-15", updatedAt: "2026-02-23", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-oc-02",
    name: "ملكية تلقائية — أول مستجيب",
    description: "أول موظف يرد على المحادثة يصبح المالك تلقائياً",
    category: "routing",
    enabled: true,
    priority: 2,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "trigger_event", fieldLabel: "الحدث المحفز", operator: "equals", value: "first_reply", valueLabel: "أول رد" },
    ],
    actions: [
      { id: "a1", type: "assign_to", typeLabel: "تعيين إلى", params: { strategy: "first_responder" }, paramsLabel: "تعيين للمستجيب الأول" },
      { id: "a2", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "ownership_assigned" }, paramsLabel: "تسجيل الملكية" },
    ],
    createdAt: "2026-02-15", updatedAt: "2026-02-23", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-oc-03",
    name: "AI يتولى — خارج الدوام",
    description: "رسائل خارج ساعات العمل → بوت AI يتولى الكتالوج والأسعار والمخزون",
    category: "automation",
    enabled: true,
    priority: 0,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "trigger_event", fieldLabel: "الحدث المحفز", operator: "equals", value: "new_conversation", valueLabel: "محادثة جديدة" },
    ],
    actions: [
      { id: "a1", type: "auto_reply", typeLabel: "رد تلقائي", params: { ai: true, scope: "catalogue,prices,stock" }, paramsLabel: "تفعيل AI — كتالوج وأسعار ومخزون" },
      { id: "a2", type: "tag", typeLabel: "إضافة وسم", params: { tag: "ai_handled" }, paramsLabel: "وسم «معالج بواسطة AI»" },
      { id: "a3", type: "tag", typeLabel: "إضافة وسم", params: { tag: "follow_up_needed" }, paramsLabel: "وسم متابعة عند بدء الدوام" },
    ],
    createdAt: "2026-02-18", updatedAt: "2026-02-23", createdBy: "فهد الراشد",
    appliesTo: "all",
    schedule: "خارج 08:00–20:00",
  },
  {
    id: "r-oc-04",
    name: "تذكير الرد — X دقائق",
    description: "تذكير الموظف إذا مرت 5 دقائق بدون رد على رسالة عميل",
    category: "notifications",
    enabled: true,
    priority: 2,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "response_time", fieldLabel: "وقت الاستجابة", operator: "greater_than", value: 5, unit: "دقيقة" },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "agent", channel: "in_app" }, paramsLabel: "تذكير الموظف بالرد" },
    ],
    createdAt: "2026-02-20", updatedAt: "2026-02-23", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-oc-05",
    name: "قائمة اتصال — وقت فراغ",
    description: "عندما يكون الموظف متاح بدون مكالمة أو محادثة حرجة → إظهار قائمة الاتصال",
    category: "automation",
    enabled: true,
    priority: 3,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "agent.status", fieldLabel: "حالة الوكيل", operator: "equals", value: "available", valueLabel: "متاح" },
      { id: "c2", field: "agent.open_conversations", fieldLabel: "محادثات الوكيل المفتوحة", operator: "equals", value: 0 },
    ],
    actions: [
      { id: "a1", type: "notify", typeLabel: "إرسال تنبيه", params: { to: "agent", message: "لديك قائمة اتصالات واجبة التنفيذ" }, paramsLabel: "تنبيه بقائمة الاتصال" },
    ],
    createdAt: "2026-02-22", updatedAt: "2026-02-23", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
  {
    id: "r-oc-06",
    name: "فتح بدون رد — تتبع",
    description: "إذا فتح موظف محادثة وقرأها بدون رد → تسجيل كـ 'مفتوحة غير مرد عليها'",
    category: "qa",
    enabled: true,
    priority: 3,
    conditionLogic: "AND",
    conditions: [
      { id: "c1", field: "listen_duration", fieldLabel: "مدة الاستماع", operator: "greater_than", value: 0, unit: "ثانية" },
      { id: "c2", field: "has_score", fieldLabel: "أعطى درجة", operator: "is_false", value: false },
    ],
    actions: [
      { id: "a1", type: "log_event", typeLabel: "تسجيل حدث", params: { type: "opened_without_reply" }, paramsLabel: "تسجيل: فتح بدون رد" },
    ],
    createdAt: "2026-02-23", updatedAt: "2026-02-23", createdBy: "فهد الراشد",
    appliesTo: "agents",
  },
];

// Combine all rules
export const allRules: Rule[] = [...defaultRules, ...omniChannelRules];