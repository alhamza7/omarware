// Shared mock data for the Knowledge Base

export interface Article {
  id: string;
  title: string;
  excerpt: string;
  category: string;
  author: string;
  date: string;
  readTime: string;
  views: number;
  pinned?: boolean;
}

export interface Event {
  id: string;
  title: string;
  description: string;
  date: string;
  time: string;
  location: string;
  type: "workshop" | "meeting" | "celebration" | "training" | "survey";
  status: "upcoming" | "ongoing" | "completed";
  attendees: number;
  maxAttendees?: number;
}

export interface Circular {
  id: string;
  title: string;
  content: string;
  date: string;
  priority: "high" | "medium" | "low";
  department: string;
  author: string;
  read: boolean;
}

export interface Idea {
  id: string;
  title: string;
  description: string;
  author: string;
  authorRole: string;
  date: string;
  votes: number;
  comments: number;
  status: "new" | "under-review" | "approved" | "implemented" | "declined";
  category: string;
  userVoted?: boolean;
}

export interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
  helpful: number;
  views: number;
}

export interface TrainingCourse {
  id: string;
  title: string;
  description: string;
  duration: string;
  level: "beginner" | "intermediate" | "advanced";
  progress: number;
  modules: number;
  completedModules: number;
  instructor: string;
  category: string;
}

export interface Document {
  id: string;
  title: string;
  type: "pdf" | "doc" | "xlsx" | "pptx";
  category: string;
  size: string;
  updatedAt: string;
  downloads: number;
}

// ── Mock Data ──────────────────────────────────────────

export const companyPolicies: Article[] = [
  {
    id: "p1",
    title: "رؤية ورسالة نور النبراس",
    excerpt: "نسعى لنكون الوجهة الأولى للعطور الفاخرة في المنطقة، مع الحفاظ على أصالة التراث العربي وابتكار تركيبات عصرية تلبي أذواق العملاء المميزين.",
    category: "عن الشركة",
    author: "إدارة الشركة",
    date: "2025-01-01",
    readTime: "5 دقائق",
    views: 342,
    pinned: true,
  },
  {
    id: "p2",
    title: "سياسة الجودة والمعايير",
    excerpt: "نلتزم بأعلى معايير الجودة في اختيار المواد الخام وعمليات التصنيع، مع شهادات ISO المعتمدة وفحوصات دورية لضمان التميز.",
    category: "سياسات",
    author: "قسم الجودة",
    date: "2025-03-15",
    readTime: "8 دقائق",
    views: 218,
    pinned: true,
  },
  {
    id: "p3",
    title: "دليل الموظف الشامل",
    excerpt: "يحتوي هذا الدليل على جميع المعلومات التي يحتاجها الموظف الجديد بما في ذلك ساعات العمل، الإجازات، المزايا، وقواعد السلوك المهني.",
    category: "سياسات",
    author: "الموارد البشرية",
    date: "2025-02-10",
    readTime: "15 دقيقة",
    views: 456,
  },
  {
    id: "p4",
    title: "سياسة الخصوصية وحماية البيانات",
    excerpt: "نحرص على حماية بيانات العملاء والموظفين وفقاً لأحدث المعايير الدولية ونظام حماية البيانات الشخصية في المملكة.",
    category: "سياسات",
    author: "القسم القانوني",
    date: "2025-04-01",
    readTime: "10 دقائق",
    views: 189,
  },
  {
    id: "p5",
    title: "هيكل الشركة التنظيمي",
    excerpt: "التعريف بالأقسام المختلفة في الشركة ومسؤولياتها وكيفية التواصل بين الإدارات لضمان سير العمل بكفاءة.",
    category: "عن الشركة",
    author: "إدارة الشركة",
    date: "2025-01-20",
    readTime: "7 دقائق",
    views: 275,
  },
  {
    id: "p6",
    title: "سياسة خدمة العملاء المتميزة",
    excerpt: "معايير التعامل مع العملاء وأسس تقديم تجربة فاخرة تليق بعلامة نور النبراس التجارية.",
    category: "سياسات",
    author: "قسم خدمة العملاء",
    date: "2025-05-10",
    readTime: "12 دقيقة",
    views: 321,
  },
];

