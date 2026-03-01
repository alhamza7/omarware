import { useState, useMemo } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring } from "motion/react";
import {
  Package, Search, Filter, Truck, MapPin, Clock, Hash,
  User, Building2, Phone, FileText, MessageCircle, Box,
  ChevronLeft, X, Check, AlertTriangle, ExternalLink,
  ArrowLeftRight, Eye, Plus, Globe2,
  Trash2, CreditCard, Receipt,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "../ui/dialog";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import sampleBoxClosed from "../../../assets/f469e4e083a938d7ce9cab066852e9e1aa7db3f8.png";
import sampleBoxOpen from "../../../assets/3e950160ac22530d4b45dc36d7150d9bd99dd4d4.png";
import {
  mockOrders, branches, deliveryCompanies, sampleBoxes, sampleBoxDeliveries,
  orderStatusLabels, orderStatusColors, orderStatusStep,
  type Order, type OrderStatus, type Branch,
} from "./ord-data";
import { InvoiceCreationDialog } from "../invoice-creation-dialog";

// ── Helpers ─────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins} د`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} س`;
  return `${Math.floor(hrs / 24)} ي`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ar-SA", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

// ── Steps for tracking ──────────────────────────────────

const trackingSteps = [
  { key: "confirmed", label: "مؤكد" },
  { key: "preparing", label: "تجهيز" },
  { key: "shipped", label: "شُحن" },
  { key: "in_transit", label: "نقل" },
  { key: "out_for_delivery", label: "في الطريق" },
  { key: "delivered", label: "تم التوصيل" },
];

// ── Main Component ──────────────────────────────────────

export function Orders() {
  const [activeTab, setActiveTab] = useState<"orders" | "delivery" | "branches" | "samples">("orders");
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "all">("all");
  const [branchFilter, setBranchFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showNewOrderDialog, setShowNewOrderDialog] = useState(false);
  const [showInvoiceCreate, setShowInvoiceCreate] = useState(false);

  const filteredOrders = useMemo(() => {
    let ords = [...mockOrders];
    if (statusFilter !== "all") ords = ords.filter((o) => o.status === statusFilter);
    if (branchFilter !== "all") ords = ords.filter((o) => o.branchId === branchFilter);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      ords = ords.filter(
        (o) =>
          o.orderNumber.toLowerCase().includes(q) ||
          o.customerName.includes(searchQuery) ||
          (o.trackingNumber && o.trackingNumber.toLowerCase().includes(q)),
      );
    }
    return ords.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [statusFilter, branchFilter, searchQuery]);

  const stats = useMemo(() => ({
    total: mockOrders.length,
    pending: mockOrders.filter((o) => o.status === "pending").length,
    inProgress: mockOrders.filter((o) => ["confirmed", "preparing", "shipped", "in_transit", "out_for_delivery"].includes(o.status)).length,
    delivered: mockOrders.filter((o) => o.status === "delivered").length,
    totalRevenue: mockOrders.filter((o) => o.status !== "cancelled").reduce((sum, o) => sum + o.total, 0),
  }), []);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">

        {/* ── Stats ── */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3" dir="rtl">
          {[
            { label: "إجمالي الطلبات", value: stats.total, color: "text-foreground" },
            { label: "في الانتظار", value: stats.pending, color: "text-blue-400" },
            { label: "قيد المعالجة", value: stats.inProgress, color: "text-primary" },
            { label: "تم التوصيل", value: stats.delivered, color: "text-emerald-400" },
            { label: "الإيرادات", value: `$${stats.totalRevenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: "text-primary" },
          ].map((s) => (
            <div key={s.label} className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
              <p className={`text-2xl ${s.color}`}>{s.value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* ── Tabs ── */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <div className="flex items-center justify-between">
            <TabsList className="bg-muted/20">
              <TabsTrigger value="orders" className="text-xs gap-1.5">
                <Package className="w-3.5 h-3.5" />
                الطلبات
              </TabsTrigger>
              <TabsTrigger value="delivery" className="text-xs gap-1.5">
                <Truck className="w-3.5 h-3.5" />
                التتبع
              </TabsTrigger>
              <TabsTrigger value="branches" className="text-xs gap-1.5">
                <Building2 className="w-3.5 h-3.5" />
                الفروع
              </TabsTrigger>
              <TabsTrigger value="samples" className="text-xs gap-1.5">
                <Box className="w-3.5 h-3.5" />
                العينات
              </TabsTrigger>
            </TabsList>
            <Button size="sm" className="h-8 text-xs gap-1.5" onClick={() => setShowInvoiceCreate(true)}>
              <Receipt className="w-3.5 h-3.5" />
              إنشاء فاتورة
            </Button>
          </div>

          {/* ═══ Orders Table ═══ */}
          <TabsContent value="orders" className="mt-4">
            {/* Filters */}
            <div className="flex items-center gap-2 mb-4 flex-wrap" dir="rtl">
              <div className="relative">
                <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <Input
                  placeholder="بحث برقم الطلب أو العيل..."
                  className="h-8 text-xs ps-8 w-56"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <div className="flex gap-1.5">
                {(["all", "pending", "confirmed", "preparing", "shipped", "in_transit", "delivered", "cancelled"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2 py-1 rounded-lg text-xs border transition-all ${
                      statusFilter === st
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border/30 text-muted-foreground hover:border-primary/30"
                    }`}
                  >
                    {st === "all" ? "الكل" : orderStatusLabels[st]}
                  </button>
                ))}
              </div>

              <select
                value={branchFilter}
                onChange={(e) => setBranchFilter(e.target.value)}
                className="h-8 text-xs bg-card border border-border/30 rounded-lg px-2 text-muted-foreground"
              >
                <option value="all">كل الفروع</option>
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>

            <div className="rounded-xl border border-border/40 overflow-hidden bg-card/30">
              <Table>
                <TableHeader className="bg-muted/20">
                  <TableRow className="hover:bg-transparent border-border/30">
                    <TableHead className="text-start text-[11px] w-[100px]">رقم الطلب</TableHead>
                    <TableHead className="text-start text-[11px]">العميل</TableHead>
                    <TableHead className="text-start text-[11px] w-[140px]">الفرع</TableHead>
                    <TableHead className="text-start text-[11px] w-[100px]">الحالة</TableHead>
                    <TableHead className="text-start text-[11px] w-[100px]">التوصيل</TableHead>
                    <TableHead className="text-start text-[11px] w-[90px]">المبلغ</TableHead>
                    <TableHead className="text-start text-[11px] w-[80px]">التاريخ</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredOrders.map((ord) => (
                    <TableRow
                      key={ord.id}
                      className="border-border/20 cursor-pointer hover:bg-muted/10 transition-colors"
                      onClick={() => setSelectedOrder(ord)}
                    >
                      <TableCell className="font-mono text-[10px] text-muted-foreground">
                        <span dir="ltr">{ord.orderNumber}</span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-foreground">{ord.customerName}</span>
                          {ord.channelSource && (
                            <span className="text-[7px] px-1.5 py-0.5 rounded bg-muted/30 text-muted-foreground">{ord.channelSource}</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">{ord.branchName}</TableCell>
                      <TableCell>
                        <Badge className={`${orderStatusColors[ord.status]} text-[8px] h-4`}>
                          {orderStatusLabels[ord.status]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">
                        {ord.deliveryCompanyName || "—"}
                      </TableCell>
                      <TableCell className="text-xs text-foreground">
                        <span dir="ltr">${ord.total.toFixed(2)}</span>
                      </TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">{timeAgo(ord.createdAt)}</TableCell>
                    </TableRow>
                  ))}
                  {filteredOrders.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-12">
                        <Package className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                        <p className="text-xs text-muted-foreground">لا توجد طلبات</p>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          {/* ═══ Delivery Tracking ═══ */}
          <TabsContent value="delivery" className="mt-4">
            <div className="space-y-4">
              {mockOrders.filter((o) => o.deliveryCompanyId && !["cancelled", "delivered"].includes(o.status)).map((ord) => (
                <div key={ord.id} className="p-4 rounded-xl border border-border/30 bg-card/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Truck className="w-5 h-5 text-primary" />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-foreground font-mono" dir="ltr">{ord.orderNumber}</span>
                          <Badge className={`${orderStatusColors[ord.status]} text-[8px] h-4`}>
                            {orderStatusLabels[ord.status]}
                          </Badge>
                        </div>
                        <p className="text-[10px] text-muted-foreground">{ord.customerName} — {ord.deliveryCity}</p>
                      </div>
                    </div>
                    <div className="text-end">
                      <p className="text-[10px] text-muted-foreground">{ord.deliveryCompanyName}</p>
                      {ord.trackingNumber && (
                        <p className="text-[9px] text-primary font-mono">
                          <span dir="ltr">{ord.trackingNumber}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Tracking progress */}
                  <div className="flex items-center gap-0 pt-2">
                    {trackingSteps.map((step, i) => {
                      const currentStep = orderStatusStep[ord.status];
                      const stepNum = i + 1;
                      const isComplete = currentStep >= stepNum;
                      const isCurrent = currentStep === stepNum;
                      return (
                        <div key={step.key} className="flex-1 flex flex-col items-center relative">
                          {i > 0 && (
                            <div className={`absolute top-2.5 end-1/2 w-full h-0.5 ${
                              isComplete ? "bg-primary" : "bg-border/30"
                            }`} />
                          )}
                          <div className={`relative z-10 w-5 h-5 rounded-full flex items-center justify-center text-[7px] ${
                            isComplete
                              ? "bg-primary text-white"
                              : isCurrent
                                ? "bg-primary/20 text-primary border border-primary"
                                : "bg-muted/30 text-muted-foreground"
                          }`}>
                            {isComplete ? <Check className="w-3 h-3" /> : stepNum}
                          </div>
                          <span className={`text-[7px] mt-1 ${
                            isComplete || isCurrent ? "text-primary" : "text-muted-foreground/50"
                          }`}>{step.label}</span>
                        </div>
                      );
                    })}
                  </div>

                  {ord.estimatedDelivery && (
                    <p className="text-[9px] text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      الوصول المتوقع: {new Date(ord.estimatedDelivery).toLocaleDateString("ar-SA")}
                    </p>
                  )}
                </div>
              ))}
              {mockOrders.filter((o) => o.deliveryCompanyId && !["cancelled", "delivered"].includes(o.status)).length === 0 && (
                <div className="text-center py-12">
                  <Truck className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                  <p className="text-xs text-muted-foreground">لا توجد شحنات نشطة</p>
                </div>
              )}
            </div>
          </TabsContent>

          {/* ═══ Branches ═══ */}
          <TabsContent value="branches" className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {branches.map((branch) => {
                const branchOrders = mockOrders.filter((o) => o.branchId === branch.id);
                const branchRevenue = branchOrders.filter((o) => o.status !== "cancelled").reduce((s, o) => s + o.total, 0);
                return (
                  <div key={branch.id} className="p-4 rounded-xl border border-border/30 bg-card/30 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <h4 className="text-sm text-foreground">{branch.name}</h4>
                          <p className="text-[10px] text-muted-foreground">{branch.address}</p>
                        </div>
                      </div>
                      <Badge className={`text-[8px] h-4 ${branch.isActive ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                        {branch.isActive ? "نشط" : "متوقف"}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div className="text-center p-2 rounded-lg bg-muted/10">
                        <p className="text-lg text-foreground">{branchOrders.length}</p>
                        <p className="text-[8px] text-muted-foreground">طلبات</p>
                      </div>
                      <div className="text-center p-2 rounded-lg bg-muted/10">
                        <p className="text-lg text-primary"><span dir="ltr">${branchRevenue.toFixed(0)}</span></p>
                        <p className="text-[8px] text-muted-foreground">إيرادات</p>
                      </div>
                      <div className="text-center p-2 rounded-lg bg-muted/10">
                        <p className="text-lg text-foreground">{branch.manager.split(" ")[0]}</p>
                        <p className="text-[8px] text-muted-foreground">المدير</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 text-[9px] text-muted-foreground">
                      <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> <span dir="ltr">{branch.phone}</span></span>
                      <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {branch.city}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </TabsContent>

          {/* ═══ Sample Boxes ═══ */}
          <TabsContent value="samples" className="mt-4 space-y-4">
            {/* Sample box cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {sampleBoxes.map((box) => {
                const deliveries = sampleBoxDeliveries.filter((d) => d.sampleBoxId === box.id);
                return (
                  <motion.div
                    key={box.id}
                    className="group relative rounded-xl overflow-hidden cursor-pointer"
                    whileHover="hover"
                    initial="rest"
                    animate="rest"
                  >
                    {/* Glassmorphic background */}
                    <div className="absolute inset-0 rounded-xl border border-border/30 bg-gradient-to-br from-card/80 via-card/50 to-card/30 backdrop-blur-sm" />
                    
                    <div className="relative flex gap-3 p-2.5">
                      {/* ── Compact Image with hover swap ── */}
                      <div className="relative w-20 h-20 shrink-0 rounded-lg overflow-hidden">
                        {/* Closed box (default) */}
                        <motion.img
                          src={sampleBoxClosed}
                          alt={`${box.name} - مغلق`}
                          className="absolute inset-0 w-full h-full object-cover rounded-lg"
                          variants={{
                            rest: { opacity: 1, scale: 1 },
                            hover: { opacity: 0, scale: 1.08 },
                          }}
                          transition={{ duration: 0.4, ease: "easeInOut" }}
                        />
                        {/* Open box (hover) */}
                        <motion.img
                          src={sampleBoxOpen}
                          alt={`${box.name} - مفتوح`}
                          className="absolute inset-0 w-full h-full object-cover rounded-lg"
                          variants={{
                            rest: { opacity: 0, scale: 0.92 },
                            hover: { opacity: 1, scale: 1 },
                          }}
                          transition={{ duration: 0.4, ease: "easeInOut" }}
                        />
                        {/* Version badge */}
                        <div className="absolute top-1 start-1 z-10">
                          <Badge className="bg-primary/90 text-white backdrop-blur-md border-0 text-[7px] px-1.5 py-0 h-4 shadow-sm shadow-primary/20">
                            {box.version}
                          </Badge>
                        </div>
                      </div>

                      {/* ── Content ── */}
                      <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
                        {/* Title row */}
                        <div>
                          <div className="flex items-center justify-between gap-1">
                            <h4 className="text-xs text-foreground truncate">{box.name}</h4>
                            <span className="shrink-0 flex items-center gap-1 text-[8px] text-muted-foreground">
                              <Box className="w-2.5 h-2.5" />
                              {box.contents.length}
                            </span>
                          </div>
                          <p className="text-[9px] text-muted-foreground truncate mt-0.5">{box.description}</p>
                        </div>

                        {/* Sample pills - compact */}
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {box.contents.slice(0, 3).map((item) => (
                            <span
                              key={item.itemCode}
                              className="text-[7px] px-1.5 py-0.5 rounded-full bg-primary/8 text-foreground/70 border border-primary/10"
                            >
                              {item.itemName} <span className="text-primary/50 font-mono">{item.sizeML}ml</span>
                            </span>
                          ))}
                          {box.contents.length > 3 && (
                            <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-muted/20 text-muted-foreground">
                              +{box.contents.length - 3}
                            </span>
                          )}
                        </div>

                        {/* Stats row */}
                        <div className="flex items-center justify-between mt-1.5 pt-1.5 border-t border-border/10">
                          <div className="flex items-center gap-2.5">
                            <span className="flex items-center gap-1 text-[8px] text-muted-foreground">
                              <span className="w-1 h-1 rounded-full bg-primary/60 inline-block" />
                              {box.totalSent} مُرسل
                            </span>
                            <span className="flex items-center gap-1 text-[8px] text-muted-foreground">
                              <span className="w-1 h-1 rounded-full bg-emerald-500/60 inline-block" />
                              {deliveries.filter((d) => d.status === "received").length} استلم
                            </span>
                          </div>
                          <motion.span
                            className="text-[8px] text-primary flex items-center gap-0.5"
                            variants={{
                              rest: { opacity: 0, x: 4 },
                              hover: { opacity: 1, x: 0 },
                            }}
                            transition={{ duration: 0.2 }}
                          >
                            التفاصيل
                            <ChevronLeft className="w-2.5 h-2.5" />
                          </motion.span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Delivery log */}
            <h4 className="text-xs text-foreground flex items-center gap-1.5 mt-4">
              <Truck className="w-3.5 h-3.5 text-primary" />
              سجل إرسال العينات
            </h4>
            <div className="rounded-xl border border-border/40 overflow-hidden bg-card/30">
              <Table>
                <TableHeader className="bg-muted/20">
                  <TableRow className="hover:bg-transparent border-border/30">
                    <TableHead className="text-start text-[11px]">الصندوق</TableHead>
                    <TableHead className="text-start text-[11px]">العميل</TableHead>
                    <TableHead className="text-start text-[11px] w-[100px]">تاريخ الإرسال</TableHead>
                    <TableHead className="text-start text-[11px] w-[80px]">الحالة</TableHead>
                    <TableHead className="text-start text-[11px] w-[100px]">أرسلها</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sampleBoxDeliveries.map((del) => (
                    <TableRow key={del.id} className="border-border/20 hover:bg-muted/10">
                      <TableCell className="text-xs text-foreground">
                        <span className="text-muted-foreground me-1">{del.sampleBoxVersion}</span>
                        {sampleBoxes.find((b) => b.id === del.sampleBoxId)?.name}
                      </TableCell>
                      <TableCell className="text-xs">{del.customerName}</TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">{new Date(del.sentAt).toLocaleDateString("ar-SA")}</TableCell>
                      <TableCell>
                        <Badge className={`text-[8px] h-4 ${
                          del.status === "received" ? "bg-emerald-500/10 text-emerald-400" :
                          del.status === "sent" ? "bg-blue-500/10 text-blue-400" :
                          "bg-red-500/10 text-red-400"
                        }`}>
                          {del.status === "received" ? "استلم" : del.status === "sent" ? "مُرسل" : "مُرتجع"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">{del.sentBy}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

        </Tabs>

        {/* ── Order Detail Drawer ── */}
        <AnimatePresence>
          {selectedOrder && (
            <OrderDetail order={selectedOrder} onClose={() => setSelectedOrder(null)} />
          )}
        </AnimatePresence>

        {/* ── New Order Dialog ── */}
        <NewOrderDialog
          open={showNewOrderDialog}
          onClose={() => setShowNewOrderDialog(false)}
        />

        {/* ── Invoice Creation Dialog ── */}
        <InvoiceCreationDialog
          open={showInvoiceCreate}
          onClose={() => setShowInvoiceCreate(false)}
        />
      </div>
    </TooltipProvider>
  );
}

// ── New Order / Invoice Dialog ──────────────────────────

const availableProducts = [
  { code: "PERF-001", name: "عطر فاخر 100مل", price: 125 },
  { code: "PERF-002", name: "روز أمور 50مل", price: 95 },
  { code: "PERF-003", name: "إسنس غراس 75مل", price: 145 },
  { code: "PERF-005", name: "كلاسيك يورو 100مل", price: 180 },
  { code: "PERF-007", name: "فلور نوار 100مل", price: 180 },
  { code: "PERF-012", name: "جاردان دو باريس 75مل", price: 145 },
  { code: "PERF-015", name: "ليلة أمور 100مل", price: 210 },
  { code: "PERF-016", name: "فيرمنيتش إليت 100مل", price: 250 },
  { code: "OIL-003", name: "زجاج عود 10مل", price: 45 },
  { code: "ACC-001", name: "علبة هدية فاخرة", price: 35 },
];

interface InvoiceItem {
  id: string;
  productCode: string;
  name: string;
  quantity: number;
  unitPrice: number;
  discount: number;
}

function NewOrderDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryCity, setDeliveryCity] = useState("");
  const [branchId, setBranchId] = useState(branches[0].id);
  const [deliveryCompanyId, setDeliveryCompanyId] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<InvoiceItem[]>([
    { id: "new-1", productCode: availableProducts[0].code, name: availableProducts[0].name, quantity: 1, unitPrice: availableProducts[0].price, discount: 0 },
  ]);

  const addItem = () => {
    const p = availableProducts[0];
    setItems((prev) => [...prev, { id: `new-${Date.now()}`, productCode: p.code, name: p.name, quantity: 1, unitPrice: p.price, discount: 0 }]);
  };

  const removeItem = (id: string) => {
    if (items.length <= 1) return;
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  const updateItem = (id: string, field: keyof InvoiceItem, value: string | number) => {
    setItems((prev) =>
      prev.map((it) => {
        if (it.id !== id) return it;
        if (field === "productCode") {
          const product = availableProducts.find((p) => p.code === value);
          if (product) return { ...it, productCode: product.code, name: product.name, unitPrice: product.price };
        }
        return { ...it, [field]: value };
      }),
    );
  };

  const subtotal = items.reduce((sum, it) => {
    const lineTotal = it.unitPrice * it.quantity;
    const afterDiscount = lineTotal - lineTotal * (it.discount / 100);
    return sum + afterDiscount;
  }, 0);

  const vatRate = 0.15;
  const vat = subtotal * vatRate;
  const total = subtotal + vat;

  const handleSubmit = () => {
    console.log("New order:", { customerName, customerPhone, deliveryAddress, deliveryCity, branchId, deliveryCompanyId, notes, items, subtotal, vat, total });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="!max-w-3xl max-h-[90vh] flex flex-col overflow-hidden p-0">
        {/* Header */}
        <div className="shrink-0 p-5 pb-3 border-b border-border/30">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <Receipt className="w-5 h-5 text-primary" />
              فاتورة طلب جديد
            </DialogTitle>
            <DialogDescription>
              أدخل بيانات العميل والمنتجات لإنشاء طلب وفاتورة
            </DialogDescription>
          </DialogHeader>
        </div>

        {/* Body */}
        <ScrollArea dir="rtl" className="flex-1 min-h-0">
          <div className="p-5 space-y-5">
            {/* Customer & Branch */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <h4 className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" /> بيانات العميل
                </h4>
                <div className="space-y-2">
                  <div>
                    <Label className="text-[10px] text-muted-foreground">الاسم</Label>
                    <Input
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      placeholder="اسم العميل الكامل"
                      className="h-8 text-xs mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-muted-foreground">الهاتف</Label>
                    <Input
                      value={customerPhone}
                      onChange={(e) => setCustomerPhone(e.target.value)}
                      placeholder="+966 5x xxx xxxx"
                      className="h-8 text-xs mt-1"
                      dir="ltr"
                    />
                  </div>
                </div>
              </div>
              <div className="space-y-3">
                <h4 className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5" /> الفرع والتوصيل
                </h4>
                <div className="space-y-2">
                  <div>
                    <Label className="text-[10px] text-muted-foreground">الفرع</Label>
                    <select
                      value={branchId}
                      onChange={(e) => setBranchId(e.target.value)}
                      className="w-full h-8 text-xs bg-card border border-border/30 rounded-lg px-2 text-foreground mt-1"
                    >
                      {branches.map((b) => (
                        <option key={b.id} value={b.id}>{b.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label className="text-[10px] text-muted-foreground">شركة التوصيل</Label>
                    <select
                      value={deliveryCompanyId}
                      onChange={(e) => setDeliveryCompanyId(e.target.value)}
                      className="w-full h-8 text-xs bg-card border border-border/30 rounded-lg px-2 text-foreground mt-1"
                    >
                      <option value="">— بدون توصيل (استلام فرع) —</option>
                      {deliveryCompanies.map((dc) => (
                        <option key={dc.id} value={dc.id}>{dc.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Delivery Address */}
            {deliveryCompanyId && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-[10px] text-muted-foreground">عنوان التوصيل</Label>
                  <Input
                    value={deliveryAddress}
                    onChange={(e) => setDeliveryAddress(e.target.value)}
                    placeholder="الحي، الشارع، رقم المبنى"
                    className="h-8 text-xs mt-1"
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-muted-foreground">المدينة</Label>
                  <Input
                    value={deliveryCity}
                    onChange={(e) => setDeliveryCity(e.target.value)}
                    placeholder="مثال: الرياض"
                    className="h-8 text-xs mt-1"
                  />
                </div>
              </div>
            )}

            {/* Items Table */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <Package className="w-3.5 h-3.5" /> بنود الفاتورة
                </h4>
                <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1" onClick={addItem}>
                  <Plus className="w-3 h-3" /> إضافة منتج
                </Button>
              </div>
              <div className="rounded-lg border border-border/30 overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/10 hover:bg-muted/10 border-border/20">
                      <TableHead className="text-start text-[9px]">المنتج</TableHead>
                      <TableHead className="text-start text-[9px] w-[60px]">الكمية</TableHead>
                      <TableHead className="text-start text-[9px] w-[80px]">السعر</TableHead>
                      <TableHead className="text-start text-[9px] w-[60px]">خصم %</TableHead>
                      <TableHead className="text-start text-[9px] w-[80px]">الإجمالي</TableHead>
                      <TableHead className="text-center text-[9px] w-[40px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((item) => {
                      const lineTotal = item.unitPrice * item.quantity;
                      const afterDiscount = lineTotal - lineTotal * (item.discount / 100);
                      return (
                        <TableRow key={item.id} className="border-border/10">
                          <TableCell className="p-1.5">
                            <select
                              value={item.productCode}
                              onChange={(e) => updateItem(item.id, "productCode", e.target.value)}
                              className="w-full h-7 text-[10px] bg-transparent border border-border/20 rounded px-1.5 text-foreground"
                            >
                              {availableProducts.map((p) => (
                                <option key={p.code} value={p.code}>{p.name}</option>
                              ))}
                            </select>
                          </TableCell>
                          <TableCell className="p-1.5">
                            <Input
                              type="number"
                              min={1}
                              value={item.quantity}
                              onChange={(e) => updateItem(item.id, "quantity", parseInt(e.target.value) || 1)}
                              className="h-7 text-[10px] text-center px-1"
                            />
                          </TableCell>
                          <TableCell className="p-1.5 text-[10px] text-muted-foreground">
                            <span dir="ltr">${item.unitPrice}</span>
                          </TableCell>
                          <TableCell className="p-1.5">
                            <Input
                              type="number"
                              min={0}
                              max={100}
                              value={item.discount}
                              onChange={(e) => updateItem(item.id, "discount", parseInt(e.target.value) || 0)}
                              className="h-7 text-[10px] text-center px-1"
                            />
                          </TableCell>
                          <TableCell className="p-1.5 text-[10px] text-foreground">
                            <span dir="ltr">${afterDiscount.toFixed(2)}</span>
                          </TableCell>
                          <TableCell className="p-1.5 text-center">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 text-muted-foreground hover:text-red-400"
                              onClick={() => removeItem(item.id)}
                              disabled={items.length <= 1}
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>

            {/* Totals */}
            <div className="p-3 rounded-lg border border-primary/20 bg-primary/5 space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-muted-foreground">المجموع الفرعي</span>
                <span className="text-foreground" dir="ltr">${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">ضريبة القيمة المضافة (15%)</span>
                <span className="text-foreground" dir="ltr">${vat.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pt-1.5 border-t border-primary/20">
                <span className="text-foreground">الإجمالي</span>
                <span className="text-primary text-sm" dir="ltr">${total.toFixed(2)}</span>
              </div>
            </div>

            {/* Notes */}
            <div>
              <Label className="text-[10px] text-muted-foreground">ملاحظات</Label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="ملاحظات إضافية على الطلب..."
                className="mt-1 text-xs min-h-[60px]"
              />
            </div>
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="shrink-0 p-4 pt-3 border-t border-border/30 flex items-center gap-2">
          <Button className="flex-1 gap-1.5 h-9" onClick={handleSubmit}>
            <CreditCard className="w-4 h-4" />
            إنشاء الطلب والفاتورة
          </Button>
          <Button variant="outline" className="h-9 gap-1.5" onClick={onClose}>
            <X className="w-4 h-4" />
            إلغاء
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Order Detail ────────────────────────────────────────

function OrderDetail({ order, onClose }: { order: Order; onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex justify-start"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/40" />
      <motion.div
        initial={{ x: -400 }}
        animate={{ x: 0 }}
        exit={{ x: -400 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="relative w-[520px] h-full bg-card border-s border-border/40 shadow-2xl flex flex-col overflow-hidden ms-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="shrink-0 p-4 border-b border-border/30 bg-card/80">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-muted-foreground" dir="ltr">{order.orderNumber}</span>
              <Badge className={`${orderStatusColors[order.status]} text-[8px] h-4`}>
                {orderStatusLabels[order.status]}
              </Badge>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <h3 className="text-sm text-foreground">طلب {order.customerName}</h3>
          <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-0.5"><Building2 className="w-3 h-3" /> {order.branchName}</span>
            {order.channelSource && <span className="flex items-center gap-0.5"><MessageCircle className="w-3 h-3" /> {order.channelSource}</span>}
            {order.assignedAgent && <span className="flex items-center gap-0.5"><User className="w-3 h-3" /> {order.assignedAgent}</span>}
          </div>
        </div>

        <ScrollArea dir="rtl" className="flex-1 min-h-0">
          <div className="p-4 space-y-4">

            {/* Customer info */}
            <div className="p-3 rounded-lg border border-border/20 bg-muted/10 space-y-1">
              <p className="text-[9px] text-muted-foreground">بيانات العميل</p>
              <p className="text-xs text-foreground">{order.customerName}</p>
              <p className="text-[10px] text-muted-foreground"><span dir="ltr">{order.customerPhone}</span></p>
              <p className="text-[10px] text-muted-foreground">{order.deliveryAddress}، {order.deliveryCity}</p>
            </div>

            {/* Items */}
            <div>
              <p className="text-[10px] text-muted-foreground mb-2">بنود الطلب</p>
              <div className="rounded-lg border border-border/20 overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/10 hover:bg-muted/10 border-border/20">
                      <TableHead className="text-start text-[9px]">المنتج</TableHead>
                      <TableHead className="text-start text-[9px] w-[50px]">الكمية</TableHead>
                      <TableHead className="text-start text-[9px] w-[70px]">السعر</TableHead>
                      <TableHead className="text-start text-[9px] w-[60px]">الإجمالي</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {order.items.map((item) => (
                      <TableRow key={item.id} className="border-border/10 hover:bg-transparent">
                        <TableCell className="text-[10px]">
                          <span className="text-foreground">{item.name}</span>
                          <span className="text-muted-foreground ms-1 font-mono text-[8px]">{item.itemCode}</span>
                          {item.discount > 0 && (
                            <Badge className="bg-red-500/10 text-red-400 text-[7px] h-3.5 ms-1">-{item.discount}%</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-[10px] text-muted-foreground">{item.quantity}</TableCell>
                        <TableCell className="text-[10px] text-muted-foreground"><span dir="ltr">${item.unitPrice}</span></TableCell>
                        <TableCell className="text-[10px] text-foreground"><span dir="ltr">${item.total.toFixed(2)}</span></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Totals */}
              <div className="mt-2 space-y-1 text-[10px] text-end">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">المجموع الفرعي</span>
                  <span className="text-foreground" dir="ltr">${order.subtotal.toFixed(2)}</span>
                </div>
                {order.discount > 0 && (
                  <div className="flex justify-between">
                    <span className="text-red-400">الخصم</span>
                    <span className="text-red-400" dir="ltr">-${order.discount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ضريبة القيمة المضافة</span>
                  <span className="text-foreground" dir="ltr">${order.vat.toFixed(2)}</span>
                </div>
                <div className="flex justify-between pt-1 border-t border-border/20">
                  <span className="text-foreground">الإجمالي</span>
                  <span className="text-primary" dir="ltr">${order.total.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Delivery */}
            {order.deliveryCompanyId && (
              <div className="p-3 rounded-lg border border-border/20 bg-muted/10 space-y-2">
                <p className="text-[9px] text-muted-foreground">معلومات التوصيل</p>
                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-muted-foreground">الشركة: </span>
                    <span className="text-foreground">{order.deliveryCompanyName}</span>
                  </div>
                  {order.trackingNumber && (
                    <div>
                      <span className="text-muted-foreground">رقم التتبع: </span>
                      <span className="text-primary font-mono" dir="ltr">{order.trackingNumber}</span>
                    </div>
                  )}
                  {order.estimatedDelivery && (
                    <div>
                      <span className="text-muted-foreground">لوصول المتوقع: </span>
                      <span className="text-foreground">{new Date(order.estimatedDelivery).toLocaleDateString("ar-SA")}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Invoice link */}
            {order.invoiceNumber && (
              <div className="p-3 rounded-lg border border-primary/20 bg-primary/5 flex items-center justify-between">
                <div className="flex items-center gap-2 text-[10px]">
                  <FileText className="w-4 h-4 text-primary" />
                  <span className="text-foreground">الفاتورة: </span>
                  <span className="text-primary font-mono" dir="ltr">{order.invoiceNumber}</span>
                </div>
                <Button variant="ghost" size="sm" className="h-6 text-[9px] text-primary">
                  <Eye className="w-3 h-3 me-1" /> عرض
                </Button>
              </div>
            )}

            {/* Notes */}
            {order.notes && (
              <div className="p-3 rounded-lg border border-border/20 bg-muted/10">
                <p className="text-[9px] text-muted-foreground mb-1">ملاحظات</p>
                <p className="text-[10px] text-foreground">{order.notes}</p>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="shrink-0 p-3 border-t border-border/30 flex items-center gap-2">
          <Button size="sm" className="h-8 text-xs flex-1 gap-1.5">
            <Check className="w-3.5 h-3.5" />
            تحديث الحالة
          </Button>
          {order.customerId && (
            <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
              <User className="w-3.5 h-3.5" />
              بطاقة العميل
            </Button>
          )}
          <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
            <FileText className="w-3.5 h-3.5" />
            فاتورة
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}