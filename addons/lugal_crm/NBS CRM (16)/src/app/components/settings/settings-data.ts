// ═══════════════════════════════════════════════════════════
// Settings Data — Rule Engine & UI Configuration
// ═══════════════════════════════════════════════════════════

// ── Shared Rule Types ──────────────────────────────────────

export interface Rule {
  id: string;
  name: string;
  condition: string;
  action: string;
  priority: number;
  effectiveFrom: string;
  effectiveTo: string;
  enabled: boolean;
  category: string;
  description?: string;
  lastModified: string;
  modifiedBy: string;
}

export type RuleCategory =
  | "routing"
  | "vip"
  | "sla"
  | "kpi"
  | "ai"
  | "assignment";

export interface SettingsSection {
  id: string;
  label: string;
  icon: string;
  group: "ui" | "rules";
  description: string;
}

// ── Settings Sections ──────────────────────────────────────

export const settingsSections: SettingsSection[] = [
  // UI Group
  { id: "ui-theme", label: "المظهر والألوان", icon: "Palette", group: "ui", description: "إعدادات الثيم والألوان وأسلوب العرض" },
  { id: "ui-dashboard", label: "لوحة التحكم", icon: "LayoutDashboard", group: "ui", description: "تخصيص الويدجت وترتيب اللوحة" },
  { id: "ui-notifications", label: "الإشعارات", icon: "Bell", group: "ui", description: "تفضيلات عرض الإشعارات والتنبيهات" },
  { id: "ui-language", label: "اللغة والمنطقة", icon: "Globe", group: "ui", description: "اللغة والتنسيق الإقليمي والتقويم" },
  // Rules Group
  { id: "rules-routing", label: "قواعد التوجيه", icon: "Route", group: "rules", description: "توجيه المحادثات والتذاكر تلقائياً" },
  { id: "rules-vip", label: "قواعد VIP", icon: "Crown", group: "rules", description: "معاملة خاصة لعملاء VIP" },
  { id: "rules-sla", label: "قواعد SLA", icon: "Timer", group: "rules", description: "اتفاقيات مستوى الخدمة والمواعيد" },
  { id: "rules-kpi", label: "قواعد KPI", icon: "BarChart3", group: "rules", description: "حساب مؤشرات الأداء الرئيسية" },
  { id: "rules-ai", label: "قواعد الذكاء الاصطناعي", icon: "Brain", group: "rules", description: "صلاحيات ومحظورات الذكاء الاصطناعي" },
  { id: "rules-assignment", label: "قواعد التعيين", icon: "UserCog", group: "rules", description: "أولويات تعيين المهام للموظفين" },
];

// ── UI Settings Data ───────────────────────────────────────

export interface ThemeSetting {
  id: string;
  label: string;
  description: string;
  type: "toggle" | "select" | "slider" | "color";
  value: string | boolean | number;
  options?: { label: string; value: string }[];
}

export const themeSettings: ThemeSetting[] = [
  { id: "theme-mode", label: "وضع الثيم", description: "التبديل بين الوضع الداكن الذهبي والفاتح الفيروزي", type: "select", value: "dark-gold", options: [{ label: "داكن ذهبي", value: "dark-gold" }, { label: "فاتح فيروزي", value: "light-turquoise" }] },
  { id: "neumorphic", label: "تأثيرات Neumorphic", description: "تفعيل تأثيرات الظلال ثلاثية الأبعاد", type: "toggle", value: true },
  { id: "glassmorphic", label: "تأثيرات Glassmorphic", description: "تفعيل الشفافية والتمويه الزجاجي", type: "toggle", value: true },
  { id: "animations", label: "الأنيميشن", description: "تفعيل التحريكات والانتقالات", type: "toggle", value: true },
  { id: "sidebar-collapsed", label: "الشريط الجانبي مطوي", description: "عرض الشريط الجانبي بوضع مصغّر افتراضياً", type: "toggle", value: false },
  { id: "border-radius", label: "درجة الاستدارة", description: "نصف قطر الزوايا لعناصر الواجهة", type: "slider", value: 12 },
];

