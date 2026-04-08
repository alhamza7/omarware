import { useState, useEffect } from "react";
import { Sidebar } from "./components/sidebar";
import { DashboardStats } from "./components/dashboard-stats";
import { CustomerCard } from "./components/customer-card";
import { CustomerForm } from "./components/customer-form";
import { CustomerKanban } from "./components/customer-kanban";
import type { KanbanCustomer, CustomerStage } from "./components/customer-kanban";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "./components/ui/card";
import { Button } from "./components/ui/button";
import {
  Plus,
  Search,
  Palette,
  Package,
  ArrowLeft,
  ArrowRight,
  ShoppingBag,
  TrendingUp,
  Sparkles,
  Bell,
  MessageSquare,
  Settings,
  Headset,
  MoreHorizontal,
  Eye,
  FileText,
  Activity as ActivityIcon,
  Crown,
  List,
  Columns3,
} from "lucide-react";
import { Input } from "./components/ui/input";
import { AnimatedBackground } from "./components/animated-background";
import { motion, AnimatePresence } from "motion/react";
import {
  SalesChart,
  CustomerSegmentationChart,
} from "./components/dashboard/dashboard-charts";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "./components/ui/avatar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./components/ui/dialog";
import { Badge } from "./components/ui/badge";
import userProfileImage from "figma:asset/ad013dd3df0212c6805c6fe8639a2b3dadaf7388.png";
import customerProfileImage from "figma:asset/12f3aceb0af91fcf37da5c198f4273653836494f.png";
import { CustomerDetailDialog } from "./components/customer-detail-dialog";
import { AnalyticsDashboard } from "./components/analytics/analytics-dashboard";
import { KnowledgeBase } from "./components/knowledge-base/knowledge-base";
import { CallCentre } from "./components/call-centre/call-centre";