export const journals: Article[] = [
  {
    id: "j1",
    title: "أسرار صناعة العود: من الغابة إلى القارورة",
    excerpt: "رحلة مفصلة عن كيفية استخراج دهن العود من أشجار الأقار وعمليات التقطير التقليدية والحديثة المستخدمة في نور النبراس.",
    category: "صناعة العطور",
    author: "محمد الخبير",
    date: "2026-02-15",
    readTime: "12 دقيقة",
    views: 523,
  },
  {
    id: "j2",
    title: "اتجاهات العطور لعام 2026",
    excerpt: "تحليل شامل لأحدث اتجاهات صناعة العطور العالمية وكيف يمكننا الاستفادة منها في تطوير مجموعاتنا القادمة.",
    category: "تحليلات السوق",
    author: "سارة المحلل",
    date: "2026-02-10",
    readTime: "8 دقائق",
    views: 387,
  },
  {
    id: "j3",
    title: "تجربة العميل الفاخرة: دراسة حالة",
    excerpt: "كيف نجحنا في رفع معدل رضا العملاء بنسبة 40% خلال الربع الأخير من خلال تطبيق استراتيجية التجربة المتكاملة.",
    category: "تجربة العميل",
    author: "ريم التسويق",
    date: "2026-01-28",
    readTime: "10 دقائق",
    views: 445,
  },
  {
    id: "j4",
    title: "الورد الطائفي: كنز المملكة العطري",
    excerpt: "استكشاف عمق وتاريخ الورد الطائفي كأحد أفخم المكونات العطرية وأهميته في تركيبات نور النبراس.",
    category: "صناعة العطور",
    author: "أحمد العطّار",
    date: "2026-01-15",
    readTime: "6 دقائق",
    views: 612,
  },
  {
    id: "j5",
    title: "التسويق الرقمي في عالم العطور الفاخرة",
    excerpt: "استراتيجيات فعّالة لتسويق العطور الفاخرة عبر القنوات الرقمية مع الحفاظ على هوية العلامة التجارية.",
    category: "تسويق",
    author: "نورة الإعلام",
    date: "2026-02-01",
    readTime: "9 دقائق",
    views: 298,
  },
];

export const events: Event[] = [
  {
    id: "e1",
    title: "ورشة عمل: فن مزج العطور",
    description: "ورشة تفاعلية لتعلم أساسيات مزج العطور وإنشاء تركيبات شخصية فريدة تحت إشراف خبراء نور النبراس.",
    date: "2026-03-05",
    time: "10:00 - 14:00",
    location: "الفرع الرئيسي - الرياض",
    type: "workshop",
    status: "upcoming",
    attendees: 12,
    maxAttendees: 20,
  },
  {
    id: "e2",
    title: "الاجتماع الشهري للفريق",
    description: "مراجعة أداء الشهر السابق ومناقشة الأهداف والخطط للشهر القادم مع عرض النتائج المالية.",
    date: "2026-03-01",
    time: "09:00 - 11:00",
    location: "قاعة الاجتماعات الرئيسية",
    type: "meeting",
    status: "upcoming",
    attendees: 25,
  },
  {
    id: "e3",
    title: "استبيان رضا الموظفين 2026",
    description: "استبيان سري لقياس مستوى رضا الموظفين وجمع الاقتراحات لتحسين بيئة العمل. يرجى المشاركة قبل نهاية المهلة.",
    date: "2026-02-28",
    time: "طوال اليوم",
    location: "إلكتروني",
    type: "survey",
    status: "ongoing",
    attendees: 18,
    maxAttendees: 45,
  },
  {
    id: "e4",
    title: "احتفال يوم التأسيس",
    description: "احتفال بمناسبة الذكرى الخامسة لتأسيس نور النبراس مع حفل عشاء وتكريم الموظفين المتميزين.",
    date: "2026-04-10",
    time: "18:00 - 22:00",
    location: "فندق الريتز كارلتون - الرياض",
    type: "celebration",
    status: "upcoming",
    attendees: 40,
    maxAttendees: 50,
  },
  {
    id: "e5",
    title: "دورة تدريبية: خدمة العملاء VIP",
    description: "برنامج تدريبي متخصص في التعامل مع عملاء الفئة الخاصة وتقديم تجربة خدمة استثنائية.",
    date: "2026-02-20",
    time: "09:00 - 16:00",
    location: "مركز التدريب",
    type: "training",
    status: "completed",
    attendees: 15,
    maxAttendees: 15,
  },
];