export interface DashboardWidget {
  id: string;
  label: string;
  description: string;
  visible: boolean;
  order: number;
  size: "sm" | "md" | "lg";
}

export const dashboardWidgets: DashboardWidget[] = [
  { id: "stats-overview", label: "نظرة عامة على الإحصائيات", description: "بطاقات الأرقام الرئيسية", visible: true, order: 1, size: "lg" },
  { id: "sales-chart", label: "مخطط المبيعات", description: "رسم بياني للمبيعات بالفترة", visible: true, order: 2, size: "md" },
  { id: "customer-segments", label: "شرائح العملاء", description: "توزيع العملاء حسب الفئة", visible: true, order: 3, size: "sm" },
  { id: "recent-interactions", label: "التفاعلات الأخيرة", description: "آخر المحادثات والتذاكر", visible: true, order: 4, size: "sm" },
  { id: "task-tracker", label: "متتبع المهام", description: "المهام المعلقة والمكتملة", visible: true, order: 5, size: "sm" },
  { id: "alerts", label: "التنبيهات", description: "تنبيهات النظام والمخزون", visible: true, order: 6, size: "sm" },
  { id: "customer-summary", label: "ملخص العملاء", description: "إحصائيات العملاء الجدد", visible: true, order: 7, size: "sm" },
  { id: "communication", label: "الاتصالات", description: "أحدث الرسائل المرسلة", visible: false, order: 8, size: "sm" },
  { id: "feedback", label: "التقييمات", description: "تقييمات وآراء العملاء", visible: true, order: 9, size: "sm" },
  { id: "forecasting", label: "التنبؤات", description: "توقعات المبيعات والمخزون", visible: true, order: 10, size: "md" },
];

export interface NotificationSetting {
  id: string;
  label: string;
  description: string;
  sound: boolean;
  popup: boolean;
  badge: boolean;
}

export const notificationSettings: NotificationSetting[] = [
  { id: "new-order", label: "طلب جديد", description: "عند استلام طلب جديد من أي قناة", sound: true, popup: true, badge: true },
  { id: "vip-alert", label: "تنبيه VIP", description: "عند تواصل عميل VIP أو بلاتيني", sound: true, popup: true, badge: true },
  { id: "sla-warning", label: "تحذير SLA", description: "عند اقتراب انتهاء وقت الاستجابة", sound: true, popup: true, badge: true },
  { id: "low-stock", label: "نقص مخزون", description: "عند وصول المخزون للحد الأدنى", sound: false, popup: true, badge: true },
  { id: "ticket-escalation", label: "تصعيد تذكرة", description: "عند تصعيد تذكرة دعم للمشرف", sound: true, popup: true, badge: true },
  { id: "agent-offline", label: "موظف غير متصل", description: "عند خروج موظف عن الخدمة", sound: false, popup: false, badge: true },
  { id: "ai-suggestion", label: "اقتراح ذكي", description: "عند توفر اقتراح من الذكاء الاصطناعي", sound: false, popup: false, badge: true },
  { id: "campaign-end", label: "انتهاء حملة", description: "عند اقتراب انتهاء حملة تسويقية", sound: false, popup: true, badge: true },
];

export interface LanguageSetting {
  id: string;
  label: string;
  type: "select" | "toggle";
  value: string | boolean;
  options?: { label: string; value: string }[];
}

export const languageSettings: LanguageSetting[] = [
  { id: "display-lang", label: "لغة العرض", type: "select", value: "ar", options: [{ label: "العربية", value: "ar" }, { label: "English", value: "en" }] },
  { id: "calendar", label: "نوع التقويم", type: "select", value: "hijri", options: [{ label: "هجري", value: "hijri" }, { label: "ميلادي", value: "gregorian" }, { label: "مزدوج", value: "dual" }] },
  { id: "currency", label: "العملة الافتراضية", type: "select", value: "SAR", options: [{ label: "ريال سعودي (SAR)", value: "SAR" }, { label: "دولار أمريكي (USD)", value: "USD" }, { label: "درهم إماراتي (AED)", value: "AED" }] },
  { id: "timezone", label: "المنطقة الزمنية", type: "select", value: "Asia/Riyadh", options: [{ label: "الرياض (GMT+3)", value: "Asia/Riyadh" }, { label: "دبي (GMT+4)", value: "Asia/Dubai" }, { label: "القاهرة (GMT+2)", value: "Africa/Cairo" }] },
  { id: "rtl", label: "اتجاه RTL", type: "toggle", value: true },
  { id: "number-format", label: "تنسيق الأرقام", type: "select", value: "ar", options: [{ label: "عربية (١٢٣)", value: "ar" }, { label: "هندية (123)", value: "en" }] },
];

