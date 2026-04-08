import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Package, Clock, Building2, X, AlertTriangle,
  TrendingUp, ShoppingCart, AlertCircle, Sparkles,
  ArrowUpRight, ArrowDownRight, Zap, PackageCheck, RotateCcw,
  BarChart3,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../ui/table";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";
import {
  productInventory, urgencyLabels, urgencyColors,
  type ProductInventory, type UrgencyLevel,
} from "../orders/ord-data";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  ResponsiveContainer, Cell, Tooltip as RechartsTooltip,
  AreaChart, Area,
} from "recharts";
import { UrgencyInfographic } from "./urgency-infographic";

// ── Month names ─────────────────────────────────────────

const monthNames = ["سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر", "يناير", "فبراير"];

// ── Main Forecasting Component ──────────────────────────

export function Forecasting() {
  const [urgFilter, setUrgFilter] = useState<UrgencyLevel | "all">("all");
  const [selectedProduct, setSelectedProduct] = useState<ProductInventory | null>(null);

  const sorted = useMemo(() => {
    const urgOrder: Record<UrgencyLevel, number> = { critical: 0, warning: 1, normal: 2, surplus: 3 };
    let list = [...productInventory];
    if (urgFilter !== "all") list = list.filter((p) => p.urgency === urgFilter);
    return list.sort((a, b) => urgOrder[a.urgency] - urgOrder[b.urgency]);
  }, [urgFilter]);

  const summaryStats = useMemo(() => {
    const critical = productInventory.filter((p) => p.urgency === "critical").length;
    const warning = productInventory.filter((p) => p.urgency === "warning").length;
    const totalReorderCost = productInventory.filter((p) => p.suggestedOrderQty > 0).reduce((s, p) => s + p.suggestedOrderQty * p.unitCost, 0);
    const avgDaysLeft = productInventory.reduce((s, p) => s + p.daysOfStockLeft, 0) / productInventory.length;
    return { critical, warning, totalReorderCost, avgDaysLeft };
  }, []);

  const demandChartData = useMemo(() =>
    monthNames.map((m, i) => ({
      month: m,
      ...Object.fromEntries(
        productInventory.filter((p) => p.urgency === "critical" || p.urgency === "warning").map((p) => [p.name.split(" ")[0], p.monthlyTrend[i]]),
      ),
    })),
  []);

  const urgencyDistribution = useMemo(() => [
    { name: "حرج", value: productInventory.filter((p) => p.urgency === "critical").length, fill: "var(--color-destructive)" },
    { name: "تحذير", value: productInventory.filter((p) => p.urgency === "warning").length, fill: "var(--color-primary)" },
    { name: "طبيعي", value: productInventory.filter((p) => p.urgency === "normal").length, fill: "#10b981" },
    { name: "فائض", value: productInventory.filter((p) => p.urgency === "surplus").length, fill: "#60a5fa" },
  ], []);

  const trendColors = ["var(--color-destructive)", "var(--color-primary)", "#10b981", "#a78bfa", "#60a5fa", "#f472b6"];

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-5">
        {/* ── Summary Cards ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3" dir="rtl">
          <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/5 text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <p className="text-2xl text-red-400">{summaryStats.critical}</p>
            </div>
            <p className="text-[10px] text-muted-foreground">منتجات حرجة</p>
          </div>
          <div className="p-3 rounded-xl border border-primary/30 bg-primary/5 text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <AlertTriangle className="w-4 h-4 text-primary" />
              <p className="text-2xl text-primary">{summaryStats.warning}</p>
            </div>
            <p className="text-[10px] text-muted-foreground">منتجات تحتاج تزويد</p>
          </div>
          <div className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <ShoppingCart className="w-4 h-4 text-foreground" />
              <p className="text-2xl text-foreground"><span dir="ltr">${summaryStats.totalReorderCost.toLocaleString()}</span></p>
            </div>
            <p className="text-[10px] text-muted-foreground">تكلفة التزويد المقترح</p>
          </div>
          <div className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Clock className="w-4 h-4 text-foreground" />
              <p className="text-2xl text-foreground">{Math.round(summaryStats.avgDaysLeft)}<span className="text-[10px] text-muted-foreground ms-0.5">يوم</span></p>
            </div>
            <p className="text-[10px] text-muted-foreground">متوسط أيام المخزون</p>
          </div>
        </div>

        {/* ── Charts Row ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 p-4 rounded-xl border border-border/30 bg-card/30">
            <h4 className="text-xs text-foreground flex items-center gap-1.5 mb-3">
              <TrendingUp className="w-3.5 h-3.5 text-primary" />
              اتجاه الطلب — المنتجات المطلوبة (آخر 6 أشهر)
            </h4>
            <div style={{ direction: "ltr" }}>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={demandChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="month" tick={{ fontSize: 10, fill: "var(--color-muted-foreground)" }} />
                  <YAxis tick={{ fontSize: 10, fill: "var(--color-muted-foreground)" }} />
                  <RechartsTooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 11, direction: "rtl" }} />
                  {productInventory.filter((p) => p.urgency === "critical" || p.urgency === "warning").map((p, i) => (
                    <Area key={p.itemCode} type="monotone" dataKey={p.name.split(" ")[0]} stroke={trendColors[i % trendColors.length]} fill={trendColors[i % trendColors.length]} fillOpacity={0.1} strokeWidth={2} />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="p-4 rounded-xl border border-border/30 bg-card/30">
            <h4 className="text-xs text-foreground flex items-center gap-1.5 mb-3">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              توزيع حالة المخزون
            </h4>
            <UrgencyInfographic data={urgencyDistribution} />
          </div>
        </div>

        {/* ── Filter Bar ── */}
        <div className="flex items-center gap-2 flex-wrap" dir="rtl">
          <h4 className="text-xs text-foreground flex items-center gap-1.5 me-2">
            <PackageCheck className="w-3.5 h-3.5 text-primary" />
            توصيات إعادة الطلب
          </h4>
          {(["all", "critical", "warning", "normal", "surplus"] as const).map((u) => (
            <button key={u} onClick={() => setUrgFilter(u)} className={`px-2.5 py-1 rounded-lg text-[9px] border transition-all ${urgFilter === u ? "border-primary bg-primary/10 text-primary" : "border-border/30 text-muted-foreground hover:border-primary/30"}`}>
              {u === "all" ? "الكل" : urgencyLabels[u].split("—")[0].trim()}
            </button>
          ))}
        </div>

        {/* ── Products Table ── */}
        <div className="rounded-xl border border-border/40 overflow-hidden bg-card/30">
          <Table>
            <TableHeader className="bg-muted/20">
              <TableRow className="hover:bg-transparent border-border/30">
                <TableHead className="text-start text-[11px]">المنتج</TableHead>
                <TableHead className="text-start text-[11px] w-[70px]">المخزون</TableHead>
                <TableHead className="text-start text-[11px] w-[80px]">مبيع/يوم</TableHead>
                <TableHead className="text-start text-[11px] w-[80px]">أيام متبقية</TableHead>
                <TableHead className="text-start text-[11px] w-[70px]">الاتجاه</TableHead>
                <TableHead className="text-start text-[11px] w-[90px]">الحالة</TableHead>
                <TableHead className="text-start text-[11px] w-[80px]">كمية الطلب</TableHead>
                <TableHead className="text-start text-[11px] w-[80px]">التكلفة</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((p) => {
                const trend30vs60 = p.last60DaysSold > 0 ? ((p.last30DaysSold - (p.last60DaysSold - p.last30DaysSold)) / (p.last60DaysSold - p.last30DaysSold)) * 100 : 0;
                const trendUp = trend30vs60 > 5;
                const trendDown = trend30vs60 < -5;
                const stockPercent = Math.min(100, Math.round((p.currentStock / p.maxStock) * 100));
                return (
                  <TableRow key={p.itemCode} className="border-border/20 cursor-pointer hover:bg-muted/10 transition-colors" onClick={() => setSelectedProduct(p)}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className={`w-1.5 h-8 rounded-full shrink-0 ${p.urgency === "critical" ? "bg-red-500" : p.urgency === "warning" ? "bg-primary" : p.urgency === "normal" ? "bg-emerald-500" : "bg-blue-400"}`} />
                        <div>
                          <p className="text-xs text-foreground">{p.name}</p>
                          <p className="text-[9px] text-muted-foreground flex items-center gap-1">
                            <span dir="ltr" className="font-mono">{p.itemCode}</span>
                            <span>•</span>
                            <span>{p.supplierName}</span>
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <p className={`text-xs ${p.currentStock <= p.reorderPoint ? "text-red-400" : "text-foreground"}`}>{p.currentStock}</p>
                        <div className="w-full h-1.5 rounded-full bg-muted/30 overflow-hidden">
                          <div className={`h-full rounded-full transition-all ${stockPercent < 20 ? "bg-red-500" : stockPercent < 50 ? "bg-primary" : "bg-emerald-500"}`} style={{ width: `${stockPercent}%` }} />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-foreground">{p.avgDailySales.toFixed(1)}</TableCell>
                    <TableCell>
                      <span className={`text-xs ${p.daysOfStockLeft <= 7 ? "text-red-400" : p.daysOfStockLeft <= 14 ? "text-primary" : "text-foreground"}`}>{p.daysOfStockLeft} يوم</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {trendUp ? <ArrowUpRight className="w-3.5 h-3.5 text-red-400" /> : trendDown ? <ArrowDownRight className="w-3.5 h-3.5 text-emerald-400" /> : <span className="text-[9px] text-muted-foreground">—</span>}
                        <span className={`text-[9px] ${trendUp ? "text-red-400" : trendDown ? "text-emerald-400" : "text-muted-foreground"}`}>
                          {trendUp ? "متصاعد" : trendDown ? "متراجع" : "مستقر"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={`text-[8px] h-4 border ${urgencyColors[p.urgency]}`}>
                        {p.urgency === "critical" ? "حرج" : p.urgency === "warning" ? "تحذير" : p.urgency === "normal" ? "طبيعي" : "فائض"}
                      </Badge>
                    </TableCell>
                    <TableCell>{p.suggestedOrderQty > 0 ? <span className="text-xs text-primary">{p.suggestedOrderQty} وحدة</span> : <span className="text-[10px] text-muted-foreground/50">—</span>}</TableCell>
                    <TableCell>{p.suggestedOrderQty > 0 ? <span className="text-xs text-foreground" dir="ltr">${(p.suggestedOrderQty * p.unitCost).toLocaleString()}</span> : <span className="text-[10px] text-muted-foreground/50">—</span>}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>

        {/* ── Reorder Summary ── */}
        {productInventory.filter((p) => p.suggestedOrderQty > 0).length > 0 && (
          <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs text-foreground flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-primary" />
                ملخص طلب التزويد المقترح
              </h4>
              <Button size="sm" className="h-7 text-[10px] gap-1">
                <ShoppingCart className="w-3 h-3" />
                إنشاء أمر شراء
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {productInventory.filter((p) => p.suggestedOrderQty > 0).map((p) => (
                <div key={p.itemCode} className="flex items-center justify-between p-2 rounded-lg bg-card/50 border border-border/20">
                  <div className="flex items-center gap-2">
                    <div className={`w-1 h-6 rounded-full ${p.urgency === "critical" ? "bg-red-500" : "bg-primary"}`} />
                    <div>
                      <p className="text-[10px] text-foreground">{p.name}</p>
                      <p className="text-[8px] text-muted-foreground">{p.supplierName} • {p.leadTimeDays} يوم توريد</p>
                    </div>
                  </div>
                  <div className="text-end">
                    <p className="text-[10px] text-primary">{p.suggestedOrderQty} وحدة</p>
                    <p className="text-[8px] text-muted-foreground" dir="ltr">${(p.suggestedOrderQty * p.unitCost).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-primary/20 text-[11px]">
              <span className="text-muted-foreground">إجمالي تكلفة التزويد</span>
              <span className="text-primary text-sm" dir="ltr">${productInventory.filter((p) => p.suggestedOrderQty > 0).reduce((s, p) => s + p.suggestedOrderQty * p.unitCost, 0).toLocaleString()}</span>
            </div>
          </div>
        )}

        {/* ── Product Detail Drawer ── */}
        <AnimatePresence>
          {selectedProduct && <ProductForecastDetail product={selectedProduct} onClose={() => setSelectedProduct(null)} />}
        </AnimatePresence>
      </div>
    </TooltipProvider>
  );
}

// ── Dashboard Widget (compact version) ──────────────────

export function ForecastingWidget({ onNavigate }: { onNavigate?: () => void }) {
  const criticalItems = productInventory.filter((p) => p.urgency === "critical");
  const warningItems = productInventory.filter((p) => p.urgency === "warning");
  const allUrgent = [...criticalItems, ...warningItems];
  const totalReorderCost = productInventory.filter((p) => p.suggestedOrderQty > 0).reduce((s, p) => s + p.suggestedOrderQty * p.unitCost, 0);

  return (
    <div className="space-y-3">
      {/* Header stats row */}
      <div className="grid grid-cols-3 gap-2">
        <div className="p-2 rounded-lg border border-red-500/20 bg-red-500/5 text-center">
          <p className="text-lg text-red-400">{criticalItems.length}</p>
          <p className="text-[8px] text-muted-foreground">حرج</p>
        </div>
        <div className="p-2 rounded-lg border border-primary/20 bg-primary/5 text-center">
          <p className="text-lg text-primary">{warningItems.length}</p>
          <p className="text-[8px] text-muted-foreground">تحذير</p>
        </div>
        <div className="p-2 rounded-lg border border-border/20 bg-card/30 text-center">
          <p className="text-lg text-foreground" dir="ltr">${(totalReorderCost / 1000).toFixed(1)}k</p>
          <p className="text-[8px] text-muted-foreground">تكلفة التزويد</p>
        </div>
      </div>

      {/* Urgent items list */}
      <div className="space-y-1.5">
        {allUrgent.slice(0, 5).map((p) => {
          const stockPercent = Math.min(100, Math.round((p.currentStock / p.maxStock) * 100));
          return (
            <div key={p.itemCode} className="flex items-center gap-2 p-2 rounded-lg bg-secondary/30 border border-border/50 hover:bg-secondary/60 hover:border-primary/30 transition-all cursor-pointer">
              <div className={`w-1 h-6 rounded-full shrink-0 ${p.urgency === "critical" ? "bg-red-500" : "bg-primary"}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] text-foreground truncate">{p.name}</p>
                  <span className={`text-[9px] shrink-0 ms-2 ${p.daysOfStockLeft <= 7 ? "text-red-400" : "text-primary"}`}>{p.daysOfStockLeft} يوم</span>
                </div>
                <div className="w-full h-1 rounded-full bg-muted/30 overflow-hidden mt-1">
                  <div className={`h-full rounded-full ${stockPercent < 20 ? "bg-red-500" : "bg-primary"}`} style={{ width: `${stockPercent}%` }} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {onNavigate && (
        <Button
          variant="link"
          className="w-full text-xs text-muted-foreground hover:text-primary"
          onClick={onNavigate}
        >
          عرض جميع التنبؤات والتوصيات
        </Button>
      )}
    </div>
  );
}

// ── Product Forecast Detail Drawer ──────────────────────

function ProductForecastDetail({ product, onClose }: { product: ProductInventory; onClose: () => void }) {
  const trendData = monthNames.map((m, i) => ({ month: m, sold: product.monthlyTrend[i] }));
  const stockPercent = Math.round((product.currentStock / product.maxStock) * 100);
  const trend30vs60 = product.last60DaysSold > 0 ? ((product.last30DaysSold - (product.last60DaysSold - product.last30DaysSold)) / (product.last60DaysSold - product.last30DaysSold)) * 100 : 0;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex justify-start" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40" />
      <motion.div initial={{ x: -400 }} animate={{ x: 0 }} exit={{ x: -400 }} transition={{ type: "spring", stiffness: 300, damping: 30 }} className="relative w-[480px] h-full bg-card border-s border-border/40 shadow-2xl flex flex-col overflow-hidden ms-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="shrink-0 p-4 border-b border-border/30 bg-card/80">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-muted-foreground" dir="ltr">{product.itemCode}</span>
              <Badge className={`text-[8px] h-4 border ${urgencyColors[product.urgency]}`}>{urgencyLabels[product.urgency]}</Badge>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}><X className="w-4 h-4" /></Button>
          </div>
          <h3 className="text-sm text-foreground">{product.name}</h3>
          <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-0.5"><Building2 className="w-3 h-3" /> {product.topBranch}</span>
            <span className="flex items-center gap-0.5"><Package className="w-3 h-3" /> {product.supplierName}</span>
          </div>
        </div>

        <ScrollArea dir="rtl" className="flex-1 min-h-0">
          <div className="p-4 space-y-4">
            {/* Stock Visual */}
            <div className="p-3 rounded-lg border border-border/20 bg-muted/10 space-y-3">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground">مستوى المخزون</span>
                <span className={`${product.currentStock <= product.reorderPoint ? "text-red-400" : "text-foreground"}`}>{product.currentStock} / {product.maxStock}</span>
              </div>
              <div className="w-full h-3 rounded-full bg-muted/30 overflow-hidden">
                <div className={`h-full rounded-full transition-all ${stockPercent < 20 ? "bg-red-500" : stockPercent < 50 ? "bg-primary" : "bg-emerald-500"}`} style={{ width: `${stockPercent}%` }} />
              </div>
              <div className="flex items-center justify-between text-[9px] text-muted-foreground">
                <span>نقطة إعادة الطلب: {product.reorderPoint}</span>
                <span>الحد الأقصى: {product.maxStock}</span>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg border border-border/20 bg-muted/10 text-center">
                <p className="text-lg text-foreground">{product.avgDailySales.toFixed(1)}</p>
                <p className="text-[8px] text-muted-foreground">متوسط المبيعات/يوم</p>
              </div>
              <div className="p-3 rounded-lg border border-border/20 bg-muted/10 text-center">
                <p className={`text-lg ${product.daysOfStockLeft <= 7 ? "text-red-400" : "text-foreground"}`}>{product.daysOfStockLeft}</p>
                <p className="text-[8px] text-muted-foreground">أيام مخزون متبقية</p>
              </div>
              <div className="p-3 rounded-lg border border-border/20 bg-muted/10 text-center">
                <p className="text-lg text-foreground">{product.last30DaysSold}</p>
                <p className="text-[8px] text-muted-foreground">مبيعات آخر 30 يوم</p>
              </div>
              <div className="p-3 rounded-lg border border-border/20 bg-muted/10 text-center">
                <p className="text-lg text-foreground">{product.leadTimeDays} يوم</p>
                <p className="text-[8px] text-muted-foreground">مدة التوريد</p>
              </div>
            </div>

            {/* Trend Analysis */}
            <div className="p-3 rounded-lg border border-border/20 bg-muted/10 space-y-2">
              <p className="text-[9px] text-muted-foreground">تحليل الاتجاه</p>
              <div className="flex items-center gap-2">
                {trend30vs60 > 5 ? <ArrowUpRight className="w-4 h-4 text-red-400" /> : trend30vs60 < -5 ? <ArrowDownRight className="w-4 h-4 text-emerald-400" /> : <TrendingUp className="w-4 h-4 text-muted-foreground" />}
                <span className="text-xs text-foreground">
                  {trend30vs60 > 5 ? `الطلب متصاعد بنسبة ${Math.round(trend30vs60)}% — يُنصح بزيادة الكمية` : trend30vs60 < -5 ? `الطلب متراجع بنسبة ${Math.abs(Math.round(trend30vs60))}%` : "الطلب مستقر"}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[9px] text-muted-foreground">
                <span>المعامل الموسمي: <span className="text-foreground">{product.seasonalIndex.toFixed(2)}</span></span>
                {product.seasonalIndex > 1.1 && <Badge className="bg-red-500/10 text-red-400 text-[7px] h-3.5">موسم عالي</Badge>}
              </div>
            </div>

            {/* Monthly Trend Chart */}
            <div className="p-3 rounded-lg border border-border/20 bg-muted/10 space-y-2">
              <p className="text-[9px] text-muted-foreground">مبيعات آخر 6 أشهر</p>
              <div style={{ direction: "ltr" }}>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="month" tick={{ fontSize: 9, fill: "var(--color-muted-foreground)" }} />
                    <YAxis tick={{ fontSize: 9, fill: "var(--color-muted-foreground)" }} />
                    <RechartsTooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 11, direction: "rtl" }} />
                    <Bar dataKey="sold" radius={[4, 4, 0, 0]}>
                      {trendData.map((_, i) => (
                        <Cell key={`cell-${i}`} fill={i === trendData.length - 1 ? "var(--color-primary)" : "var(--color-muted-foreground)"} fillOpacity={i === trendData.length - 1 ? 1 : 0.3} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recommendation */}
            {product.suggestedOrderQty > 0 && (
              <div className="p-3 rounded-lg border border-primary/20 bg-primary/5 space-y-2">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-primary" />
                  <p className="text-xs text-foreground">توصية إعادة الطلب</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div><span className="text-muted-foreground">الكمية المقترحة: </span><span className="text-primary">{product.suggestedOrderQty} وحدة</span></div>
                  <div><span className="text-muted-foreground">التكلفة: </span><span className="text-primary" dir="ltr">${(product.suggestedOrderQty * product.unitCost).toLocaleString()}</span></div>
                  <div><span className="text-muted-foreground">المورد: </span><span className="text-foreground">{product.supplierName}</span></div>
                  <div><span className="text-muted-foreground">مدة التوريد: </span><span className="text-foreground">{product.leadTimeDays} يوم</span></div>
                </div>
                <p className="text-[9px] text-muted-foreground">آخر تزويد: {new Date(product.lastRestockedAt).toLocaleDateString("ar-SA")}</p>
              </div>
            )}

            {/* Pricing Info */}
            <div className="p-3 rounded-lg border border-border/20 bg-muted/10">
              <p className="text-[9px] text-muted-foreground mb-2">معلومات التسعير</p>
              <div className="grid grid-cols-3 gap-2 text-[10px]">
                <div className="text-center"><p className="text-foreground" dir="ltr">${product.unitCost}</p><p className="text-[8px] text-muted-foreground">تكلفة الوحدة</p></div>
                <div className="text-center"><p className="text-foreground" dir="ltr">${product.unitPrice}</p><p className="text-[8px] text-muted-foreground">سعر البيع</p></div>
                <div className="text-center"><p className="text-emerald-400" dir="ltr">{Math.round(((product.unitPrice - product.unitCost) / product.unitCost) * 100)}%</p><p className="text-[8px] text-muted-foreground">هامش الربح</p></div>
              </div>
            </div>
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="shrink-0 p-3 border-t border-border/30 flex items-center gap-2">
          {product.suggestedOrderQty > 0 && (
            <Button size="sm" className="h-8 text-xs flex-1 gap-1.5"><ShoppingCart className="w-3.5 h-3.5" /> طلب {product.suggestedOrderQty} وحدة</Button>
          )}
          <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5"><RotateCcw className="w-3.5 h-3.5" /> تحديث المخزون</Button>
        </div>
      </motion.div>
    </motion.div>
  );
}