export const circulars: Circular[] = [
  {
    id: "c1",
    title: "تحديث ساعات العمل خلال شهر رمضان",
    content: "يسرنا إبلاغكم بتعديل ساعات العمل خ��ال شهر رمضان المبارك. ستكون ساعات العمل من 10 صباحاً حتى 3 عصراً، ومن 9 مساءً حتى 1 صباحاً لفروع البيع.",
    date: "2026-02-20",
    priority: "high",
    department: "الموارد البشرية",
    author: "مدير الموارد البشرية",
    read: false,
  },
  {
    id: "c2",
    title: "إطلاق مجموعة عطور الربيع الجديدة",
    content: "نفخر بالإعلان عن إطلاق مجموعة 'نسمات الربيع' المكونة من 5 عطور جديدة. يرجى الاطلاع على المواد التسويقية المرفقة.",
    date: "2026-02-18",
    priority: "medium",
    department: "التسويق",
    author: "مدير التسويق",
    read: true,
  },
  {
    id: "c3",
    title: "تحديث نظام إدارة المخزون",
    content: "سيتم تحديث نظام إدارة المخزون يوم السبت القادم. يرجى التأكد من إدخال جميع البيانات المعلقة قبل الموعد المحدد.",
    date: "2026-02-15",
    priority: "high",
    department: "تقنية المعلومات",
    author: "مدير التقنية",
    read: false,
  },
  {
    id: "c4",
    title: "برنامج مكافآت الموظف المثالي",
    content: "يسعدنا الإعلان عن تفعيل برنامج 'نجم نور النبراس' لمكافأة الموظفين المتميزين شهرياً بجوائز مالية وعينية.",
    date: "2026-02-12",
    priority: "medium",
    department: "الموارد البشرية",
    author: "المدير العام",
    read: true,
  },
  {
    id: "c5",
    title: "إجراءات السلامة المحدّثة",
    content: "تم تحديث إجراءات السلامة في مختبرات التصنيع. يرجى من جميع موظفي قسم الإنتاج حضور الجلسة التوعوية.",
    date: "2026-02-08",
    priority: "low",
    department: "السلامة",
    author: "مسؤول السلامة",
    read: true,
  },
];

export const ideas: Idea[] = [
  {
    id: "i1",
    title: "خدمة تخصيص العطور عبر الإنترنت",
    description: "إتاحة خدمة إلكترونية تسمح للعملاء بتصميم عطرهم الخاص من خلال اختيار المكونات والتركيزات عبر موقعنا.",
    author: "سارة الحربي",
    authorRole: "موظفة",
    date: "2026-02-18",
    votes: 47,
    comments: 12,
    status: "approved",
    category: "منتجات",
    userVoted: true,
  },
  {
    id: "i2",
    title: "برنامج ولاء متدرج للعملاء",
    description: "تطوير برنامج ولاء بأربع مستويات (فضي، ذهبي، بلاتيني، ألماسي) مع مزايا حصرية لكل مستوى.",
    author: "خالد القحطاني",
    authorRole: "عميل VIP",
    date: "2026-02-15",
    votes: 35,
    comments: 8,
    status: "under-review",
    category: "خدمة العملاء",
  },
  {
    id: "i3",
    title: "تطبيق الواقع المعزز لتجربة العطور",
    description: "استخدام تقنية AR لمحاكاة تجربة العطر عبر الهاتف قبل الشراء مع عرض مكونات كل عطر بشكل تفاعلي.",
    author: "أحمد العلي",
    authorRole: "موظف",
    date: "2026-02-10",
    votes: 28,
    comments: 15,
    status: "new",
    category: "تقنية",
  },
  {
    id: "i4",
    title: "شراكة مع فنادق خمس نجوم",
    description: "توفير عطور نور النبراس الحصرية في أجنحة كبار الزوار بالفنادق الفاخرة كهدايا ترحيبية مع بطاقة المتجر.",
    author: "نورة الشمري",
    authorRole: "شريك تجاري",
    date: "2026-02-05",
    votes: 52,
    comments: 6,
    status: "implemented",
    category: "شراكات",
    userVoted: true,
  },
  {
    id: "i5",
    title: "مختبر عطور مفتوح للزوار",
    description: "فتح جزء من المختبر للزوار لمشاهدة عملية صنع العطور وتجربة مكونات خام مختلفة بشكل تفاعلي.",
    author: "فاطمة السالم",
    authorRole: "موظفة",
    date: "2026-01-28",
    votes: 19,
    comments: 4,
    status: "declined",
    category: "تجربة العميل",
  },
  {
    id: "i6",
    title: "خط عطور صديق للبيئة",
    description: "تطوير مجموعة عطور بمكونات طبيعية 100% مع عبوات قابلة لإعادة التدوير لجذب شريحة العملاء المهتمين بالاستدامة.",
    author: "ماجد السبيعي",
    authorRole: "موظف",
    date: "2026-02-20",
    votes: 41,
    comments: 9,
    status: "new",
    category: "منتجات",
  },
];

