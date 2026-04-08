import { useState, useEffect, useRef, useCallback } from "react";
// ── Shared UI ──────────────────────────────────────────────────────────────
import { Sidebar } from "./components/sidebar";
import { AnimatedBackground } from "./components/animated-background";
import { ViewToggle } from "./components/view-toggle";
import { getHourlyQuote } from "./components/inspirational-quotes";
import { Input } from "./components/ui/input";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { ScrollArea } from "./components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "./components/ui/avatar";
import { motion, AnimatePresence } from "motion/react";
import {
  Bell, MessageSquare, Settings, Building2, ChevronDown,
  X, CheckCheck, AlertTriangle, ShoppingCart, UserPlus, Star,
  Clock, Trash2, Sun, Moon, Search, Plus, Eye,
  ShoppingBag, TrendingUp, Sparkles, Package, ArrowLeft, Tickets,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./components/ui/table";

// ── Static presentational components (no data-fetch) ──────────────────────
import { LoginPage } from "./components/login-page";
import { SalesChart, CustomerSegmentationChart } from "./components/dashboard/dashboard-charts";
import { RecentInteractions, TaskTracker, AlertsWidget, CustomerSummary, CommunicationWidget, FeedbackWidget } from "./components/dashboard/dashboard-lists";
import { DashboardStats } from "./components/dashboard-stats";
import { AdminDashboard } from "./components/admin-dashboard/admin-dashboard";
import { PriceList } from "./components/price-list/price-list";
import { ProductKanban } from "./components/product-kanban";
import { Promotions } from "./components/promotions/promotions";
import { Orders } from "./components/orders/orders";
import { SalesPipeline } from "./components/sales-pipeline/sales-pipeline";
import { EventLog } from "./components/event-log/event-log";
import { Forecasting, ForecastingWidget } from "./components/forecasting/forecasting";
import { SettingsPage } from "./components/settings/settings";

// ── Feature containers (API-connected) ────────────────────────────────────
import { CustomerListContainer } from "../features/customers/containers/CustomerListContainer";
import { CallCentreContainer } from "../features/call-centre/containers/CallCentreContainer";
import { TicketsContainer } from "../features/tickets/containers/TicketsContainer";
import { OmniChannelContainer } from "../features/omnichannel/containers/OmniChannelContainer";
import { AnalyticsContainer } from "../features/analytics/containers/AnalyticsContainer";
import { SupplyChainContainer } from "../features/supply-chain/containers/SupplyChainContainer";
import { KnowledgeBaseContainer } from "../features/knowledge-base/containers/KnowledgeBaseContainer";
import { WorkforceContainer } from "../features/workforce/containers/WorkforceContainer";

// ── Feature hooks ──────────────────────────────────────────────────────────
import { useAuth } from "../features/auth/hooks/useAuth";
import { useDashboard } from "../features/dashboard/hooks/useDashboard";

// ── Misc ───────────────────────────────────────────────────────────────────
import { branches } from "./components/orders/ord-data";

function App() {
  // ── Auth ────────────────────────────────────────────────────────────────
  const { user, isLoggedIn, isLoading: authLoading, error: authError, login, logout, restoreSession } = useAuth();

  // ── UI State ────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState("dashboard");
  const [showCustomerForm, setShowCustomerForm] = useState(false);
  const [colorTheme, setColorTheme] = useState<"dark-gold" | "light-turquoise">("dark-gold");
  const [customerView, setCustomerView] = useState<"list" | "kanban">("kanban");
  const [productView, setProductView] = useState<"list" | "kanban">("kanban");
  const [selectedBranch, setSelectedBranch] = useState("all");
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  // ── Dashboard data (notifications from API) ────────────────────────────
  const selectedBranchId = selectedBranch === "all" ? undefined : Number(selectedBranch);
  const {
    notifications: apiNotifications,
    stats:         dashboardStats,
    recentOrders:  apiRecentOrders,
    vipCustomers:  apiVipCustomers,
    unreadCount,
    markRead,
    markAllRead,
    removeNotification,
  } = useDashboard(selectedBranchId);

  /** Map API notification to display-compatible shape */
  const notifications = apiNotifications.map((n) => ({
    id:   String(n.id),
    type: n.type,
    title: n.title,
    desc:  n.body,
    time:  n.created_at,
    read:  n.is_read,
  }));

  const markAsRead = useCallback((id: string) => markRead(Number(id)), [markRead]);
  const handleRemove = useCallback((id: string) => removeNotification(Number(id)), [removeNotification]);

  /** Helper: notification icon per type */
  const getNotifIcon = (type: string) => {
    switch (type) {
      case "order":    return <ShoppingCart className="w-4 h-4" />;
      case "alert":    return <AlertTriangle className="w-4 h-4" />;
      case "customer": return <UserPlus className="w-4 h-4" />;
      case "review":   return <Star className="w-4 h-4" />;
      default:         return <Bell className="w-4 h-4" />;
    }
  };

  /** Helper: notification badge color per type */
  const getNotifColor = (type: string) => {
    switch (type) {
      case "order":    return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "alert":    return "bg-red-500/10 text-red-400 border-red-500/20";
      case "customer": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "review":   return "bg-primary/10 text-primary border-primary/20";
      default:         return "bg-muted/30 text-muted-foreground border-border/30";
    }
  };

  /** Close notification panel when clicking outside */
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
    };
    if (showNotifications) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [showNotifications]);

  /** Apply theme + RTL direction to document */
  useEffect(() => {
    document.documentElement.dir  = "rtl";
    document.documentElement.lang = "ar";
    if (colorTheme === "light-turquoise") {
      document.body.classList.add("light-turquoise");
      document.body.classList.remove("dark");
    } else {
      document.body.classList.remove("light-turquoise");
      document.body.classList.add("dark");
    }
  }, [colorTheme]);

  /** Restore session from localStorage on first mount */
  useEffect(() => {
    restoreSession();
  }, []);

  const toggleTheme = () =>
    setColorTheme((prev) => prev === "dark-gold" ? "light-turquoise" : "dark-gold");

  const handleLogin = useCallback(
    async (username: string, password: string) => login(username, password),
    [login],
  );

  // ── Guard: show login if not authenticated ─────────────────────────────
  if (!isLoggedIn) {
    return (
      <LoginPage
        onLogin={handleLogin as never}
        colorTheme={colorTheme}
        onToggleTheme={toggleTheme}
        isLoading={authLoading}
        error={authError}
      />
    );
  }

  return (
    <div className="min-h-screen flex bg-background" dir="rtl">
      {/* Animated Background */}
      <AnimatedBackground />

      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onLogout={logout}
      />

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-xl border-b border-border">
          <div className="px-8 py-4">
            <div className="flex items-center justify-between gap-4" dir="rtl">
              {/* Right Side (start): Profile, Icons, Branch, Search */}
              <div className="flex items-center gap-3">
                {/* Profile Section */}
                <div className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative">
                    {/* Glow Effect */}
                    <div className="absolute inset-0 rounded-full bg-primary/20 blur-md scale-0 group-hover:scale-125 transition-transform duration-500" />
                    <Avatar className="h-11 w-11 border-2 border-primary/30 shadow-lg shadow-primary/10 transition-transform duration-300 group-hover:scale-105 group-hover:border-primary">
                      <AvatarFallback className="bg-primary/10 text-primary">
                        {user?.name?.slice(0, 2) ?? "NA"}
                      </AvatarFallback>
                    </Avatar>
                    {/* Status Indicator */}
                    <span className="absolute bottom-0.5 start-0.5 w-3 h-3 bg-green-500 border-2 border-background rounded-full shadow-[0_0_8px_rgba(34,197,94,0.8)] animate-pulse" />
                  </div>
                  <div className="text-start hidden lg:block transition-transform duration-300">
                    <p className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                      أحمد العلي
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      مدير النظم
                    </p>
                  </div>
                </div>

                <div className="h-8 w-px bg-border/50" />

                {/* Action Icons */}
                <div className="flex items-center gap-1">
                  <div className="relative" ref={notifRef}>
                    <Button
                      onClick={() => setShowNotifications(!showNotifications)}
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full relative"
                    >
                      <Bell className="w-5 h-5" />
                      {unreadCount > 0 && (
                        <span className="absolute -top-0.5 -start-0.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] tabular-nums animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.6)]">
                          {unreadCount}
                        </span>
                      )}
                    </Button>

                    {/* Notifications Dropdown */}
                    <AnimatePresence>
                      {showNotifications && (
                        <motion.div
                          initial={{ opacity: 0, y: -10, scale: 0.95 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: -10, scale: 0.95 }}
                          transition={{ duration: 0.2, ease: "easeOut" }}
                          className="absolute top-full start-0 mt-2 w-[380px] bg-card border border-border/50 rounded-2xl z-50 shadow-2xl shadow-black/20 overflow-hidden"
                          dir="rtl"
                        >
                          {/* Header */}
                          <div className="flex items-center justify-between px-5 py-3.5 border-b border-border/30 bg-muted/10">
                            <div className="flex items-center gap-2">
                              <Bell className="w-4 h-4 text-primary" />
                              <h3 className="text-sm text-foreground">الإشعارات</h3>
                              {unreadCount > 0 && (
                                <Badge className="bg-red-500/10 text-red-400 border-red-500/20 text-[10px] h-5 px-1.5">
                                  {unreadCount} جديد
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-1">
                              {unreadCount > 0 && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 text-[10px] text-muted-foreground hover:text-primary gap-1"
                                  onClick={markAllRead}
                                >
                                  <CheckCheck className="w-3.5 h-3.5" />
                                  قراءة الكل
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-7 w-7 text-muted-foreground hover:text-foreground"
                                onClick={() => setShowNotifications(false)}
                              >
                                <X className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          </div>

                          {/* Notification List */}
                          <ScrollArea dir="rtl" className="max-h-[420px]">
                            <div className="p-2 space-y-1">
                              {notifications.length === 0 ? (
                                <div className="text-center py-10">
                                  <Bell className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                                  <p className="text-xs text-muted-foreground">لا توجد إشعارات</p>
                                </div>
                              ) : (
                                notifications.map((notif) => (
                                  <div
                                    key={notif.id}
                                    className={`flex items-start gap-3 p-3 rounded-xl transition-all duration-200 cursor-pointer group/notif ${
                                      notif.read
                                        ? "hover:bg-muted/10"
                                        : "bg-primary/5 border border-primary/10 hover:bg-primary/10"
                                    }`}
                                    onClick={() => markAsRead(notif.id)}
                                  >
                                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${getNotifColor(notif.type)}`}>
                                      {getNotifIcon(notif.type)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-center gap-2">
                                        <p className={`text-xs truncate ${notif.read ? "text-muted-foreground" : "text-foreground"}`}>
                                          {notif.title}
                                        </p>
                                        {!notif.read && (
                                          <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
                                        )}
                                      </div>
                                      <p className="text-[10px] text-muted-foreground mt-0.5 truncate">{notif.desc}</p>
                                      <p className="text-[9px] text-muted-foreground/60 mt-1 flex items-center gap-1">
                                        <Clock className="w-2.5 h-2.5" />
                                        {notif.time}
                                      </p>
                                    </div>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-6 w-6 text-muted-foreground/40 hover:text-red-400 opacity-0 group-hover/notif:opacity-100 transition-opacity shrink-0 mt-0.5"
                                      onClick={(e) => { e.stopPropagation(); removeNotification(notif.id); }}
                                    >
                                      <Trash2 className="w-3 h-3" />
                                    </Button>
                                  </div>
                                ))
                              )}
                            </div>
                          </ScrollArea>

                          {/* Footer */}
                          {notifications.length > 0 && (
                            <div className="px-5 py-2.5 border-t border-border/30 bg-muted/5">
                              <Button
                                variant="ghost"
                                className="w-full h-8 text-xs text-muted-foreground hover:text-primary"
                                onClick={() => { setShowNotifications(false); setActiveTab("event-log"); }}
                              >
                                عرض جميع الإشعارات
                              </Button>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full"
                    title="الرسائل"
                    onClick={() => setActiveTab("omni-channel")}
                  >
                    <MessageSquare className="w-5 h-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full"
                    title="الإعدادات"
                    onClick={() => setActiveTab("settings")}
                  >
                    <Settings className="w-5 h-5" />
                  </Button>
                  {/* Theme Toggle - Premium 3D Switch */}
                  <div dir="ltr" className="relative flex items-center h-9">
                    <motion.button
                      onClick={toggleTheme}
                      whileHover={{ scale: 1.08 }}
                      whileTap={{ scale: 0.92 }}
                      className="relative w-14 h-7 rounded-full cursor-pointer outline-none"
                      title={colorTheme === "dark-gold" ? "الوضع النهاري" : "الوضع الليلي"}
                      style={{
                        background: colorTheme === "dark-gold" ? "#1a1a2e" : "#e3edf2",
                        boxShadow: colorTheme === "dark-gold"
                          ? "4px 4px 10px rgba(0,0,0,0.65), -4px -4px 10px rgba(50,50,80,0.35)"
                          : "4px 4px 10px rgba(165,180,195,0.45), -4px -4px 10px rgba(255,255,255,0.85)",
                      }}
                    >
                      <span className="absolute inset-0 flex items-center justify-between px-1.5 pointer-events-none">
                        <Moon
                          className="w-3 h-3 transition-all"
                          style={{ color: colorTheme === "dark-gold" ? "#D4AF37" : "#A0AEC0" }}
                        />
                        <Sun
                          className="w-3 h-3 transition-all"
                          style={{ color: colorTheme === "light-turquoise" ? "#06B6D4" : "#5A5A78" }}
                        />
                      </span>
                      <motion.span
                        layout
                        transition={{ type: "spring", stiffness: 500, damping: 35 }}
                        className="absolute top-[3px] w-[22px] h-[22px] rounded-full flex items-center justify-center"
                        style={{
                          left: colorTheme === "dark-gold" ? "3px" : "calc(100% - 25px)",
                          background: colorTheme === "dark-gold" ? "#1a1a2e" : "#e3edf2",
                          boxShadow: colorTheme === "dark-gold"
                            ? "4px 4px 10px rgba(0,0,0,0.65), -4px -4px 10px rgba(50,50,80,0.35)"
                            : "4px 4px 10px rgba(165,180,195,0.45), -4px -4px 10px rgba(255,255,255,0.85)",
                        }}
                      >
                        {colorTheme === "dark-gold" ? (
                          <Moon className="w-2.5 h-2.5" style={{ color: "#D4AF37" }} />
                        ) : (
                          <Sun className="w-2.5 h-2.5" style={{ color: "#06B6D4" }} />
                        )}
                      </motion.span>
                    </motion.button>
                  </div>
                </div>

                <div className="h-8 w-px bg-border/50 hidden md:block" />

                {/* Branch Selector */}
                <div className="hidden md:flex items-center gap-2 bg-secondary/30 border border-border/40 rounded-full px-3 h-10">
                  <Building2 className="w-4 h-4 text-primary shrink-0" />
                  <select
                    value={selectedBranch}
                    onChange={(e) => setSelectedBranch(e.target.value)}
                    className="bg-transparent text-sm text-foreground border-none outline-none cursor-pointer appearance-none pe-4"
                  >
                    <option value="all">جميع الفروع</option>
                    {branches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-muted-foreground shrink-0 -me-1" />
                </div>

                <div className="h-8 w-px bg-border/50 hidden md:block" />

                {/* Search Bar */}
                <div className="relative hidden md:block">
                  <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="بحث سريع..."
                    className="w-56 ps-9 pe-4 bg-secondary/30 border-primary/10 focus:bg-background focus:border-primary/30 transition-all rounded-full h-10"
                  />
                </div>

                {activeTab === "customers" && (
                  <Button
                    onClick={() =>
                      setShowCustomerForm(!showCustomerForm)
                    }
                    size="default"
                    className="gap-2 rounded-full"
                  >
                    <Plus className="w-4 h-4" />
                    <span className="hidden sm:inline">
                      إضافة عميل
                    </span>
                  </Button>
                )}
              </div>

              {/* Left Side (end): Title & Welcome */}
              <div className="text-start">
                <h2 className="text-3xl font-bold text-gradient-gold drop-shadow-sm">
                  {activeTab === "dashboard" && "لوحة التحكم"}
                  {activeTab === "customers" && "إدارة العملاء"}
                  {activeTab === "products" && "المنتجات"}
                  {activeTab === "orders" && "الطلبات"}
                  {activeTab === "supply-chain" && "سلسلة التوريد"}
                  {activeTab === "analytics" && "التحليلات"}
                  {activeTab === "call-centre" && "مركز الاتصال"}
                  {activeTab === "knowledge-base" && "قاعدة المعرفة"}
                  {activeTab === "admin-dashboard" && "لوحة المشرف"}
                  {activeTab === "settings" && "الإعدادات"}
                  {activeTab === "omni-channel" && "القنوت الموحدة"}
                  {activeTab === "tickets" && "التذاكر والمتابعات"}
                  {activeTab === "agents" && "الموظفون"}
                  {activeTab === "promotions" && "مركز العروض والحملات"}
                  {activeTab === "sales-pipeline" && "خط أنابيب المبيعات"}
                  {activeTab === "forecasting" && "التنبؤات وإعادة الطلب"}
                  {activeTab === "event-log" && "سجل الأحداث"}
                </h2>
                <p className="text-muted-foreground mt-1 text-sm">
                  مرحباً بك، {user?.name ?? ""} — <span className="italic opacity-80">{getHourlyQuote()}</span>
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="p-8 space-y-8">
          {activeTab === "dashboard" && (
            <div className="space-y-6">
              {/* Stats Overview */}
              <DashboardStats stats={dashboardStats} />

              {/* Charts Section */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <SalesChart theme={colorTheme} />
                <CustomerSegmentationChart theme={colorTheme} />
              </div>

              {/* Activity & Alerts Section */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <RecentInteractions />
                <TaskTracker overdueCt={dashboardStats?.tasks?.overdue} />
                <AlertsWidget stats={dashboardStats} />
              </div>

              {/* Engagement Section */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <CustomerSummary
                  vipCustomers={apiVipCustomers.length > 0 ? apiVipCustomers : undefined}
                  totalVip={dashboardStats?.customers?.vip}
                />
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
                        {apiRecentOrders.length > 0
                          ? apiRecentOrders.slice(0, 5).map((order, i) => (
                              <motion.div
                                key={order.id}
                                initial={{ opacity: 0, x: 10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.2 + i * 0.1 }}
                                className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 border border-border/50 hover:bg-secondary/60 hover:border-primary/30 transition-all duration-200 cursor-pointer group/item"
                              >
                                <div>
                                  <p className="font-semibold text-sm group-hover/item:text-primary transition-colors">
                                    {order.name ?? `طلب #${order.id}`}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    {order.partner_name ?? "—"}
                                  </p>
                                </div>
                                <div className="text-end">
                                  <p className="font-bold text-primary text-sm">
                                    {order.total ? `${order.total.toLocaleString("ar-SA")} ريال` : "—"}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    {order.status ?? "—"}
                                  </p>
                                </div>
                              </motion.div>
                            ))
                          : /* Empty state */ (
                              <p className="text-sm text-muted-foreground text-center py-4">
                                لا توجد طلبات حديثة
                              </p>
                            )}
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
                          "وز باريس",
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

              {/* Forecasting Widget */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                <Card className="hover:shadow-2xl hover:shadow-red-500/10 transition-all duration-300 border-t-4 border-t-red-500/50 relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-b from-red-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <CardHeader className="relative z-10 pb-2">
                    <div className="flex justify-between items-center mb-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-red-500" />
                        التنبؤات وإعادة الطلب
                      </CardTitle>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-red-500"
                        onClick={() => setActiveTab("forecasting")}
                      >
                        <ArrowLeft className="w-4 h-4" />
                      </Button>
                    </div>
                    <CardDescription>
                      المنتجات التي تحتاج إعادة طلب
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="relative z-10">
                    <ForecastingWidget onNavigate={() => setActiveTab("forecasting")} />
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          )}

          {activeTab === "customers" && (
            <>
              {/* Toolbar: View Toggle */}
              <div className="flex gap-4 items-center justify-end flex-wrap">
                <ViewToggle
                  view={customerView}
                  onViewChange={setCustomerView}
                  isDark={colorTheme === "dark-gold"}
                  iconOnly
                />
              </div>
              {/* API-connected customer container */}
              <CustomerListContainer
                view={customerView}
                showForm={showCustomerForm}
                onCloseForm={() => setShowCustomerForm(false)}
              />
            </>
          )}

          {activeTab === "analytics" && (
            <AnalyticsContainer />
          )}

          {activeTab === "knowledge-base" && (
            <KnowledgeBaseContainer />
          )}

          {activeTab === "call-centre" && (
            <CallCentreContainer branchId={selectedBranchId} />
          )}

          {activeTab === "supply-chain" && (
            <SupplyChainContainer />
          )}

          {activeTab === "admin-dashboard" && (
            <AdminDashboard />
          )}

          {activeTab === "products" && (
            <>
              {/* View Toggle */}
              <div className="mb-4 flex justify-end">
                <ViewToggle
                  view={productView}
                  onViewChange={setProductView}
                  listLabel="قائمة الأسعار"
                  isDark={colorTheme === "dark-gold"}
                  iconOnly
                />
              </div>

              {productView === "list" && <PriceList />}
              {productView === "kanban" && <ProductKanban />}
            </>
          )}

          {activeTab === "omni-channel" && (
            <OmniChannel />
          )}

          {activeTab === "tickets" && (
            <Tickets />
          )}

          {activeTab === "agents" && (
            <Agents />
          )}

          {activeTab === "promotions" && (
            <Promotions />
          )}

          {activeTab === "orders" && (
            <Orders />
          )}

          {activeTab === "sales-pipeline" && (
            <SalesPipeline />
          )}

          {activeTab === "forecasting" && (
            <Forecasting />
          )}

          {activeTab === "event-log" && (
            <EventLog />
          )}

          {activeTab === "settings" && (
            <SettingsPage isDark={colorTheme === "dark-gold"} />
          )}
        </div>
      </main>

      {/* Notifications panel is inline with the Bell button above */}
    </div>
  );
}

export default App;