// ── Rules Data ─────────────────────────────────────────────

export const routingRules: Rule[] = [
  { id: "RT-001", name: "توجيه واتساب VIP", condition: "القناة = واتساب AND فئة العميل = VIP", action: "توجيه إلى → فريق VIP المخصص", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "routing", description: "توجيه محادثات واتساب من عملاء VIP مباشرة لفريق الخدمة المميزة", lastModified: "2025-11-15", modifiedBy: "أحمد العلي" },
  { id: "RT-002", name: "توجيه مكالمات بعد الدوام", condition: "الوقت > 17:00 AND القناة = هاتف", action: "توجيه إلى → الرد الآلي + تسجيل رسالة", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "routing", description: "تحويل المكالمات خارج ساعات العمل للرد الآلي", lastModified: "2025-10-20", modifiedBy: "سارة الحربي" },
  { id: "RT-003", name: "توجيه شكاوى التوصيل", condition: "نوع التذكرة = شكوى AND الموضوع يحتوي 'توصيل'", action: "توجيه إلى → فريق اللوجستيك", priority: 3, effectiveFrom: "2025-03-01", effectiveTo: "2026-06-30", enabled: true, category: "routing", description: "توجيه شكاوى التوصيل مباشرة لفريق اللوجستيك", lastModified: "2025-09-10", modifiedBy: "خالد المطيري" },
  { id: "RT-004", name: "توجيه الاستفسارات العامة", condition: "نوع التذكرة = استفسار AND لا يوجد موظف متاح", action: "توجيه إلى → روبوت الدردشة الذكي", priority: 5, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "routing", description: "استخدام الذكاء الاصطناعي للرد على الاستفسارات العامة", lastModified: "2025-12-01", modifiedBy: "فهد العلي" },
  { id: "RT-005", name: "توجيه البريد الإلكتروني", condition: "القناة = بريد إلكتروني", action: "توجيه إلى → صندوق الوارد المشترك + تصنيف تلقائي", priority: 4, effectiveFrom: "2025-06-01", effectiveTo: "2026-12-31", enabled: false, category: "routing", description: "تصنيف وتوزيع رسائل البريد الإلكتروني تلقائياً", lastModified: "2025-08-15", modifiedBy: "أحمد العلي" },
  { id: "RT-006", name: "توجيه إنستغرام", condition: "القناة = إنستغرام AND نوع = رسالة مباشرة", action: "توجيه إلى → فريق التسويق الرقمي", priority: 6, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "routing", description: "رسائل إنستغرام تذهب لفريق التسويق", lastModified: "2025-11-28", modifiedBy: "سارة الحربي" },
];