export const faqs: FAQ[] = [
  {
    id: "f1",
    question: "كيف أقدم طلب إجازة؟",
    answer: "يمكنك تقديم طلب الإجازة عبر نظام الموارد البشرية الإلكتروني. ادخل إلى حسابك > طلبات الإجازة > طلب جديد. يجب تقديم الطلب قبل 5 أيام عمل على الأقل للإجازات العادية، و30 يوماً للإجاز��ت الطويلة.",
    category: "الموارد البشرية",
    helpful: 89,
    views: 234,
  },
  {
    id: "f2",
    question: "ما هي سياسة الخصومات للموظفين؟",
    answer: "يحصل جميع الموظفين على خصم 30% على منتجات نور النبراس. الموظفون بعد سنة من الخدمة يحصلون على 40%. كما يمكن الحصول على خصم 20% لأفراد العائلة من الدرجة الأولى بحد أقصى 3 طلبات شهرياً.",
    category: "المزايا",
    helpful: 156,
    views: 445,
  },
  {
    id: "f3",
    question: "كيف أتعامل مع شكوى عميل حول جودة المنتج؟",
    answer: "اتبع الخطوات التالية: 1) استمع للعميل باهتمام وتعاطف. 2) اعتذر عن الإزعاج. 3) سجّل الشكوى في النظام. 4) اعرض الاستبدال الفوري أو الاسترداد. 5) أحل المنتج لقسم الجودة. 6) تابع مع العميل خلال 48 ساعة.",
    category: "خدمة العملاء",
    helpful: 203,
    views: 567,
  },
  {
    id: "f4",
    question: "ما هي إجراءات فتح وإغلاق الفرع؟",
    answer: "الفتح: الحضور قبل 30 دقيقة من الافتتاح، فحص المخزون، تشغيل الأنظمة، ترتيب العرض. الإغلاق: مراجعة المبيعات، إغلاق الصندوق، تأمين المنتجات الثمينة في الخزنة، تفعيل نظام الأمان.",
    category: "العمليات",
    helpful: 78,
    views: 189,
  },
  {
    id: "f5",
    question: "كيف أستخدم نظام نقاط البيع (POS)؟",
    answer: "سجّل الدخول بحسابك > مسح المنتج أو البحث بالاسم > إضافة للسلة > اختيار طريقة الدفع > إتمام العملية. للعملاء المسجلين، تأكد من إدخال رقم العضوية لاحتساب النقاط.",
    category: "الأنظمة",
    helpful: 134,
    views: 378,
  },
  {
    id: "f6",
    question: "ما هي سياسة الاستبدال والاسترجاع؟",
    answer: "يحق للعميل الاستبدال خلال 14 يوم من الشراء بشرط عدم فتح العبوة. الاسترجاع خلال 7 أيام للمنتجات غير المفتوحة. المنتجات المخصصة (Custom) غير قابلة للاسترجاع.",
    category: "خدمة العملاء",
    helpful: 167,
    views: 489,
  },
  {
    id: "f7",
    question: "كيف أرفع تقرير مبيعات يومي؟",
    answer: "من نظام الإدارة > التقارير > تقرير يومي > اختر الفرع والتاريخ > مراجعة البيانات > إرسال. يجب رفع التقرير قبل 10 مساءً يومياً.",
    category: "العمليات",
    helpful: 92,
    views: 256,
  },
  {
    id: "f8",
    question: "ما هي معايير تخزين العطور في المستودع؟",
    answer: "درجة الحرارة: 15-25 مئوية. الرطوبة: أقل من 60%. بعيداً عن أشعة الشمس المباشرة. تخزين عمودي للقوارير. فحص دوري كل أسبوعين. تسجيل درجات الحرارة ثلاث مرات يومياً.",
    category: "الجودة",
    helpful: 56,
    views: 143,
  },
];

