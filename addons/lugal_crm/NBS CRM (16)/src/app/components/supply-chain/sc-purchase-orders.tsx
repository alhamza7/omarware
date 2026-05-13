import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { toast } from "sonner";
import {
  Plus,
  Search,
  Eye,
  Download,
  Share2,
  ChevronDown,
  ChevronUp,
  Upload,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  TriangleAlert,
  PackageOpen,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "../ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { ScrollArea } from "../ui/scroll-area";
import {
  purchaseOrders as demoPurchaseOrders,
  suggestedPOs,
  suppliers,
  poStatusConfig,
  currencySymbols,
  type PurchaseOrder,
  type SuggestedPO,
  type Division,
  type Currency,
} from "./sc-data";
import { supplyService } from "../../../features/supply-chain/services/supplyService";

type SubTab = "all" | "open" | "suggested" | "packing";

/** Subset of Odoo `supply_po_list` / `supply_po_get` payload used for grid + packing actions */
export type ApiSupplyPo = {
  id: number;
  name?: string;
  lines?: Array<{
    id: number;
    product_name?: string;
    size?: string;
    quantity?: number;
    quantity_pcs?: number;
    unit_price?: number;
  }>;
  vendor_name?: string;
  division?: string;
  currency_name?: string;
  status?: string;
  total_amount?: number;
  created_at?: string;
  notes?: string;
  created_by_name?: string;
  container_name?: string;
};

const fmt = (n: number) =>
  new Intl.NumberFormat("ar-SA").format(n);

function mapCurrency(name?: string): Currency {
  const u = (name || "USD").toUpperCase().slice(0, 3);
  if (u === "EUR" || u === "CNY" || u === "SAR" || u === "IQD" || u === "USD") return u;
  return "USD";
}

function mapApiSupplyPoToPurchaseOrder(api: ApiSupplyPo): PurchaseOrder {
  const statusMap: Record<string, PurchaseOrder["status"]> = {
    draft: "draft",
    confirmed: "confirmed",
    cancelled: "cancelled",
    shipped: "shipped",
    received: "received",
    sent: "sent",
  };
  const st = statusMap[api.status || ""] || "draft";
  const div: Division =
    api.division === "europe" || api.division === "china" ? api.division : "china";
  return {
    id: api.name || `PO-${api.id}`,
    odooId: api.id,
    supplierId: `v-${api.id}`,
    supplierName: api.vendor_name || "—",
    division: div,
    currency: mapCurrency(api.currency_name),
    status: st,
    items: (api.lines || []).map((ln) => ({
      id: `L-${ln.id}`,
      name: ln.product_name || "—",
      size: ln.size || "—",
      qty: Number(ln.quantity ?? ln.quantity_pcs ?? 0),
      unitPrice: Number(ln.unit_price ?? 0),
      category: "other",
    })),
    totalAmount: Number(api.total_amount ?? 0),
    createdAt: (api.created_at || "").slice(0, 10) || "—",
    updatedAt: (api.created_at || "").slice(0, 10) || "—",
    containerNumber: api.container_name || undefined,
    notes: api.notes || "",
    hasPackingList: (api.lines?.length ?? 0) > 0,
    createdBy: api.created_by_name || "—",
  };
}

function resolveOdooPoId(po: PurchaseOrder): number | null {
  if (po.odooId != null && Number.isFinite(po.odooId)) return po.odooId;
  if (/^\d+$/.test(String(po.id).trim())) return parseInt(String(po.id), 10);
  return null;
}

function buildLocalPackingShareText(po: PurchaseOrder): string {
  const lines: string[] = [
    "Packing List (local / preview)",
    `PO: ${po.id}`,
  ];
  if (po.supplierName) lines.push(`Vendor: ${po.supplierName}`);
  lines.push("", "#\tItem\tSize\tQty\tCBM\tWeight (kg)");
  po.items.forEach((item, i) => {
    lines.push(
      `${i + 1}\t${item.name}\t${item.size}\t${item.qty}\t${item.cbm ?? "—"}\t${item.weight ?? "—"}`,
    );
  });
  return lines.join("\n");
}

export type SCPurchaseOrdersProps = {
  /** Live rows from `/api/crm/supply/po/list`. When omitted, demo data is used. */
  apiPos?: ApiSupplyPo[];
};

export function SCPurchaseOrders({ apiPos }: SCPurchaseOrdersProps = {}) {
  const purchaseOrders = useMemo(
    () => (apiPos !== undefined ? apiPos.map(mapApiSupplyPoToPurchaseOrder) : demoPurchaseOrders),
    [apiPos],
  );

  const [subTab, setSubTab] = useState<SubTab>("all");
  const [divisionFilter, setDivisionFilter] = useState<"all" | Division>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPO, setSelectedPO] = useState<PurchaseOrder | null>(null);
  const [showPackingList, setShowPackingList] = useState(false);
  const [showCreatePO, setShowCreatePO] = useState(false);
  const [expandedSuggested, setExpandedSuggested] = useState<string | null>(null);
  const [packingBusy, setPackingBusy] = useState<false | "share" | "pdf">(false);

  const runPackingShare = async (poArg?: PurchaseOrder) => {
    const po = poArg ?? selectedPO;
    if (!po) return;
    const oid = resolveOdooPoId(po);
    setPackingBusy("share");
    try {
      let title = `Packing List — ${po.id}`;
      let text: string;
      if (oid != null) {
        const res = await supplyService.getPackingListShare(oid);
        if (!res.success || !res.data) {
          toast.error(res.error ?? "تعذر تحميل نص المشاركة");
          return;
        }
        title = res.data.title || title;
        text = res.data.text || "";
      } else {
        text = buildLocalPackingShareText(po);
        toast.message("معاينة محلية — سجّل الدخول واختر أمراً من الخادم لمشاركة بيانات Odoo");
      }
      const url = typeof window !== "undefined" ? window.location.href : "";
      if (typeof navigator !== "undefined" && navigator.share) {
        try {
          await navigator.share({ title, text, url });
        } catch (err) {
          if ((err as Error).name === "AbortError") return;
          try {
            await navigator.clipboard.writeText(`${title}\n\n${text}`);
            toast.success("تم نسخ قائمة التعبئة");
          } catch {
            toast.error("تعذر المشاركة أو النسخ");
          }
        }
      } else {
        try {
          await navigator.clipboard.writeText(`${title}\n\n${text}`);
          toast.success("تم نسخ قائمة التعبئة");
        } catch {
          toast.error("المتصفح لا يدعم الحافظة");
        }
      }
    } finally {
      setPackingBusy(false);
    }
  };

  const runPackingPdf = async (poArg?: PurchaseOrder) => {
    const po = poArg ?? selectedPO;
    if (!po) return;
    const oid = resolveOdooPoId(po);
    if (oid == null) {
      toast.error(
        "تنزيل PDF يتطلب ربط الأمر بسجل Odoo (معرّف رقمي). استخدم أوامر الشراء المحمّلة من الخادم.",
      );
      return;
    }
    setPackingBusy("pdf");
    try {
      const res = await supplyService.getPackingListPdf(oid);
      if (!res.success || !res.data) {
        toast.error(res.error ?? "تعذر إنشاء PDF");
        return;
      }
      const { filename, pdf_base64 } = res.data;
      const bytes = Uint8Array.from(atob(pdf_base64), (c) => c.charCodeAt(0));
      const blob = new Blob([bytes], { type: "application/pdf" });
      const a = document.createElement("a");
      const href = URL.createObjectURL(blob);
      a.href = href;
      a.download = filename || `PackingList-${oid}.pdf`;
      a.click();
      URL.revokeObjectURL(href);
      toast.success("تم تنزيل PDF");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "فشل تنزيل PDF");
    } finally {
      setPackingBusy(false);
    }
  };

  const filteredPOs = purchaseOrders.filter((po) => {
    if (divisionFilter !== "all" && po.division !== divisionFilter) return false;
    if (subTab === "open" && !["draft", "sent", "confirmed"].includes(po.status)) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const idHit =
        po.id.toLowerCase().includes(q) ||
        (po.odooId != null && String(po.odooId).includes(searchQuery.trim()));
      return idHit || po.supplierName.includes(searchQuery);
    }
    return true;
  });

  const subTabs = [
    { id: "all" as SubTab, label: "جميع الأوامر", count: purchaseOrders.length },
    { id: "open" as SubTab, label: "أوامر مفتوحة", count: purchaseOrders.filter((p) => ["draft", "sent", "confirmed"].includes(p.status)).length },
    { id: "suggested" as SubTab, label: "أوامر مقترحة", count: suggestedPOs.length },
    { id: "packing" as SubTab, label: "قوائم التعبئة", count: purchaseOrders.filter((p) => p.hasPackingList).length },
  ];

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex gap-1.5">
          {subTabs.map((t) => (
            <Button
              key={t.id}
              variant={subTab === t.id ? "default" : "outline"}
              size="sm"
              className="text-xs gap-1"
              onClick={() => setSubTab(t.id)}
            >
              {t.label}
              <span className={`text-[9px] px-1.5 rounded-full ${
                subTab === t.id ? "bg-primary-foreground/20 text-primary-foreground" : "bg-muted text-muted-foreground"
              }`}>{t.count}</span>
            </Button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {/* Division Filter */}
          <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40">
            {([
              { key: "all", label: "الكل" },
              { key: "europe", label: "أوروبا" },
              { key: "china", label: "الصين" },
            ] as const).map((d) => (
              <button
                key={d.key}
                onClick={() => setDivisionFilter(d.key)}
                className={`px-2.5 py-1 rounded text-[10px] transition-all ${
                  divisionFilter === d.key
                    ? "bg-card text-primary shadow-sm border border-primary/20"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
          <div className="relative">
            <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              placeholder="بحث..."
              className="h-8 text-xs ps-8 w-40"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button size="sm" className="text-xs gap-1.5" onClick={() => setShowCreatePO(true)}>
            <Plus className="w-3.5 h-3.5" />
            أمر شراء جديد
          </Button>
        </div>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {(subTab === "all" || subTab === "open") && (
          <motion.div
            key="po-list"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-start">رقم الأمر</TableHead>
                      <TableHead className="text-start">المورد</TableHead>
                      <TableHead className="text-start">القسم</TableHead>
                      <TableHead className="text-start">الحالة</TableHead>
                      <TableHead className="text-end">المبلغ</TableHead>
                      <TableHead className="text-start">التاريخ</TableHead>
                      <TableHead className="text-start">الحاوية</TableHead>
                      <TableHead className="text-center">إجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredPOs.map((po) => {
                      const conf = poStatusConfig[po.status];
                      return (
                        <TableRow
                          key={`${po.odooId ?? "demo"}-${po.id}`}
                          className="cursor-pointer hover:bg-muted/30"
                          onClick={() => setSelectedPO(po)}
                        >
                          <TableCell className="text-start">
                            <span className="text-xs text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{po.id}</span>
                          </TableCell>
                          <TableCell className="text-start text-xs">{po.supplierName}</TableCell>
                          <TableCell className="text-start">
                            <Badge variant="outline" className="text-[9px]">
                              {po.division === "europe" ? "أوروبا" : "الصين"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-start">
                            <Badge className={`text-[9px] border-transparent ${conf.color}`}>{conf.label}</Badge>
                          </TableCell>
                          <TableCell className="text-end">
                            <span className="text-xs" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                              {currencySymbols[po.currency]} {fmt(po.totalAmount)}
                            </span>
                          </TableCell>
                          <TableCell className="text-start text-[10px] text-muted-foreground">{po.createdAt}</TableCell>
                          <TableCell className="text-start">
                            {po.containerNumber ? (
                              <span className="text-[10px] text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                                {po.containerNumber}
                              </span>
                            ) : (
                              <span className="text-[10px] text-muted-foreground">—</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex items-center justify-center gap-1">
                              <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={(e) => { e.stopPropagation(); setSelectedPO(po); }}>
                                <Eye className="w-3 h-3" />
                              </Button>
                              {po.hasPackingList && (
                                <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={(e) => { e.stopPropagation(); setSelectedPO(po); setShowPackingList(true); }}>
                                  <PackageOpen className="w-3 h-3 text-primary" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {subTab === "suggested" && (
          <motion.div
            key="suggested"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            <Card className="border-primary/20 bg-primary/5">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-primary/15 flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-foreground">أوامر شراء مقترحة بناءً على تحليل المبيعات</p>
                    <p className="text-[10px] text-muted-foreground mt-1">
                      المعادلة: (متوسط مبيعات أعلى 6 أشهر سنوياً) ÷ المخزون المتاح = الكمية المقترحة
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {suggestedPOs.map((spo) => {
              const ratio = spo.currentStock / (spo.avgTop6MonthsSales / 6);
              const urgency = ratio < 1 ? "urgent" : ratio < 2 ? "warning" : "ok";
              const isExpanded = expandedSuggested === spo.id;
              return (
                <Card key={spo.id} className={`border-border/50 ${urgency === "urgent" ? "border-red-500/30" : ""}`}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                        urgency === "urgent" ? "bg-red-500/15" : urgency === "warning" ? "bg-primary/15" : "bg-emerald-500/15"
                      }`}>
                        {urgency === "urgent" ? (
                          <AlertTriangle className="w-4 h-4 text-red-500" />
                        ) : urgency === "warning" ? (
                          <TriangleAlert className="w-4 h-4 text-primary" />
                        ) : (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-foreground">{spo.itemName}</p>
                        <div className="flex items-center gap-3 text-[10px] text-muted-foreground mt-0.5">
                          <span>المورد: {spo.supplierName}</span>
                          <Badge variant="outline" className="text-[8px] h-4">{spo.category === "glass" ? "زجاجيات" : spo.category === "perfume" ? "عطور" : spo.category === "alcohol" ? "كحول" : "ألمنيوم"}</Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 shrink-0">
                        <div className="text-center">
                          <p className={`text-xs ${urgency === "urgent" ? "text-red-500" : urgency === "warning" ? "text-primary" : "text-emerald-500"}`}>{fmt(spo.currentStock)}</p>
                          <p className="text-[8px] text-muted-foreground">المخزون</p>
                        </div>
                        <div className="w-px h-7 bg-border/40" />
                        <div className="text-center">
                          <p className="text-xs text-foreground">{fmt(spo.suggestedQty)}</p>
                          <p className="text-[8px] text-muted-foreground">مقترح</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => setExpandedSuggested(isExpanded ? null : spo.id)}
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </Button>
                      </div>
                    </div>

                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 pt-3 border-t border-border/30 grid grid-cols-4 gap-3">
                            <div className="p-2 rounded-lg bg-muted/30 text-center">
                              <p className="text-[10px] text-muted-foreground">متوسط سنوي</p>
                              <p className="text-xs text-foreground mt-0.5">{fmt(spo.avgAnnualSales)}</p>
                            </div>
                            <div className="p-2 rounded-lg bg-muted/30 text-center">
                              <p className="text-[10px] text-muted-foreground">أعلى 6 أشهر</p>
                              <p className="text-xs text-foreground mt-0.5">{fmt(spo.avgTop6MonthsSales)}</p>
                            </div>
                            <div className="p-2 rounded-lg bg-muted/30 text-center">
                              <p className="text-[10px] text-muted-foreground">آخر سعر</p>
                              <p className="text-xs text-foreground mt-0.5">{fmt(spo.lastPrice)}</p>
                            </div>
                            <div className="p-2 rounded-lg bg-muted/30 text-center">
                              <p className="text-[10px] text-muted-foreground">تكفي لـ</p>
                              <p className="text-xs text-foreground mt-0.5">{ratio.toFixed(1)} شهر</p>
                            </div>
                          </div>
                          <div className="mt-3 flex justify-end">
                            <Button size="sm" className="text-xs gap-1.5">
                              <Plus className="w-3 h-3" />
                              إنشاء أمر شراء
                            </Button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </CardContent>
                </Card>
              );
            })}
          </motion.div>
        )}

        {subTab === "packing" && (
          <motion.div
            key="packing"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {purchaseOrders.filter((p) => p.hasPackingList).map((po) => (
              <Card key={`${po.odooId ?? "demo"}-${po.id}`} className="border-border/50">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <PackageOpen className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm text-foreground">قائمة تعبئة — <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{po.id}</span></p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{po.supplierName} • {po.items.length} أصناف</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="text-[10px] h-7 gap-1"
                        disabled={!!packingBusy}
                        onClick={() => void runPackingShare(po)}
                      >
                        {packingBusy === "share" ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Share2 className="w-3 h-3" />
                        )}
                        مشاركة
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="text-[10px] h-7 gap-1"
                        disabled={!!packingBusy}
                        onClick={() => void runPackingPdf(po)}
                      >
                        {packingBusy === "pdf" ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Download className="w-3 h-3" />
                        )}
                        تحميل
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => { setSelectedPO(po); setShowPackingList(true); }}>
                        <Eye className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                  {/* Packing summary */}
                  <div className="mt-3 grid grid-cols-4 gap-2">
                    <div className="p-2 rounded bg-muted/30 text-center">
                      <p className="text-[9px] text-muted-foreground">الأصناف</p>
                      <p className="text-xs text-foreground">{po.items.length}</p>
                    </div>
                    <div className="p-2 rounded bg-muted/30 text-center">
                      <p className="text-[9px] text-muted-foreground">إجمالي الكمية</p>
                      <p className="text-xs text-foreground">{fmt(po.items.reduce((s, i) => s + i.qty, 0))}</p>
                    </div>
                    <div className="p-2 rounded bg-muted/30 text-center">
                      <p className="text-[9px] text-muted-foreground">CBM</p>
                      <p className="text-xs text-foreground">{po.items.reduce((s, i) => s + (i.cbm || 0), 0).toFixed(1)}</p>
                    </div>
                    <div className="p-2 rounded bg-muted/30 text-center">
                      <p className="text-[9px] text-muted-foreground">الوزن (كغ)</p>
                      <p className="text-xs text-foreground">{fmt(po.items.reduce((s, i) => s + (i.weight || 0), 0))}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── PO Detail Dialog ── */}
      <Dialog open={!!selectedPO && !showPackingList} onOpenChange={(open) => { if (!open) setSelectedPO(null); }}>
        <DialogContent className="!max-w-3xl !p-0 !gap-0">
          <DialogTitle className="sr-only">تفاصيل أمر الشراء</DialogTitle>
          <DialogDescription className="sr-only">عرض تفاصيل أمر الشراء والأصناف</DialogDescription>
          {selectedPO && (
            <div>
              {/* Header */}
              <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedPO.id}</h3>
                      <Badge className={`text-[9px] border-transparent ${poStatusConfig[selectedPO.status].color}`}>
                        {poStatusConfig[selectedPO.status].label}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{selectedPO.supplierName} • {selectedPO.division === "europe" ? "أوروبا" : "الصين"}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" className="text-[10px] h-7 gap-1">
                      <Upload className="w-3 h-3" />
                      استيراد Excel
                    </Button>
                    <Button variant="outline" size="sm" className="text-[10px] h-7 gap-1" onClick={() => setShowPackingList(true)}>
                      <PackageOpen className="w-3 h-3" />
                      قائمة التعبئة
                    </Button>
                  </div>
                </div>
              </div>
              {/* Items Table */}
              <ScrollArea className="max-h-[60vh]" dir="rtl">
                <div className="p-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-start">الصنف</TableHead>
                        <TableHead className="text-start">الحجم</TableHead>
                        <TableHead className="text-center">الكمية</TableHead>
                        <TableHead className="text-end">السعر</TableHead>
                        <TableHead className="text-end">السعر السابق</TableHead>
                        <TableHead className="text-end">الإجمالي</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedPO.items.map((item) => {
                        const priceDiff = item.previousPrice
                          ? item.unitPrice - item.previousPrice
                          : 0;
                        const priceColor = priceDiff > 0 ? "text-red-500" : priceDiff < 0 ? "text-primary" : "text-emerald-500";
                        return (
                          <TableRow key={item.id}>
                            <TableCell className="text-start text-xs">{item.name}</TableCell>
                            <TableCell className="text-start text-xs text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{item.size}</TableCell>
                            <TableCell className="text-center text-xs">{fmt(item.qty)}</TableCell>
                            <TableCell className="text-end text-xs">
                              <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{currencySymbols[selectedPO.currency]} {item.unitPrice.toFixed(2)}</span>
                            </TableCell>
                            <TableCell className="text-end">
                              {item.previousPrice ? (
                                <span className={`text-xs ${priceColor}`} style={{ direction: "ltr", unicodeBidi: "embed" }}>
                                  {currencySymbols[selectedPO.currency]} {item.previousPrice.toFixed(2)}
                                  {priceDiff > 0 ? " ▲" : priceDiff < 0 ? " ▼" : " ="}
                                </span>
                              ) : (
                                <span className="text-xs text-muted-foreground">—</span>
                              )}
                            </TableCell>
                            <TableCell className="text-end text-xs">
                              <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{currencySymbols[selectedPO.currency]} {fmt(item.unitPrice * item.qty)}</span>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                  {/* Totals */}
                  <div className="mt-4 pt-3 border-t border-border/30 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {selectedPO.containerNumber && (
                        <div className="text-xs">
                          <span className="text-muted-foreground">الحاوية: </span>
                          <a
                            href={`https://www.searates.com/container/tracking/?number=${selectedPO.containerNumber}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline"
                            style={{ direction: "ltr", unicodeBidi: "embed" }}
                          >
                            {selectedPO.containerNumber}
                          </a>
                        </div>
                      )}
                      <span className="text-[10px] text-muted-foreground">بواسطة: {selectedPO.createdBy}</span>
                    </div>
                    <div className="text-end">
                      <p className="text-[10px] text-muted-foreground">الإجمالي</p>
                      <p className="text-lg text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {currencySymbols[selectedPO.currency]} {fmt(selectedPO.totalAmount)}
                      </p>
                    </div>
                  </div>
                  {/* Notes */}
                  {selectedPO.notes && (
                    <div className="mt-3 p-3 rounded-lg bg-muted/30 text-xs text-muted-foreground">
                      {selectedPO.notes}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Packing List Dialog ── */}
      <Dialog
        open={showPackingList && !!selectedPO}
        onOpenChange={(open) => {
          if (!open) {
            setShowPackingList(false);
            setPackingBusy(false);
          }
        }}
      >
        <DialogContent className="!max-w-2xl !p-0 !gap-0">
          <DialogTitle className="sr-only">قائمة التعبئة</DialogTitle>
          <DialogDescription className="sr-only">قائمة التعبئة بدون أسعار</DialogDescription>
          {selectedPO && (
            <div>
              <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <PackageOpen className="w-5 h-5 text-primary" />
                    <div>
                      <h3 className="text-sm text-foreground">قائمة التعبئة (Packing List)</h3>
                      <p className="text-[10px] text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedPO.id}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="text-[10px] h-7 gap-1"
                      disabled={!!packingBusy}
                      onClick={() => void runPackingShare()}
                    >
                      {packingBusy === "share" ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Share2 className="w-3 h-3" />
                      )}
                      مشاركة
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="text-[10px] h-7 gap-1"
                      disabled={!!packingBusy}
                      onClick={() => void runPackingPdf()}
                    >
                      {packingBusy === "pdf" ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Download className="w-3 h-3" />
                      )}
                      PDF
                    </Button>
                  </div>
                </div>
              </div>
              <ScrollArea className="max-h-[60vh]" dir="rtl">
                <div className="p-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-start">#</TableHead>
                        <TableHead className="text-start">الصنف</TableHead>
                        <TableHead className="text-start">الحجم</TableHead>
                        <TableHead className="text-center">الكمية</TableHead>
                        <TableHead className="text-end">CBM</TableHead>
                        <TableHead className="text-end">الوزن (كغ)</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedPO.items.map((item, idx) => (
                        <TableRow key={item.id}>
                          <TableCell className="text-start text-xs text-muted-foreground">{idx + 1}</TableCell>
                          <TableCell className="text-start text-xs">{item.name}</TableCell>
                          <TableCell className="text-start text-xs text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{item.size}</TableCell>
                          <TableCell className="text-center text-xs">{fmt(item.qty)}</TableCell>
                          <TableCell className="text-end text-xs">{item.cbm?.toFixed(2) || "—"}</TableCell>
                          <TableCell className="text-end text-xs">{item.weight ? fmt(item.weight) : "—"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <div className="mt-4 pt-3 border-t border-border/30 grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-muted/30 text-center">
                      <p className="text-[10px] text-muted-foreground">إجمالي الكمية</p>
                      <p className="text-sm text-foreground">{fmt(selectedPO.items.reduce((s, i) => s + i.qty, 0))}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/30 text-center">
                      <p className="text-[10px] text-muted-foreground">إجمالي CBM</p>
                      <p className="text-sm text-foreground">{selectedPO.items.reduce((s, i) => s + (i.cbm || 0), 0).toFixed(2)}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/30 text-center">
                      <p className="text-[10px] text-muted-foreground">إجمالي الوزن</p>
                      <p className="text-sm text-foreground">{fmt(selectedPO.items.reduce((s, i) => s + (i.weight || 0), 0))} كغ</p>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Create PO Dialog ── */}
      <Dialog open={showCreatePO} onOpenChange={setShowCreatePO}>
        <DialogContent className="!max-w-3xl !p-0 !gap-0">
          <DialogTitle className="sr-only">إنشاء أمر شراء جديد</DialogTitle>
          <DialogDescription className="sr-only">نموذج إنشاء أمر شراء</DialogDescription>
          <div>
            <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Plus className="w-5 h-5 text-primary" />
                  <h3 className="text-sm text-foreground">إنشاء أمر شراء جديد</h3>
                </div>
                <Button variant="outline" size="sm" className="text-[10px] h-7 gap-1">
                  <Upload className="w-3 h-3" />
                  استيراد من Excel
                </Button>
              </div>
            </div>
            <ScrollArea className="max-h-[70vh]" dir="rtl">
              <div className="p-5 space-y-4">
                {/* Form Fields */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs text-muted-foreground">المورد</label>
                    <select className="w-full h-9 rounded-md border border-input bg-input-background px-3 text-xs text-foreground">
                      <option value="">اختر المورد</option>
                      {suppliers.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs text-muted-foreground">القسم</label>
                    <select className="w-full h-9 rounded-md border border-input bg-input-background px-3 text-xs text-foreground">
                      <option value="europe">أوروبا</option>
                      <option value="china">الصين</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs text-muted-foreground">العملة</label>
                    <select className="w-full h-9 rounded-md border border-input bg-input-background px-3 text-xs text-foreground">
                      <option value="USD">دولار أمريكي (USD)</option>
                      <option value="EUR">يورو (EUR)</option>
                      <option value="CNY">يوان صيني (CNY)</option>
                      <option value="SAR">ريال سعودي (SAR)</option>
                      <option value="IQD">دينار عراقي (IQD)</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs text-muted-foreground">رقم الحاوية (اختياري)</label>
                    <Input className="h-9 text-xs" placeholder="XXXX0000000" style={{ direction: "ltr" }} />
                  </div>
                  <div className="space-y-1.5 col-span-2">
                    <label className="text-xs text-muted-foreground">ملاحظات</label>
                    <textarea className="w-full h-20 rounded-md border border-input bg-input-background px-3 py-2 text-xs text-foreground resize-none" placeholder="ملاحظات إضافية..." />
                  </div>
                </div>

                {/* Items */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-muted-foreground">الأصناف</label>
                    <Button variant="outline" size="sm" className="text-[10px] h-6 gap-1">
                      <Plus className="w-3 h-3" />
                      إضافة صنف
                    </Button>
                  </div>
                  <div className="border border-border/40 rounded-lg p-3 text-center text-xs text-muted-foreground">
                    اضغط "إضافة صنف" أو استورد من Excel لبدء إضافة الأصناف
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-border/30">
                  <Button variant="outline" size="sm" className="text-xs" onClick={() => setShowCreatePO(false)}>إلغاء</Button>
                  <Button size="sm" className="text-xs gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    حفظ أمر الشراء
                  </Button>
                </div>
              </div>
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}