import {
  RecentInteractions,
  TaskTracker,
  AlertsWidget,
  CustomerSummary,
  CommunicationWidget,
  FeedbackWidget,
} from "./components/dashboard/dashboard-lists";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [showCustomerForm, setShowCustomerForm] =
    useState(false);
  const [selectedCustomer, setSelectedCustomer] =
    useState<any>(null);
  const [colorTheme, setColorTheme] = useState<
    "dark-gold" | "light-turquoise"
  >("dark-gold");
  const [customerView, setCustomerView] = useState<"list" | "kanban">("list");

  // Apply theme class and direction to document body
  useEffect(() => {
    const body = document.body;
    // Force RTL direction for the entire app, including Portals
    document.documentElement.dir = "rtl";
    document.documentElement.lang = "ar";

    if (colorTheme === "light-turquoise") {
      body.classList.add("light-turquoise");
      body.classList.remove("dark");
    } else {
      body.classList.remove("light-turquoise");
      body.classList.add("dark");
    }
  }, [colorTheme]);

  const toggleTheme = () => {
    setColorTheme((prev) =>
      prev === "dark-gold" ? "light-turquoise" : "dark-gold",
    );
  };

  // Mock customer data
  const customers: KanbanCustomer[] = [
    {
      id: "C-001",
      name: "أحمد محمد العلي",
      email: "ahmed.ali@email.com",
      phone: "+966 50 123 4567",
      address: "الرياض، حي النخيل، شارع الملك فهد",
      totalPurchases: 15680,
      joinDate: "2024-01-15",
      vipStatus: true,
      favoriteFragrance: "عود ملكي",
      stage: "vip",
      lastActivity: "منذ يومين",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 50 123 4567", verified: true },
        { channel: "instagram", handle: "@ahmed_ali_vip", verified: true },
        { channel: "email", handle: "ahmed.ali@email.com", verified: true },
        { channel: "store", handle: "فرع الرياض - النخيل", verified: true },
      ],
    },
    {
      id: "C-002",
      name: "فاطمة عبدالله السالم",
      email: "fatima.salem@email.com",
      phone: "+966 55 987 6543",
      address: "جدة، حي الحمراء، شارع التحلية",
      totalPurchases: 8950,
      joinDate: "2024-02-20",
      vipStatus: false,
      favoriteFragrance: "روز باريس",
      stage: "active",
      lastActivity: "منذ 5 أيام",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 55 987 6543", verified: true },
        { channel: "instagram", handle: "@fatima_beauty", verified: true },
        { channel: "tiktok", handle: "@fatima.perfume", verified: false },
        { channel: "email", handle: "fatima.salem@email.com", verified: true },
      ],
    },
    {
      id: "C-003",
      name: "خالد سعد القحطاني",
      email: "khalid.q@email.com",
      phone: "+966 54 456 7890",
      address: "الدمام، حي الفيصلية، شارع الأمير محمد",
      totalPurchases: 22340,
      joinDate: "2023-11-10",
      vipStatus: true,
      favoriteFragrance: "مسك الليل",
      stage: "vip",
      lastActivity: "اليوم",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 54 456 7890", verified: true },
        { channel: "instagram", handle: "@khalid_q_perfumes", verified: true },
        { channel: "x", handle: "@khalid_saud", verified: true },
        { channel: "telegram", handle: "@khalid_q", verified: false },
        { channel: "store", handle: "فرع الدمام", verified: true },
      ],
    },
    {
      id: "C-004",
      name: "نورة محمد الشمري",
      email: "noura.sh@email.com",
      phone: "+966 56 111 2222",
      address: "الرياض، حي الملقا، شارع أنس بن مالك",
      totalPurchases: 3200,
      joinDate: "2025-06-01",
      vipStatus: false,
      favoriteFragrance: "ورد طائفي",
      stage: "interested",
      lastActivity: "منذ أسبوع",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 56 111 2222", verified: true },
        { channel: "instagram", handle: "@noura_sh", verified: false },
        { channel: "website", handle: "noura.sh@email.com", verified: true },
      ],
    },
    {
      id: "C-005",
      name: "عبدالرحمن صالح الدوسري",
      email: "abdulrahman.d@email.com",
      phone: "+966 58 333 4444",
      address: "جدة، حي الروضة، شارع فلسطين",
      totalPurchases: 750,
      joinDate: "2025-12-20",
      vipStatus: false,
      stage: "lead",
      lastActivity: "منذ 3 أيام",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 58 333 4444", verified: true },
        { channel: "snapchat", handle: "abdulrahman_d", verified: false },
      ],
    },
    {
      id: "C-006",
      name: "سارة علي الحربي",
      email: "sara.h@email.com",
      phone: "+966 59 555 6666",
      address: "الرياض، حي العليا، طريق الملك فهد",
      totalPurchases: 12400,
      joinDate: "2024-03-05",
      vipStatus: false,
      favoriteFragrance: "عنبر فاخر",
      stage: "active",
      lastActivity: "أمس",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 59 555 6666", verified: true },
        { channel: "instagram", handle: "@sara_harbi", verified: true },
        { channel: "tiktok", handle: "@sara.perfume", verified: true },
        { channel: "email", handle: "sara.h@email.com", verified: true },
        { channel: "store", handle: "فرع الرياض - العليا", verified: true },
      ],
    },
    {
      id: "C-007",
      name: "محمد عبدالله العتيبي",
      email: "m.otaibi@email.com",
      phone: "+966 50 777 8888",
      address: "مكة المكرمة، حي العزيزية",
      totalPurchases: 1500,
      joinDate: "2025-08-15",
      vipStatus: false,
      stage: "interested",
      lastActivity: "منذ أسبوعين",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 50 777 8888", verified: true },
        { channel: "email", handle: "m.otaibi@email.com", verified: true },
      ],
    },
    {
      id: "C-008",
      name: "ريم سعود الراشد",
      email: "reem.r@email.com",
      phone: "+966 55 999 0000",
      address: "الخبر، حي الراكة، شارع الأمير تركي",
      totalPurchases: 4800,
      joinDate: "2024-09-10",
      vipStatus: false,
      favoriteFragrance: "بخور العربية",
      stage: "dormant",
      lastActivity: "منذ 4 أشهر",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 55 999 0000", verified: true },
        { channel: "instagram", handle: "@reem_perfume", verified: false },
      ],
    },
    {
      id: "C-009",
      name: "تركي فيصل المطيري",
      email: "turki.m@email.com",
      phone: "+966 54 222 3333",
      address: "الرياض، حي الورود",
      totalPurchases: 320,
      joinDate: "2026-01-10",
      vipStatus: false,
      stage: "lead",
      lastActivity: "منذ يوم",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 54 222 3333", verified: true },
        { channel: "website", handle: "turki.m@email.com", verified: true },
      ],
    },
    {
      id: "C-010",
      name: "هند خالد الزهراني",
      email: "hind.z@email.com",
      phone: "+966 56 444 5555",
      address: "جدة، حي البوادي، شارع الأندلس",
      totalPurchases: 6700,
      joinDate: "2024-06-20",
      vipStatus: false,
      favoriteFragrance: "روز باريس",
      stage: "dormant",
      lastActivity: "منذ 6 أشهر",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 56 444 5555", verified: true },
        { channel: "snapchat", handle: "hind_z", verified: false },
        { channel: "store", handle: "فرع جدة", verified: true },
      ],
    },
    {
      id: "C-011",
      name: "ماجد عمر السبيعي",
      email: "majed.s@email.com",
      phone: "+966 58 666 7777",
      address: "الدمام، حي الشاطئ",
      totalPurchases: 950,
      joinDate: "2025-11-01",
      vipStatus: false,
      stage: "lead",
      lastActivity: "منذ 4 أيام",
      channelIdentities: [
        { channel: "instagram", handle: "@majed_oud", verified: false },
        { channel: "whatsapp", handle: "+966 58 666 7777", verified: true },
      ],
    },
    {
      id: "C-012",
      name: "لمى عبدالعزيز الغامدي",
      email: "lama.g@email.com",
      phone: "+966 50 888 9999",
      address: "الرياض، حي الربيع",
      totalPurchases: 18500,
      joinDate: "2023-08-01",
      vipStatus: true,
      favoriteFragrance: "عود ملكي",
      stage: "vip",
      lastActivity: "اليوم",
      channelIdentities: [
        { channel: "whatsapp", handle: "+966 50 888 9999", verified: true },
        { channel: "instagram", handle: "@lama_luxury", verified: true },
        { channel: "x", handle: "@lama_g", verified: true },
        { channel: "email", handle: "lama.g@email.com", verified: true },
        { channel: "store", handle: "الفرع الرئيسي", verified: true },
        { channel: "telegram", handle: "@lama_vip", verified: true },
      ],
    },
  ];

  const handleCustomerSubmit = (data: any) => {
    console.log("New customer data:", data);
    setShowCustomerForm(false);
  };

  return (
    <div className="min-h-screen flex bg-background" dir="rtl">
      {/* Animated Background */}
      <AnimatedBackground />

      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-xl border-b border-border">
          <div className="px-8 py-4">
            <div className="flex items-center justify-between gap-4">
              {/* Right Side: Title & Welcome */}
              <div>
                <h2 className="text-3xl font-bold text-gradient-gold drop-shadow-sm">
                  {activeTab === "dashboard" && "لوحة التحكم"}
                  {activeTab === "customers" && "إدارة العملاء"}
                  {activeTab === "products" && "المنتجات"}
                  {activeTab === "orders" && "الطلبات"}
                  {activeTab === "analytics" && "التحليلات"}
                  {activeTab === "call-centre" &&
                    "مركز الاتصال"}
                  {activeTab === "knowledge-base" && "قاعدة المعرفة"}
                  {activeTab === "settings" && "الإعدادات"}
                </h2>
                <p className="text-muted-foreground mt-1 text-sm">
                  مرحباً بك، أحمد العلي 👋
                </p>
              </div>

              {/* Left Side: Search, Icons, Profile */}
              <div className="flex items-center gap-4">
                {/* Search Bar */}
                <div className="relative hidden md:block">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="بحث سريع..."
                    className="w-64 pr-9 pl-4 bg-secondary/30 border-primary/10 focus:bg-background focus:border-primary/30 transition-all rounded-full h-10"
                  />
                </div>

                <div className="h-8 w-px bg-border/50 hidden md:block" />

                {/* Action Icons */}
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full relative"
                  >
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full"
                  >
                    <MessageSquare className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full"
                  >
                    <Settings className="w-5 h-5" />
                  </Button>
                </div>

                {/* Theme Toggle (Mini) */}
                <Button
                  onClick={toggleTheme}
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full"
                  title={
                    colorTheme === "dark-gold"
                      ? "الوضع النهاري"
                      : "الوضع الليلي"
                  }
                >
                  <Palette className="w-5 h-5" />
                </Button>

                <div className="h-8 w-px bg-border/50" />

                {/* Profile Section */}
                <div className="flex items-center gap-3 pl-2 cursor-pointer group">
                  <div className="text-right hidden lg:block transition-transform duration-300 group-hover:-translate-x-1">
                    <p className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                      أحمد العلي
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      مدير النظ��م
                    </p>
                  </div>

                  <div className="relative">
                    {/* Glow Effect */}
                    <div className="absolute inset-0 rounded-full bg-primary/20 blur-md scale-0 group-hover:scale-125 transition-transform duration-500" />

                    <Avatar className="h-11 w-11 border-2 border-primary/30 shadow-lg shadow-primary/10 transition-transform duration-300 group-hover:scale-105 group-hover:border-primary">
                      <AvatarImage
                        src={userProfileImage}
                        alt="User"
                        className="object-cover bg-secondary/50"
                      />
                      <AvatarFallback className="bg-primary/10 text-primary">
                        AA
                      </AvatarFallback>
                    </Avatar>

                    {/* Status Indicator */}
                    <span className="absolute bottom-0.5 right-0.5 w-3 h-3 bg-green-500 border-2 border-background rounded-full shadow-[0_0_8px_rgba(34,197,94,0.8)] animate-pulse" />
                  </div>
                </div>

                {activeTab === "customers" && (
                  <Button
                    onClick={() =>
                      setShowCustomerForm(!showCustomerForm)
                    }
                    size="default"
                    className="gap-2 mr-2 rounded-full"
                  >
                    <Plus className="w-4 h-4" />
                    <span className="hidden sm:inline">
                      إضافة عميل
                    </span>
                  </Button>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="p-8 space-y-8">
          {activeTab === "dashboard" && (
            <div className="space-y-6">
              {/* Stats Overview */}
              <DashboardStats />

              {/* Charts Section */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <SalesChart theme={colorTheme} />
                <CustomerSegmentationChart theme={colorTheme} />
              </div>

              {/* Activity & Alerts Section */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <RecentInteractions />
                <TaskTracker />
                <AlertsWidget />
              </div>

              {/* Engagement Section */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <CustomerSummary />
                <CommunicationWidget />
                <FeedbackWidget />
              </div>

              {/* Recent Activity & Products */}
              <div className="grid gap-6 lg:grid-cols-3">
                {/* Recent Orders Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                >
                  <Card className="h-full hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 border-t-4 border-t-primary/50 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    <CardHeader className="relative z-10 pb-2">
                      <div className="flex justify-between items-center mb-1">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <ShoppingBag className="w-5 h-5 text-primary" />
                          أحدث الطلبات
                        </CardTitle>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-primary"
                        >
                          <ArrowLeft className="w-4 h-4" />
                        </Button>
                      </div>
                      <CardDescription>
                        آخر 5 طلبات تم استلامها
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="relative z-10">
                      <div className="space-y-3">
                        {[1, 2, 3, 4, 5].map((item, i) => (
                          <motion.div
                            key={item}
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{
                              delay: 0.2 + i * 0.1,
                            }}
                            className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border/50 hover:bg-secondary/60 hover:border-primary/30 transition-all duration-200 cursor-pointer group/item"
                          >
                            <div>
                              <p className="font-semibold text-sm group-hover/item:text-primary transition-colors">
                                طلب #{2000 + item}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                عميل {item}
                              </p>
                            </div>
                            <div>
                              <p className="font-bold text-primary text-sm">
                                {(
                                  Math.random() * 1000 +
                                  200
                                ).toFixed(0)}{" "}
                                ريال
                              </p>
                              <p className="text-xs text-muted-foreground">
                                منذ {item} ساعات
                              </p>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                      <Button
                        variant="link"
                        className="w-full mt-4 text-xs text-muted-foreground hover:text-primary"
                      >
                        عرض جميع الطلبات
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>

                {/* Best Sellers Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                >
                  <Card className="h-full hover:shadow-2xl hover:shadow-yellow-500/10 transition-all duration-300 border-t-4 border-t-yellow-500/50 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-b from-yellow-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    <CardHeader className="relative z-10 pb-2">
                      <div className="flex justify-between items-center mb-1">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <TrendingUp className="w-5 h-5 text-yellow-500" />
                          المنتجات الأكثر مبيعاً
                        </CardTitle>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-yellow-500"
                        >
                          <ArrowLeft className="w-4 h-4" />
                        </Button>
                      </div>
                      <CardDescription>
                        أفضل 5 منتجات هذا الشهر
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="relative z-10">
                      <div className="space-y-3">
                        {[
                          "عود ملكي",
                          "��وز باريس",
                          "مسك الليل",
                          "عنبر فاخر",
                          "ورد طائفي",
                        ].map((product, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{
                              delay: 0.3 + index * 0.1,
                            }}
                            className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border/50 hover:bg-secondary/60 hover:border-yellow-500/30 transition-all duration-200 cursor-pointer group/item"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center shrink-0">
                                <span className="text-xs font-bold text-yellow-500">
                                  #{index + 1}
                                </span>
                              </div>
                              <p className="font-semibold text-sm group-hover/item:text-yellow-600 dark:group-hover/item:text-yellow-400 transition-colors">
                                {product}
                              </p>
                            </div>
                            <div className="flex flex-col items-end">
                              <p className="text-yellow-600 dark:text-yellow-400 font-bold text-sm">
                                {150 - index * 20}
                              </p>
                              <span className="text-[10px] text-muted-foreground">
                                وحدة مباعة
                              </span>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                      <Button
                        variant="link"
                        className="w-full mt-4 text-xs text-muted-foreground hover:text-yellow-500"
                      >
                        تحليل المبيعات الكامل
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>

                {/* New Products Card */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.3 }}
                >
                  <Card className="h-full hover:shadow-2xl hover:shadow-cyan-500/10 transition-all duration-300 border-t-4 border-t-cyan-500/50 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    <CardHeader className="relative z-10 pb-2">
                      <div className="flex justify-between items-center mb-1">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <Sparkles className="w-5 h-5 text-cyan-500" />
                          المنتجات الحديثة
                        </CardTitle>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-cyan-500"
                        >
                          <ArrowLeft className="w-4 h-4" />
                        </Button>
                      </div>
                      <CardDescription>
                        أحدث الإضافات للمتجر
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="relative z-10">
                      <div className="space-y-3">
                        {[
                          "عطر الشتاء",
                          "مخلط ملكي",
                          "مسك الرمان",
                          "دهن عود قديم",
                          "بخور العربية",
                        ].map((product, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: 10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{
                              delay: 0.4 + index * 0.1,
                            }}
                            className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border/50 hover:bg-secondary/60 hover:border-cyan-500/30 transition-all duration-200 cursor-pointer group/item"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center group-hover/item:bg-cyan-500/20 transition-colors shrink-0">
                                <Package className="w-4 h-4 text-cyan-500" />
                              </div>
                              <div>
                                <p className="font-semibold text-sm group-hover/item:text-cyan-600 dark:group-hover/item:text-cyan-400 transition-colors">
                                  {product}
                                </p>
                              </div>
                            </div>
                            <div className="flex flex-col items-end">
                              <p className="text-cyan-600 dark:text-cyan-400 font-bold text-sm">
                                {(
                                  Math.random() * 500 +
                                  200
                                ).toFixed(0)}{" "}
                                ريال
                              </p>
                              <span className="text-[10px] bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 px-1.5 py-0.5 rounded-full mt-0.5">
                                جديد
                              </span>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                      <Button
                        variant="link"
                        className="w-full mt-4 text-xs text-muted-foreground hover:text-cyan-500"
                      >
                        إدارة المخزون
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              </div>
            </div>
          )}

          {activeTab === "customers" && (
            <>
              {/* Toolbar: Search + View Toggle */}
              <div className="flex gap-4 items-center justify-between flex-wrap">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    placeholder="البحث عن عميل..."
                    className="pr-10"
                  />
                </div>

                {/* View Toggle */}
                <div className="flex items-center gap-1 bg-secondary/30 border border-border/40 rounded-xl p-1">
                  <Button
                    variant={customerView === "list" ? "default" : "ghost"}
                    size="sm"
                    className={`h-8 gap-1.5 rounded-lg text-xs ${
                      customerView === "list"
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => setCustomerView("list")}
                  >
                    <List className="w-3.5 h-3.5" />
                    قائمة
                  </Button>
                  <Button
                    variant={customerView === "kanban" ? "default" : "ghost"}
                    size="sm"
                    className={`h-8 gap-1.5 rounded-lg text-xs ${
                      customerView === "kanban"
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => setCustomerView("kanban")}
                  >
                    <Columns3 className="w-3.5 h-3.5" />
                    كانبان
                  </Button>
                </div>
              </div>

              {/* Customer Form (Conditional) */}
              {showCustomerForm && (
                <div className="max-w-2xl">
                  <CustomerForm
                    onSubmit={handleCustomerSubmit}
                  />
                </div>
              )}

              {/* ═══ List View ═══ */}
              {customerView === "list" && (
                <div className="rounded-xl border border-border/40 overflow-hidden bg-card/30 backdrop-blur-md shadow-sm">
                  <Table>
                    <TableHeader className="bg-muted/30">
                      <TableRow className="hover:bg-transparent border-border/40">
                        <TableHead className="text-right w-[80px]">
                          المعرف
                        </TableHead>
                        <TableHead className="text-right">
                          العميل
                        </TableHead>
                        <TableHead className="text-right hidden md:table-cell">
                          البريد الإلكتروني
                        </TableHead>
                        <TableHead className="text-right hidden md:table-cell">
                          رقم الهاتف
                        </TableHead>
                        <TableHead className="text-right hidden lg:table-cell">
                          التصنيف
                        </TableHead>
                        <TableHead className="text-right hidden lg:table-cell">
                          إجمالي الشراء
                        </TableHead>
                        <TableHead className="text-center w-[50px]"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {customers.map((customer) => (
                        <TableRow
                          key={customer.id}
                          className="cursor-pointer hover:bg-primary/5 border-border/40 transition-colors group"
                          onClick={() =>
                            setSelectedCustomer(customer)
                          }
                        >
                          <TableCell className="font-mono text-xs text-muted-foreground">
                            {customer.id}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar className="h-8 w-8 border border-border/50">
                                <AvatarFallback className="bg-primary/10 text-primary text-xs">
                                  {customer.name
                                    .split(" ")
                                    .map((n) => n[0])
                                    .join("")
                                    .slice(0, 2)}
                                </AvatarFallback>
                              </Avatar>
                              <div className="flex flex-col">
                                <span className="font-medium text-sm text-foreground group-hover:text-primary transition-colors">
                                  {customer.name}
                                </span>
                                <span className="text-[10px] text-muted-foreground md:hidden">
                                  {customer.vipStatus
                                    ? "VIP"
                                    : "عادي"}
                                </span>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                            {customer.email}
                          </TableCell>
                          <TableCell
                            className="hidden md:table-cell text-sm text-muted-foreground"
                            dir="ltr"
                          >
                            {customer.phone}
                          </TableCell>
                          <TableCell className="hidden lg:table-cell">
                            {customer.vipStatus ? (
                              <Badge
                                variant="default"
                                className="bg-primary/10 text-primary hover:bg-primary/20 border-primary/20"
                              >
                                VIP
                              </Badge>
                            ) : (
                              <Badge
                                variant="outline"
                                className="text-muted-foreground"
                              >
                                عادي
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="hidden lg:table-cell font-mono text-sm">
                            {customer.totalPurchases.toLocaleString()}{" "}
                            ر.س
                          </TableCell>
                          <TableCell className="text-center">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-muted-foreground hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* ═══ Kanban View ═══ */}
              {customerView === "kanban" && (
                <CustomerKanban
                  customers={customers}
                  onCustomerClick={(customer) => setSelectedCustomer(customer)}
                />
              )}

              {/* 360 Degree Customer View Dialog */}
              <CustomerDetailDialog
                customer={selectedCustomer}
                open={!!selectedCustomer}
                onClose={() => setSelectedCustomer(null)}
                profileImage={customerProfileImage}
              />
            </>
          )}

          {activeTab === "analytics" && (
            <AnalyticsDashboard />
          )}

          {activeTab === "knowledge-base" && (
            <KnowledgeBase />
          )}

          {activeTab === "call-centre" && (
            <CallCentre />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;