export const trainingCourses: TrainingCourse[] = [
  {
    id: "t1",
    title: "أساسيات علم العطور",
    description: "تعلم المفاهيم الأساسية في علم العطور: العائلات العطرية، الطبقات، التركيز، وكيفية وصف الروائح بشكل احترافي.",
    duration: "6 ساعات",
    level: "beginner",
    progress: 100,
    modules: 8,
    completedModules: 8,
    instructor: "أ. محمد العطّار",
    category: "المنتجات",
  },
  {
    id: "t2",
    title: "فن البيع الفاخر",
    description: "تقنيات البيع المتقدمة للمنتجات الفاخرة: قراءة العميل، تقديم التجربة، التوصيات الشخصية، وإغلاق البيع.",
    duration: "8 ساعات",
    level: "intermediate",
    progress: 65,
    modules: 10,
    completedModules: 6,
    instructor: "أ. سارة المبيعات",
    category: "المبيعات",
  },
  {
    id: "t3",
    title: "إدارة علاقات العملاء CRM",
    description: "التدريب على استخدام نظام إدارة علاقات العملاء بكفاءة لتتبع التفاعلات وتحسين تجربة العميل.",
    duration: "4 ساعات",
    level: "beginner",
    progress: 30,
    modules: 6,
    completedModules: 2,
    instructor: "م. خالد التقنية",
    category: "الأنظمة",
  },
  {
    id: "t4",
    title: "التميز في خدمة عملاء VIP",
    description: "برنامج متقدم للتعامل مع عملاء الفئة الخاصة وتقديم تجربة خدمة استثنائية تفوق التوقعات.",
    duration: "10 ساعات",
    level: "advanced",
    progress: 0,
    modules: 12,
    completedModules: 0,
    instructor: "أ. ريم الخدمات",
    category: "خدمة العملاء",
  },
  {
    id: "t5",
    title: "مهارات التواصل الفعّال",
    description: "تطوير مهارات التواصل اللفظي وغير اللفظي مع العملاء والزملاء لبناء علاقات مهنية قوية.",
    duration: "5 ساعات",
    level: "beginner",
    progress: 80,
    modules: 7,
    completedModules: 5,
    instructor: "د. أحمد السلوك",
    category: "مهارات شخصية",
  },
];

export const documents: Document[] = [
  {
    id: "d1",
    title: "دليل هوية العلامة التجارية",
    type: "pdf",
    category: "التسويق",
    size: "12.5 MB",
    updatedAt: "2026-02-15",
    downloads: 89,
  },
  {
    id: "d2",
    title: "نموذج طلب إجازة",
    type: "doc",
    category: "الموارد البشرية",
    size: "245 KB",
    updatedAt: "2026-01-20",
    downloads: 234,
  },
  {
    id: "d3",
    title: "قائمة أسعار المنتجات 2026",
    type: "xlsx",
    category: "المبيعات",
    size: "1.8 MB",
    updatedAt: "2026-02-01",
    downloads: 156,
  },
  {
    id: "d4",
    title: "عرض تقديمي - خطة التوسع",
    type: "pptx",
    category: "الإدارة",
    size: "8.3 MB",
    updatedAt: "2026-02-10",
    downloads: 67,
  },
  {
    id: "d5",
    title: "إجراءات السلامة في المختبر",
    type: "pdf",
    category: "السلامة",
    size: "3.2 MB",
    updatedAt: "2026-01-15",
    downloads: 98,
  },
  {
    id: "d6",
    title: "نموذج تقييم الأداء السنوي",
    type: "doc",
    category: "الموارد البشرية",
    size: "380 KB",
    updatedAt: "2026-02-05",
    downloads: 178,
  },
  {
    id: "d7",
    title: "كتالوج المنتجات - الإصدار الجديد",
    type: "pdf",
    category: "المبيعات",
    size: "25.6 MB",
    updatedAt: "2026-02-18",
    downloads: 312,
  },
  {
    id: "d8",
    title: "تقرير المبيعات الشهري - يناير 2026",
    type: "xlsx",
    category: "المبيعات",
    size: "2.1 MB",
    updatedAt: "2026-02-03",
    downloads: 45,
  },
];