export const vipRules: Rule[] = [
  { id: "VIP-001", name: "ترقية تلقائية لبلاتيني", condition: "إجمالي المشتريات ≥ 15,000 ر.س AND عدد الطلبات ≥ 10", action: "ترقية إلى → بلاتيني + إرسال رسالة ترحيب + خصم 15%", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "vip", description: "ترقية العملاء تلقائياً عند تجاوز الحد الأدنى", lastModified: "2025-11-01", modifiedBy: "أحمد العلي" },
  { id: "VIP-002", name: "ترقية ذهبي", condition: "إجمالي المشتريات ≥ 8,000 ر.س AND عدد الطلبات ≥ 5", action: "ترقية إلى → ذهبي + خصم 10% + شحن مجاني", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "vip", description: "ترقية للفئة الذهبية مع مزايا إضافية", lastModified: "2025-10-15", modifiedBy: "فهد العلي" },
  { id: "VIP-003", name: "تخفيض عند عدم النشاط", condition: "آخر شراء > 6 أشهر AND الفئة ≠ عادي", action: "تخفيض درجة واحدة + إرسال عرض استعادة 20%", priority: 3, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "vip", description: "تخفيض تلقائي للفئة مع محاولة استعادة العميل", lastModified: "2025-09-20", modifiedBy: "خالد المطيري" },
  { id: "VIP-004", name: "هدية عيد ميلاد VIP", condition: "اليوم = عيد ميلاد العميل AND الفئة ∈ [ذهبي, بلاتيني]", action: "إرسال قسيمة هدية 200 ر.س + رسالة تهنئة شخصية", priority: 4, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "vip", description: "إرسال هدايا تلقائية في أعياد الميلاد", lastModified: "2025-12-05", modifiedBy: "سارة الحربي" },
  { id: "VIP-005", name: "أولوية الدعم لبلاتيني", condition: "فئة العميل = بلاتيني AND نوع التواصل = دعم", action: "وضع في رأس القائمة + إشعار للمشرف + وقت استجابة ≤ 2 دقيقة", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "vip", description: "أولوية قصوى لعملاء بلاتيني في الدعم", lastModified: "2025-11-30", modifiedBy: "أحمد العلي" },
];

export const slaRules: Rule[] = [
  { id: "SLA-001", name: "استجابة أولى - عاجل", condition: "الأولوية = عاجل", action: "وقت الاستجابة الأولى ≤ 5 دقائق + تصعيد تلقائي بعد 3 دقائق", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "sla", description: "أسرع استجابة للتذاكر العاجلة", lastModified: "2025-10-01", modifiedBy: "أحمد العلي" },
  { id: "SLA-002", name: "استجابة أولى - عالي", condition: "الأولوية = عالي", action: "وقت الاستجابة الأولى ≤ 15 دقيقة", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "sla", description: "استجابة سريعة للأولوية العالية", lastModified: "2025-10-01", modifiedBy: "أحمد العلي" },
  { id: "SLA-003", name: "استجابة أولى - عادي", condition: "الأولوية = عادي", action: "وقت الاستجابة الأولى ≤ 30 دقيقة", priority: 3, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "sla", description: "استجابة ضمن نصف ساعة للتذاكر العادية", lastModified: "2025-10-01", modifiedBy: "فهد العلي" },
  { id: "SLA-004", name: "وقت الحل - شكوى", condition: "نوع التذكرة = شكوى", action: "وقت الحل ≤ 4 ساعات + إشعار كل ساعة للمسؤول", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "sla", description: "حل الشكاوى خلال 4 ساعات", lastModified: "2025-09-15", modifiedBy: "خالد المطيري" },
  { id: "SLA-005", name: "تصعيد تلقائي", condition: "وقت الاستجابة > الحد المسموح × 1.5", action: "تصعيد للمشرف + إشعار للمدير + تسجيل مخالفة", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "sla", description: "تصعيد تلقائي عند تجاوز وقت SLA", lastModified: "2025-11-20", modifiedBy: "سارة الحربي" },
  { id: "SLA-006", name: "SLA عطلة نهاية الأسبوع", condition: "اليوم ∈ [الجمعة, السبت]", action: "مضاعفة الأوقات المسموحة × 2", priority: 4, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "sla", description: "أوقات SLA مرنة في العطلات", lastModified: "2025-08-10", modifiedBy: "أحمد العلي" },
];

