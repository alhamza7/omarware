// ═══════════════════════════════════════════════════════════
//  Sales Pipeline & Attribution
//  Funnel stages, deal tracking, sales attribution logic
// ═══════════════════════════════════════════════════════════

import { useState, useMemo } from "react";
import { motion } from "motion/react";
import {
  TrendingUp, DollarSign, User, Users, Target, BarChart3,
  Calendar, Phone, MessageCircle, ArrowLeftRight, Plus,
  ChevronDown, Star, Zap, Eye, Filter, Search, Clock,
  Hash, Check, X, AlertTriangle,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";

// ── Types ───────────────────────────────────────────────

type PipelineStage = "lead" | "qualified" | "proposal" | "negotiation" | "won" | "lost";
type DealSource = "whatsapp" | "instagram" | "tiktok" | "email" | "phone" | "walk-in" | "referral" | "website";
type AttributionModel = "first_touch" | "last_touch" | "linear" | "time_decay";

interface Deal {
  id: string;
  title: string;
  customerId: string;
  customerName: string;
  value: number;
  currency: string;
  stage: PipelineStage;
  probability: number;
  source: DealSource;
  assignedAgent: string;
  createdAt: string;
  updatedAt: string;
  expectedClose?: string;
  touchpoints: Touchpoint[];
  isVip: boolean;
  notes?: string;
}

interface Touchpoint {
  channel: DealSource;
  timestamp: string;
  agent: string;
  action: string;
  contribution: number; // percentage attribution
}

interface StageConfig {
  id: PipelineStage;
  label: string;
  color: string;
  bgColor: string;
  probability: number;
}

// ── Config ──────────────────────────────────────────────

const stageConfigs: StageConfig[] = [
  { id: "lead", label: "عميل محتمل", color: "text-blue-400", bgColor: "bg-blue-500/10 border-blue-500/20", probability: 10 },
  { id: "qualified", label: "مؤهل", color: "text-cyan-400", bgColor: "bg-cyan-500/10 border-cyan-500/20", probability: 30 },
  { id: "proposal", label: "عرض سعر", color: "text-violet-400", bgColor: "bg-violet-500/10 border-violet-500/20", probability: 50 },
  { id: "negotiation", label: "مفاوضة", color: "text-primary", bgColor: "bg-primary/10 border-primary/20", probability: 75 },
  { id: "won", label: "مكسب", color: "text-emerald-400", bgColor: "bg-emerald-500/10 border-emerald-500/20", probability: 100 },
  { id: "lost", label: "خسارة", color: "text-red-400", bgColor: "bg-red-500/10 border-red-500/20", probability: 0 },
];

const sourceLabels: Record<DealSource, string> = {
  whatsapp: "واتساب", instagram: "إنستقرام", tiktok: "تيك توك",
  email: "بريد", phone: "هاتف", "walk-in": "زيارة", referral: "إحالة", website: "موقع",
};

const attributionModelLabels: Record<AttributionModel, string> = {
  first_touch: "أول تواصل", last_touch: "آخر تواصل", linear: "خطي متساوي", time_decay: "اضمحلال زمني",
};

// ── Mock Data ───────────────────────────────────────────

const mockDeals: Deal[] = [
  {
    id: "deal-01", title: "طلب عطور مجموعة VIP", customerId: "C-001", customerName: "أحمد محمد العلي",
    value: 4500, currency: "USD", stage: "negotiation", probability: 75, source: "whatsapp",
    assignedAgent: "سعود المالكي", createdAt: "2026-02-10", updatedAt: "2026-02-22", expectedClose: "2026-02-28",
    isVip: true,
    touchpoints: [
      { channel: "whatsapp", timestamp: "2026-02-10", agent: "سعود المالكي", action: "محادثة أولى", contribution: 40 },
      { channel: "phone", timestamp: "2026-02-15", agent: "سعود المالكي", action: "مكالمة متابعة", contribution: 30 },
      { channel: "email", timestamp: "2026-02-20", agent: "سعود المالكي", action: "إرسال عرض سعر", contribution: 30 },
    ],
  },
  {
    id: "deal-02", title: "صفقة أجهزة عطور للمكاتب", customerId: "C-003", customerName: "خالد سعد القحطاني",
    value: 12000, currency: "USD", stage: "proposal", probability: 50, source: "email",
    assignedAgent: "فارس العنزي", createdAt: "2026-02-05", updatedAt: "2026-02-21", expectedClose: "2026-03-10",
    isVip: true,
    touchpoints: [
      { channel: "email", timestamp: "2026-02-05", agent: "فارس العنزي", action: "استفسار وارد", contribution: 20 },
      { channel: "phone", timestamp: "2026-02-08", agent: "فارس العنزي", action: "عرض تفصيلي", contribution: 40 },
      { channel: "whatsapp", timestamp: "2026-02-18", agent: "سعود المالكي", action: "إرسال كتالوج", contribution: 40 },
    ],
  },
  {
    id: "deal-03", title: "طلب عينات تعريفية", customerId: "C-006", customerName: "سارة علي الحربي",
    value: 350, currency: "USD", stage: "qualified", probability: 30, source: "instagram",
    assignedAgent: "عبدالله الحربي", createdAt: "2026-02-18", updatedAt: "2026-02-22",
    isVip: false,
    touchpoints: [
      { channel: "instagram", timestamp: "2026-02-18", agent: "عبدالله الحربي", action: "DM على إنستقرام", contribution: 60 },
      { channel: "whatsapp", timestamp: "2026-02-20", agent: "منى الشهري", action: "متابعة واتساب", contribution: 40 },
    ],
  },
  {
    id: "deal-04", title: "عميل تيك توك — عطور نسائية", customerId: "", customerName: "user_tiktok_392",
    value: 200, currency: "USD", stage: "lead", probability: 10, source: "tiktok",
    assignedAgent: "عبدالله الحربي", createdAt: "2026-02-23", updatedAt: "2026-02-23",
    isVip: false,
    touchpoints: [
      { channel: "tiktok", timestamp: "2026-02-23", agent: "عبدالله الحربي", action: "رسالة من تيك توك", contribution: 100 },
    ],
  },
  {
    id: "deal-05", title: "طلب بخور فاخر بالجملة", customerId: "C-002", customerName: "فاطمة عبدالله السالم",
    value: 2800, currency: "USD", stage: "won", probability: 100, source: "whatsapp",
    assignedAgent: "منى الشهري", createdAt: "2026-01-28", updatedAt: "2026-02-15",
    isVip: false,
    touchpoints: [
      { channel: "whatsapp", timestamp: "2026-01-28", agent: "منى الشهري", action: "استفسار أول", contribution: 30 },
      { channel: "phone", timestamp: "2026-02-02", agent: "منى الشهري", action: "عرض أسعار", contribution: 25 },
      { channel: "walk-in", timestamp: "2026-02-10", agent: "سعود المالكي", action: "زيارة المعرض", contribution: 25 },
      { channel: "whatsapp", timestamp: "2026-02-15", agent: "منى الشهري", action: "تأكيد الطلب", contribution: 20 },
    ],
  },
  {
    id: "deal-06", title: "طلب زيوت مخصصة", customerId: "C-004", customerName: "نورة بدر المالكي",
    value: 650, currency: "USD", stage: "lost", probability: 0, source: "whatsapp",
    assignedAgent: "منى الشهري", createdAt: "2026-02-01", updatedAt: "2026-02-20",
    isVip: false, notes: "العميل فضّل مورد آخر بسبب السعر",
    touchpoints: [
      { channel: "whatsapp", timestamp: "2026-02-01", agent: "منى الشهري", action: "استفسار", contribution: 50 },
      { channel: "phone", timestamp: "2026-02-10", agent: "منى الشهري", action: "مفاوضة سعر", contribution: 50 },
    ],
  },
  {
    id: "deal-07", title: "مجموعة هدايا رمضان", customerId: "C-001", customerName: "أحمد محمد العلي",
    value: 8500, currency: "USD", stage: "qualified", probability: 30, source: "phone",
    assignedAgent: "سعود المالكي", createdAt: "2026-02-20", updatedAt: "2026-02-23", expectedClose: "2026-03-15",
    isVip: true,
    touchpoints: [
      { channel: "phone", timestamp: "2026-02-20", agent: "سعود المالكي", action: "مكالمة عرض", contribution: 70 },
      { channel: "email", timestamp: "2026-02-23", agent: "سعود المالكي", action: "إرسال التفاصيل", contribution: 30 },
    ],
  },
];

// ── Main Component ──────────────────────────────────────

export function SalesPipeline() {
  const [activeTab, setActiveTab] = useState<"kanban" | "attribution" | "funnel">("kanban");
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [attributionModel, setAttributionModel] = useState<AttributionModel>("first_touch");

  const pipelineStages: PipelineStage[] = ["lead", "qualified", "proposal", "negotiation", "won"];

  const stageStats = useMemo(() => {
    return pipelineStages.map((stageId) => {
      const deals = mockDeals.filter((d) => d.stage === stageId);
      const totalValue = deals.reduce((s, d) => s + d.value, 0);
      const weighted = deals.reduce((s, d) => s + d.value * (d.probability / 100), 0);
      return { stageId, deals, totalValue, weighted, count: deals.length };
    });
  }, []);

  const totalPipelineValue = mockDeals.filter((d) => d.stage !== "lost").reduce((s, d) => s + d.value, 0);
  const totalWeighted = mockDeals.filter((d) => d.stage !== "lost").reduce((s, d) => s + d.value * (d.probability / 100), 0);
  const wonDeals = mockDeals.filter((d) => d.stage === "won");
  const wonValue = wonDeals.reduce((s, d) => s + d.value, 0);
  const lostValue = mockDeals.filter((d) => d.stage === "lost").reduce((s, d) => s + d.value, 0);
  const conversionRate = mockDeals.length > 0 ? Math.round((wonDeals.length / mockDeals.length) * 100) : 0;

  // Attribution analysis
  const attributionByChannel = useMemo(() => {
    const channels: Record<string, { deals: number; revenue: number; contribution: number }> = {};
    mockDeals.filter((d) => d.stage === "won").forEach((deal) => {
      deal.touchpoints.forEach((tp) => {
        if (!channels[tp.channel]) channels[tp.channel] = { deals: 0, revenue: 0, contribution: 0 };
        // Different attribution models
        let attrValue = 0;
        if (attributionModel === "first_touch") {
          attrValue = tp === deal.touchpoints[0] ? deal.value : 0;
        } else if (attributionModel === "last_touch") {
          attrValue = tp === deal.touchpoints[deal.touchpoints.length - 1] ? deal.value : 0;
        } else if (attributionModel === "linear") {
          attrValue = deal.value / deal.touchpoints.length;
        } else {
          attrValue = deal.value * (tp.contribution / 100);
        }
        channels[tp.channel].revenue += attrValue;
        channels[tp.channel].contribution += tp.contribution;
        if (tp === deal.touchpoints[0]) channels[tp.channel].deals += 1;
      });
    });
    return Object.entries(channels).sort((a, b) => b[1].revenue - a[1].revenue);
  }, [attributionModel]);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">

        {/* ── KPIs ── */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: "إجمالي الأنبوب", value: `$${totalPipelineValue.toLocaleString()}`, color: "text-foreground" },
            { label: "القيمة المرجحة", value: `$${totalWeighted.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: "text-primary" },
            { label: "صفقات مكسبة", value: `$${wonValue.toLocaleString()}`, color: "text-emerald-400" },
            { label: "صفقات خاسرة", value: `$${lostValue.toLocaleString()}`, color: "text-red-400" },
            { label: "معدل التحويل", value: `${conversionRate}%`, color: "text-primary" },
          ].map((kpi) => (
            <div key={kpi.label} className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
              <p className={`text-2xl ${kpi.color}`}>{kpi.value}</p>
              <p className="text-[9px] text-muted-foreground mt-0.5">{kpi.label}</p>
            </div>
          ))}
        </div>

        {/* ── Tabs ── */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <div className="flex items-center justify-between">
            <TabsList className="bg-muted/20">
              <TabsTrigger value="kanban" className="text-xs gap-1.5">
                <Target className="w-3.5 h-3.5" />
                خط الأنابيب
              </TabsTrigger>
              <TabsTrigger value="attribution" className="text-xs gap-1.5">
                <TrendingUp className="w-3.5 h-3.5" />
                الإسناد
              </TabsTrigger>
              <TabsTrigger value="funnel" className="text-xs gap-1.5">
                <BarChart3 className="w-3.5 h-3.5" />
                القمع
              </TabsTrigger>
            </TabsList>
            <Button size="sm" className="h-8 text-xs gap-1.5">
              <Plus className="w-3.5 h-3.5" />
              صفقة جديدة
            </Button>
          </div>

          {/* ═══ Kanban Pipeline ═══ */}
          <TabsContent value="kanban" className="mt-4">
            <ScrollArea dir="rtl" className="w-full">
              <div className="flex gap-3 min-w-[1000px] pb-2">
                {stageStats.map((stage) => {
                  const config = stageConfigs.find((s) => s.id === stage.stageId)!;
                  return (
                    <div key={stage.stageId} className="flex-1 min-w-[200px]">
                      <div className={`p-2 rounded-t-xl border ${config.bgColor}`}>
                        <div className="flex items-center justify-between">
                          <span className={`text-xs ${config.color}`}>{config.label}</span>
                          <Badge className={`${config.bgColor} ${config.color} text-[8px] h-4`}>
                            {stage.count}
                          </Badge>
                        </div>
                        <p className="text-[9px] text-muted-foreground mt-0.5" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                          ${stage.totalValue.toLocaleString()}
                        </p>
                      </div>
                      <div className="space-y-2 p-2 rounded-b-xl border border-t-0 border-border/20 bg-card/20 min-h-[200px]">
                        {stage.deals.map((deal) => (
                          <motion.button
                            key={deal.id}
                            className="w-full text-start p-3 rounded-lg border border-border/30 bg-card/40 hover:border-primary/30 transition-all space-y-2"
                            whileTap={{ scale: 0.98 }}
                            onClick={() => setSelectedDeal(deal)}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] text-foreground line-clamp-1">{deal.title}</span>
                              {deal.isVip && <Star className="w-3 h-3 text-primary fill-primary shrink-0" />}
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Avatar className="h-5 w-5">
                                <AvatarFallback className="text-[7px] bg-primary/10 text-primary">
                                  {deal.customerName.slice(0, 2)}
                                </AvatarFallback>
                              </Avatar>
                              <span className="text-[9px] text-muted-foreground">{deal.customerName}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                                ${deal.value.toLocaleString()}
                              </span>
                              <span className="text-[8px] text-muted-foreground">{sourceLabels[deal.source]}</span>
                            </div>
                            {deal.expectedClose && (
                              <p className="text-[8px] text-muted-foreground flex items-center gap-0.5">
                                <Calendar className="w-2.5 h-2.5" />
                                {new Date(deal.expectedClose).toLocaleDateString("ar-SA", { month: "short", day: "numeric" })}
                              </p>
                            )}
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* ═══ Attribution ═══ */}
          <TabsContent value="attribution" className="mt-4 space-y-4">
            {/* Model selector */}
            <div className="flex items-center gap-3">
              <span className="text-[10px] text-muted-foreground">نموذج الإسناد:</span>
              {(Object.entries(attributionModelLabels) as [AttributionModel, string][]).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setAttributionModel(key)}
                  className={`px-3 py-1.5 rounded-lg text-[10px] border transition-all ${
                    attributionModel === key
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border/30 text-muted-foreground hover:border-primary/30"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Channel attribution */}
            <div className="space-y-2">
              <h4 className="text-xs text-foreground">إسناد القنوات (صفقات مكسبة)</h4>
              {attributionByChannel.map(([channel, data]) => {
                const maxRevenue = Math.max(...attributionByChannel.map(([, d]) => d.revenue));
                const pct = maxRevenue > 0 ? (data.revenue / maxRevenue) * 100 : 0;
                return (
                  <div key={channel} className="p-3 rounded-xl border border-border/30 bg-card/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-foreground">{sourceLabels[channel as DealSource] ?? channel}</span>
                      <span className="text-xs text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        ${data.revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-muted/20 overflow-hidden">
                      <motion.div
                        className="h-full rounded-full bg-primary"
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ type: "spring", stiffness: 200, damping: 20 }}
                      />
                    </div>
                  </div>
                );
              })}
              {attributionByChannel.length === 0 && (
                <p className="text-xs text-muted-foreground text-center py-8">لا توجد صفقات مكسبة لتحليل الإسناد</p>
              )}
            </div>
          </TabsContent>

          {/* ═══ Funnel ═══ */}
          <TabsContent value="funnel" className="mt-4">
            <div className="space-y-2 max-w-xl mx-auto">
              {stageStats.filter((s) => s.stageId !== "won").map((stage, i) => {
                const config = stageConfigs.find((s) => s.id === stage.stageId)!;
                const maxCount = Math.max(...stageStats.map((s) => s.count), 1);
                const widthPct = Math.max((stage.count / maxCount) * 100, 20);
                return (
                  <motion.div
                    key={stage.stageId}
                    className={`rounded-xl border p-3 ${config.bgColor} mx-auto`}
                    style={{ width: `${widthPct}%` }}
                    initial={{ width: "0%", opacity: 0 }}
                    animate={{ width: `${widthPct}%`, opacity: 1 }}
                    transition={{ delay: i * 0.1, type: "spring", stiffness: 200 }}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-xs ${config.color}`}>{config.label}</span>
                      <span className="text-xs text-foreground">{stage.count}</span>
                    </div>
                    <p className="text-[9px] text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      ${stage.totalValue.toLocaleString()}
                    </p>
                  </motion.div>
                );
              })}

              {/* Won indicator */}
              <div className="text-center pt-4 border-t border-border/20 mt-4">
                <Check className="w-8 h-8 mx-auto mb-2 text-emerald-400" />
                <p className="text-xs text-emerald-400">
                  {wonDeals.length} صفقة مكسبة — <span style={{ direction: "ltr", unicodeBidi: "embed" }}>${wonValue.toLocaleString()}</span>
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* ── Deal Detail Overlay ── */}
        {selectedDeal && (
          <DealDetail deal={selectedDeal} onClose={() => setSelectedDeal(null)} />
        )}
      </div>
    </TooltipProvider>
  );
}

// ── Deal Detail ─────────────────────────────────────────

function DealDetail({ deal, onClose }: { deal: Deal; onClose: () => void }) {
  const stageConfig = stageConfigs.find((s) => s.id === deal.stage)!;
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/40" />
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        className="relative bg-card border border-border/40 rounded-2xl shadow-2xl w-[500px] max-h-[80vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm text-foreground">{deal.title}</h3>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center gap-3">
            <Badge className={`${stageConfig.bgColor} ${stageConfig.color} text-[9px]`}>
              {stageConfig.label}
            </Badge>
            <span className="text-lg text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
              ${deal.value.toLocaleString()}
            </span>
            {deal.isVip && <Star className="w-4 h-4 text-primary fill-primary" />}
          </div>

          {/* Customer */}
          <div className="p-3 rounded-lg border border-border/20 bg-muted/10">
            <p className="text-[9px] text-muted-foreground mb-1">العميل</p>
            <p className="text-xs text-foreground">{deal.customerName}</p>
            <p className="text-[10px] text-muted-foreground">المصدر: {sourceLabels[deal.source]} • الموظف: {deal.assignedAgent}</p>
          </div>

          {/* Touchpoints / Attribution */}
          <div>
            <p className="text-[10px] text-muted-foreground mb-2">نقاط التواصل (الإسناد)</p>
            <div className="space-y-1.5">
              {deal.touchpoints.map((tp, i) => (
                <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-muted/10">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-[8px] text-primary">
                    {i + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-[10px] text-foreground">{tp.action}</p>
                    <p className="text-[8px] text-muted-foreground">{sourceLabels[tp.channel]} • {tp.agent}</p>
                  </div>
                  <Badge className="bg-primary/10 text-primary text-[8px] h-4">{tp.contribution}%</Badge>
                </div>
              ))}
            </div>
          </div>

          {deal.notes && (
            <div className="p-3 rounded-lg border border-border/20 bg-muted/10">
              <p className="text-[9px] text-muted-foreground mb-1">ملاحظات</p>
              <p className="text-[10px] text-foreground">{deal.notes}</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