export const kpiRules: Rule[] = [
  { id: "KPI-001", name: "معدل رضا العملاء (CSAT)", condition: "المقياس = CSAT AND الفترة = شهري", action: "حساب = متوسط التقييمات ÷ 5 × 100 | الهدف ≥ 90%", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "kpi", description: "قياس رضا العملاء شهرياً", lastModified: "2025-10-01", modifiedBy: "أحمد العلي" },
  { id: "KPI-002", name: "معدل حل المشكلة من أول تواصل (FCR)", condition: "المقياس = FCR AND القسم = الدعم", action: "حساب = (تذاكر محلولة من أول رد ÷ إجمالي التذاكر) × 100 | الهدف ≥ 75%", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "kpi", description: "نسبة حل المشكلات من التواصل الأول", lastModified: "2025-09-15", modifiedBy: "فهد العلي" },
  { id: "KPI-003", name: "متوسط وقت المعالجة (AHT)", condition: "المقياس = AHT AND القسم = مركز الاتصال", action: "حساب = مجموع أوقات المكالمات ÷ عدد المكالمات | الهدف ≤ 6 دقائق", priority: 3, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "kpi", description: "متوسط وقت معالجة المكالمة", lastModified: "2025-11-01", modifiedBy: "خالد المطيري" },
  { id: "KPI-004", name: "معدل التحويل (Conversion Rate)", condition: "المقياس = تحويل AND القناة = الكل", action: "حساب = (طلبات مكتملة ÷ إجمالي الزيارات) × 100 | الهدف ≥ 3.5%", priority: 4, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "kpi", description: "نسبة تحويل الزوار لمشترين", lastModified: "2025-10-20", modifiedBy: "سارة الحربي" },
  { id: "KPI-005", name: "صافي نقاط الترويج (NPS)", condition: "المقياس = NPS AND الفترة = ربع سنوي", action: "حساب = (% مروجين - % منتقدين) | الهدف ≥ 50", priority: 5, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "kpi", description: "مؤشر ولاء العملاء الربع سنوي", lastModified: "2025-12-01", modifiedBy: "أحمد العلي" },
  { id: "KPI-006", name: "إنتاجية الموظف", condition: "المقياس = إنتاجية AND الدور = موظف دعم", action: "حساب = (تذاكر محلولة × وزن + مكالمات × وزن) ÷ ساعات العمل | الهدف ≥ 8/ساعة", priority: 6, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "kpi", description: "قياس إنتاجية الموظفين اليومية", lastModified: "2025-11-15", modifiedBy: "فهد العلي" },
];

export const aiRules: Rule[] = [
  { id: "AI-001", name: "السماح بالرد التلقائي", condition: "نوع السؤال = استفسار عام AND الثقة ≥ 85%", action: "السماح → رد تلقائي مع توقيع 'مساعد نور النبراس الذكي'", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "ai", description: "رد تلقائي على الأسئلة الشائعة بثقة عالية", lastModified: "2025-11-01", modifiedBy: "أحمد العلي" },
  { id: "AI-002", name: "منع تعديل الأسعار", condition: "الإجراء = تعديل سعر OR الإجراء = منح خصم > 10%", action: "منع → تحويل لموظف بشري + تسجيل المحاولة", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "ai", description: "الذكاء الاصطناعي لا يمكنه تغيير الأسعار", lastModified: "2025-10-15", modifiedBy: "فهد العلي" },
  { id: "AI-003", name: "منع الوعود المالية", condition: "المحتوى يحتوي وعد مالي OR ضمان استرداد غير معتمد", action: "منع → تنبيه المشرف + حظر الرسالة", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "ai", description: "منع أي وعود مالية غير مصرح بها", lastModified: "2025-09-20", modifiedBy: "خالد المطيري" },
  { id: "AI-004", name: "السماح باقتراح المنتجات", condition: "السياق = محادثة بيع AND العميل طلب توصية", action: "السماح → اقتراح حتى 3 منتجات بناءً على سجل المشتريات", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "ai", description: "اقتراحات ذكية للمنتجات المناسبة", lastModified: "2025-12-01", modifiedBy: "سارة الحربي" },
  { id: "AI-005", name: "منع مشاركة بيانات حساسة", condition: "الرد يحتوي رقم هاتف عميل آخر OR بيانات مالية", action: "منع → حذف البيانات + تنبيه أمني", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "ai", description: "حماية البيانات الشخصية والمالية", lastModified: "2025-11-10", modifiedBy: "أحمد العلي" },
  { id: "AI-006", name: "السماح بتلخيص المحادثات", condition: "الإجراء = تلخيص AND المحادثة منتهية", action: "السماح → إنشاء ملخص + حفظ في سجل العميل", priority: 3, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "ai", description: "تلخيص تلقائي للمحادثات المنتهية", lastModified: "2025-10-05", modifiedBy: "فهد العلي" },
  { id: "AI-007", name: "منع إلغاء الطلبات", condition: "الإجراء = إلغاء طلب AND قيمة الطلب > 500 ر.س", action: "منع → تحويل لمشرف + طلب تأكيد يدوي", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: false, category: "ai", description: "إلغاء الطلبات الكبيرة يتطلب تدخل بشري", lastModified: "2025-08-25", modifiedBy: "خالد المطيري" },
];

export const assignmentRules: Rule[] = [
  { id: "ASN-001", name: "توزيع متوازن", condition: "عدد تذاكر الموظف < المتوسط AND حالته = متصل", action: "تعيين → الموظف الأقل تذاكر نشطة", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "assignment", description: "توزيع عادل للتذاكر بين الموظفين", lastModified: "2025-11-01", modifiedBy: "أحمد العلي" },
  { id: "ASN-002", name: "تعيين حسب المهارة", condition: "التذكرة تتطلب مهارة = 'عطور فاخرة' AND الموظف لديه المهارة", action: "تعيين → الموظف المتخصص في العطور الفاخرة", priority: 2, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "assignment", description: "مطابقة التذاكر مع مهارات الموظفين", lastModified: "2025-10-20", modifiedBy: "فهد العلي" },
  { id: "ASN-003", name: "تعيين VIP لموظف مخصص", condition: "فئة العميل = بلاتيني AND موظف العميل المخصص متصل", action: "تعيين → موظف العميل المخصص حصرياً", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "assignment", description: "عملاء بلاتيني يحصلون على موظف مخصص", lastModified: "2025-09-15", modifiedBy: "خالد المطيري" },
  { id: "ASN-004", name: "تصعيد عدم الاستجابة", condition: "لا يوجد رد بعد 5 دقائق AND الأولوية ≥ عالي", action: "إعادة تعيين → الموظف التالي المتاح + إشعار المشرف", priority: 1, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "assignment", description: "إعادة تعيين تلقائي عند عدم الاستجابة", lastModified: "2025-12-01", modifiedBy: "سارة الحربي" },
  { id: "ASN-005", name: "تعيين لغوي", condition: "لغة العميل = English AND الموظف يتحدث الإنجليزية", action: "تعيين → الموظف ثنائي اللغة", priority: 3, effectiveFrom: "2025-01-01", effectiveTo: "2026-12-31", enabled: true, category: "assignment", description: "مطابقة لغة العميل مع الموظف", lastModified: "2025-11-15", modifiedBy: "أحمد العلي" },
];

// ── Helper to get rules by category ────────────────────────

export function getRulesByCategory(category: RuleCategory): Rule[] {
  const map: Record<RuleCategory, Rule[]> = {
    routing: routingRules,
    vip: vipRules,
    sla: slaRules,
    kpi: kpiRules,
    ai: aiRules,
    assignment: assignmentRules,
  };
  return map[category] ?? [];
}

export const ruleCategoryLabels: Record<RuleCategory, string> = {
  routing: "قواعد التوجيه",
  vip: "قواعد VIP",
  sla: "قواعد SLA",
  kpi: "قواعد KPI",
  ai: "قواعد الذكاء الاصطناعي",
  assignment: "قواعد التعيين",
};

export const ruleCategoryDescriptions: Record<RuleCategory, string> = {
  routing: "تحديد كيفية توجيه المحادثات والتذاكر إلى الفرق والموظفين المناسبين تلقائياً",
  vip: "إدارة ترقية وتخفيض فئات العملاء ومعاملتهم الخاصة حسب قيمتهم",
  sla: "تحديد أوقات الاستجابة والحل المطلوبة وآليات التصعيد التلقائي",
  kpi: "تعريف معادلات حساب مؤشرات الأداء وأهدافها ودورياتها",
  ai: "تحديد الصلاحيات والمحظورات لتصرفات الذكاء الاصطناعي في النظام",
  assignment: "قواعد توزيع المهام والتذاكر على الموظفين بناءً على أولويات محددة",
};
