// ═══════════════════════════════════════════════════════════
//  Live Supervisor Console
//  Real-time agent monitoring, conversation takeover, SLA dashboard
// ═══════════════════════════════════════════════════════════

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Eye, Users, MessageCircle, Phone, Shield, ArrowLeftRight,
  Clock, AlertTriangle, Activity,
  Star, BarChart3, Zap, Pause,
  Volume2, Search, RefreshCw, Check,
  Radio, PhoneMissed, PhoneForwarded, PhoneCall, UserCheck,
  RotateCcw, CheckCircle2,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";

// ── Types ───────────────────────────────────────────────

type AgentStatus = "available" | "busy" | "on-call" | "offline" | "break";

interface LiveAgent {
  id: string;
  name: string;
  role: "agent" | "supervisor";
  status: AgentStatus;
  activeChats: number;
  maxCapacity: number;
  activeCalls: number;
  todayResolved: number;
  todayMissed: number;
  avgResponseTime: number;
  csat: number;
  currentCustomer?: string;
  currentChannel?: string;
  idleMinutes: number;
  loginTime: string;
  slaBreaches: number;
}

interface LiveConversation {
  id: string;
  customerName: string;
  channel: string;
  agentName: string;
  agentId: string;
  waitingMinutes: number;
  messageCount: number;
  isEscalated: boolean;
  slaBreach: boolean;
  status: "active" | "waiting" | "escalated";
  lastActivity: string;
}

interface SlaMetric {
  label: string;
  current: number;
  target: number;
  unit: string;
  trend: "up" | "down" | "stable";
}

// ── Missed Call Types ───────────────────────────────────

type MissedCallStatus = "pending" | "callback-assigned" | "returned" | "no-answer" | "resolved";

interface MissedCall {
  id: string;
  customerName: string;
  customerPhone: string;
  channel: string;
  tier: "عادي" | "ذهبي" | "بلاتيني";
  missedAt: string;
  attempts: number;
  duration: number; // ring seconds before miss
  reason: string;
  status: MissedCallStatus;
  assignedAgent?: string;
  callbackTime?: string;
  note?: string;
  returnedAt?: string;
}

// ── Mock Data ───────────────────────────────────────────

const statusLabels: Record<AgentStatus, string> = {
  available: "متاح", busy: "مشغول", "on-call": "في مكالمة", offline: "غير متصل", break: "استراحة",
};

const statusColors: Record<AgentStatus, string> = {
  available: "bg-emerald-500", busy: "bg-primary", "on-call": "bg-violet-500", offline: "bg-zinc-500", break: "bg-blue-400",
};

const liveAgents: LiveAgent[] = [
  { id: "emp-01", name: "سعود المالكي", role: "agent", status: "busy", activeChats: 3, maxCapacity: 5, activeCalls: 0, todayResolved: 18, todayMissed: 1, avgResponseTime: 1.5, csat: 4.8, currentCustomer: "أحمد محمد العلي", currentChannel: "واتساب", idleMinutes: 0, loginTime: "2026-02-23T08:00:00", slaBreaches: 0 },
  { id: "emp-02", name: "منى الشهري", role: "agent", status: "available", activeChats: 1, maxCapacity: 5, activeCalls: 0, todayResolved: 12, todayMissed: 0, avgResponseTime: 2.0, csat: 4.9, idleMinutes: 3, loginTime: "2026-02-23T08:15:00", slaBreaches: 0 },
  { id: "emp-03", name: "عبدالله الحربي", role: "agent", status: "on-call", activeChats: 2, maxCapacity: 5, activeCalls: 1, todayResolved: 8, todayMissed: 2, avgResponseTime: 5.1, csat: 4.2, currentCustomer: "user_tiktok_392", currentChannel: "تيك توك", idleMinutes: 0, loginTime: "2026-02-23T09:00:00", slaBreaches: 2 },
  { id: "emp-05", name: "ريم الدوسري", role: "agent", status: "break", activeChats: 0, maxCapacity: 5, activeCalls: 0, todayResolved: 6, todayMissed: 0, avgResponseTime: 3.2, csat: 4.5, idleMinutes: 12, loginTime: "2026-02-23T08:30:00", slaBreaches: 0 },
  { id: "emp-06", name: "فارس العنزي", role: "agent", status: "busy", activeChats: 4, maxCapacity: 5, activeCalls: 0, todayResolved: 15, todayMissed: 1, avgResponseTime: 2.8, csat: 4.6, currentCustomer: "فاطمة عبدالله السالم", currentChannel: "بريد إلكتروني", idleMinutes: 0, loginTime: "2026-02-23T07:45:00", slaBreaches: 1 },
];

const liveConversations: LiveConversation[] = [
  { id: "lc-01", customerName: "أحمد محمد العلي", channel: "واتساب", agentName: "سعود المالكي", agentId: "emp-01", waitingMinutes: 0, messageCount: 5, isEscalated: false, slaBreach: false, status: "active", lastActivity: "2026-02-23T10:30:00" },
  { id: "lc-02", customerName: "خالد سعد القحطاني", channel: "بريد إلكتروني", agentName: "—", agentId: "", waitingMinutes: 120, messageCount: 1, isEscalated: true, slaBreach: true, status: "escalated", lastActivity: "2026-02-23T08:30:00" },
  { id: "lc-03", customerName: "مستخدم تيليجرام", channel: "تيليجرام", agentName: "AI Bot", agentId: "", waitingMinutes: 5, messageCount: 2, isEscalated: false, slaBreach: false, status: "waiting", lastActivity: "2026-02-23T10:25:00" },
  { id: "lc-04", customerName: "سارة علي الحربي", channel: "إنستقرام", agentName: "سعود المالكي", agentId: "emp-01", waitingMinutes: 20, messageCount: 12, isEscalated: false, slaBreach: false, status: "active", lastActivity: "2026-02-23T10:10:00" },
  { id: "lc-05", customerName: "user_tiktok_392", channel: "تيك توك", agentName: "عبدالله الحربي", agentId: "emp-03", waitingMinutes: 10, messageCount: 3, isEscalated: false, slaBreach: false, status: "active", lastActivity: "2026-02-23T10:20:00" },
  { id: "lc-06", customerName: "فاطمة عبدالله السالم", channel: "بريد إلكتروني", agentName: "فارس العنزي", agentId: "emp-06", waitingMinutes: 35, messageCount: 4, isEscalated: false, slaBreach: true, status: "active", lastActivity: "2026-02-23T09:55:00" },
  { id: "lc-07", customerName: "زائر الموقع", channel: "محادثة الويب", agentName: "AI Bot", agentId: "", waitingMinutes: 2, messageCount: 2, isEscalated: false, slaBreach: false, status: "waiting", lastActivity: "2026-02-23T10:28:00" },
];

const slaMetrics: SlaMetric[] = [
  { label: "متوسط وقت الاستجابة الأولى", current: 2.3, target: 3, unit: "د", trend: "down" },
  { label: "معدل الحل من أول تواصل", current: 78, target: 80, unit: "%", trend: "up" },
  { label: "نسبة مخالفات SLA", current: 4.2, target: 5, unit: "%", trend: "down" },
  { label: "رضا العملاء (CSAT)", current: 4.6, target: 4.5, unit: "/5", trend: "up" },
  { label: "متوسط وقت المعالجة", current: 8.5, target: 10, unit: "د", trend: "stable" },
  { label: "معدل التصعيد", current: 3.1, target: 5, unit: "%", trend: "down" },
];

// ── Missed Calls Mock Data ──────────────────────────────

const missedCallStatusLabels: Record<MissedCallStatus, string> = {
  pending: "بانتظار المعالجة",
  "callback-assigned": "معاد الاتصال معيّن",
  returned: "تم إعادة الاتصال",
  "no-answer": "لم يرد",
  resolved: "تم الحل",
};

const missedCallStatusColors: Record<MissedCallStatus, string> = {
  pending: "bg-red-500/15 text-red-400 border-red-500/20",
  "callback-assigned": "bg-primary/15 text-primary border-primary/20",
  returned: "bg-blue-500/15 text-blue-400 border-blue-500/20",
  "no-answer": "bg-red-500/10 text-red-300 border-red-500/15",
  resolved: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
};

const initialMissedCalls: MissedCall[] = [
  { id: "mc-01", customerName: "أحمد محمد العلي", customerPhone: "+966 50 123 4567", channel: "هاتف", tier: "بلاتيني", missedAt: "2026-02-25T09:15:00", attempts: 2, duration: 28, reason: "جميع الموظفين مشغولون", status: "pending", note: "عميل VIP — يجب الاتصال فوراً" },
  { id: "mc-02", customerName: "فاطمة عبدالله السالم", customerPhone: "+966 55 987 6543", channel: "هاتف", tier: "ذهبي", missedAt: "2026-02-25T09:32:00", attempts: 1, duration: 15, reason: "خارج ساعات العمل (المسائي)", status: "callback-assigned", assignedAgent: "منى الشهري", callbackTime: "2026-02-25T10:00:00" },
  { id: "mc-03", customerName: "خالد سعد القحطاني", customerPhone: "+966 56 444 3333", channel: "واتساب", tier: "عادي", missedAt: "2026-02-25T08:50:00", attempts: 3, duration: 40, reason: "المحادثة لم تُقرأ — مهلة انتهت", status: "returned", assignedAgent: "سعود المالكي", returnedAt: "2026-02-25T09:20:00", note: "تم الاتصال — يريد متابعة طلب #2045" },
  { id: "mc-04", customerName: "ريم سعود الراشد", customerPhone: "+966 55 999 0000", channel: "هاتف", tier: "عادي", missedAt: "2026-02-25T10:05:00", attempts: 1, duration: 12, reason: "الموظف في استراحة", status: "pending" },
  { id: "mc-05", customerName: "عبدالرحمن الغامدي", customerPhone: "+966 54 222 1111", channel: "هاتف", tier: "ذهبي", missedAt: "2026-02-25T08:20:00", attempts: 2, duration: 32, reason: "السعة القصوى ممتلئة", status: "no-answer", assignedAgent: "عبدالله الحربي", callbackTime: "2026-02-25T09:00:00", note: "تم محاولة الاتصال مرتين — لم يرد" },
  { id: "mc-06", customerName: "سارة علي الحربي", customerPhone: "+966 59 555 6666", channel: "هاتف", tier: "بلاتيني", missedAt: "2026-02-25T07:45:00", attempts: 1, duration: 20, reason: "قبل بدء الدوام", status: "resolved", assignedAgent: "فارس العنزي", returnedAt: "2026-02-25T08:05:00", note: "تم الرد — استفسار عن عطر جديد — تمت المعالجة" },
  { id: "mc-07", customerName: "نوف العتيبي", customerPhone: "+966 50 777 8888", channel: "واتساب", tier: "عادي", missedAt: "2026-02-25T10:18:00", attempts: 1, duration: 8, reason: "العميل أنهى المكالمة قبل الرد", status: "pending" },
  { id: "mc-08", customerName: "محمد الدوسري", customerPhone: "+966 53 333 4444", channel: "هاتف", tier: "ذهبي", missedAt: "2026-02-25T09:55:00", attempts: 4, duration: 55, reason: "تكرار الاتصال — لا يوجد متاح", status: "callback-assigned", assignedAgent: "ريم الدوسري", callbackTime: "2026-02-25T10:30:00", note: "أولوية عالية — 4 محاولات" },
];

// ── Main Component ──────────────────────────────────────

export function Supervisor() {
  const [activeTab, setActiveTab] = useState<"live" | "agents" | "sla" | "queue" | "missed">("live");
  const [searchQuery, setSearchQuery] = useState("");
  const [missedCalls, setMissedCalls] = useState<MissedCall[]>(initialMissedCalls);
  const [missedFilter, setMissedFilter] = useState<"all" | "pending" | "assigned" | "resolved">("all");
  const [showAgentPicker, setShowAgentPicker] = useState<string | null>(null);

  const totalOnline = liveAgents.filter((a) => a.status !== "offline").length;
  const totalChats = liveAgents.reduce((s, a) => s + a.activeChats, 0);
  const totalCalls = liveAgents.reduce((s, a) => s + a.activeCalls, 0);
  const totalBreaches = liveConversations.filter((c) => c.slaBreach).length;
  const totalEscalated = liveConversations.filter((c) => c.isEscalated).length;
  const avgCsat = liveAgents.length > 0 ? (liveAgents.reduce((s, a) => s + a.csat, 0) / liveAgents.length).toFixed(1) : "0";
  const totalMissedPending = missedCalls.filter((mc) => mc.status === "pending").length;

  const filteredConversations = useMemo(() => {
    if (!searchQuery) return liveConversations;
    const q = searchQuery.toLowerCase();
    return liveConversations.filter(
      (c) => c.customerName.toLowerCase().includes(q) || c.agentName.includes(searchQuery) || c.channel.includes(searchQuery),
    );
  }, [searchQuery]);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">

        {/* ── Live Indicator ── */}
        <div className="flex items-center gap-2 text-xs text-emerald-400">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
          بث مباشر — آخر تحديث: الآن
          <Button variant="ghost" size="sm" className="h-6 text-[9px] gap-1 ms-2 text-muted-foreground">
            <RefreshCw className="w-3 h-3" /> تحديث
          </Button>
        </div>

        {/* ── KPIs ── */}
        <div className="grid grid-cols-2 md:grid-cols-7 gap-3">
          {[
            { label: "موظفون متصلون", value: totalOnline, icon: Users, color: "text-emerald-400" },
            { label: "محادثات نشطة", value: totalChats, icon: MessageCircle, color: "text-primary" },
            { label: "مكالمات جارية", value: totalCalls, icon: Phone, color: "text-violet-400" },
            { label: "مكالمات فائتة", value: totalMissedPending, icon: PhoneMissed, color: totalMissedPending > 0 ? "text-red-500" : "text-muted-foreground" },
            { label: "مخالفات SLA", value: totalBreaches, icon: AlertTriangle, color: totalBreaches > 0 ? "text-red-500" : "text-muted-foreground" },
            { label: "تصعيدات", value: totalEscalated, icon: Zap, color: totalEscalated > 0 ? "text-red-400" : "text-muted-foreground" },
            { label: "CSAT", value: avgCsat, icon: Star, color: "text-primary" },
          ].map((kpi) => {
            const Icon = kpi.icon;
            return (
              <div key={kpi.label} className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
                <Icon className={`w-4 h-4 mx-auto mb-1 ${kpi.color}`} />
                <p className={`text-2xl ${kpi.color}`}>{kpi.value}</p>
                <p className="text-[9px] text-muted-foreground mt-0.5">{kpi.label}</p>
              </div>
            );
          })}
        </div>

        {/* ── Tabs ── */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <TabsList className="bg-muted/20">
            <TabsTrigger value="live" className="text-xs gap-1.5">
              <Radio className="w-3.5 h-3.5" />
              البث المباشر
            </TabsTrigger>
            <TabsTrigger value="agents" className="text-xs gap-1.5">
              <Users className="w-3.5 h-3.5" />
              الموظفون
            </TabsTrigger>
            <TabsTrigger value="sla" className="text-xs gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              SLA
            </TabsTrigger>
            <TabsTrigger value="queue" className="text-xs gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              طابور الانتظار
            </TabsTrigger>
            <TabsTrigger value="missed" className="text-xs gap-1.5">
              <PhoneMissed className="w-3.5 h-3.5" />
              المكالمات الفائتة
            </TabsTrigger>
          </TabsList>

          {/* ═══ Live Feed ═══ */}
          <TabsContent value="live" className="mt-4">
            <div className="relative mb-4">
              <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                placeholder="بحث بالعميل أو الموظف أو القناة..."
                className="h-8 text-xs ps-8 w-64"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              {filteredConversations.map((conv) => (
                <motion.div
                  key={conv.id}
                  layout
                  className={`p-3 rounded-xl border transition-all ${
                    conv.isEscalated
                      ? "border-red-500/30 bg-red-500/5"
                      : conv.slaBreach
                        ? "border-red-500/20 bg-red-500/[0.02]"
                        : "border-border/30 bg-card/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="text-[9px] bg-primary/10 text-primary">
                          {conv.customerName.slice(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-foreground">{conv.customerName}</span>
                          <span className="text-[8px] px-1.5 py-0.5 rounded bg-muted/30 text-muted-foreground">{conv.channel}</span>
                          {conv.isEscalated && (
                            <Badge className="bg-red-500/15 text-red-500 text-[7px] h-4">مصعّد</Badge>
                          )}
                          {conv.slaBreach && !conv.isEscalated && (
                            <Badge className="bg-red-500/10 text-red-400 text-[7px] h-4">SLA</Badge>
                          )}
                        </div>
                        <p className="text-[9px] text-muted-foreground">
                          الموظف: {conv.agentName} • {conv.messageCount} رسالة • انتظار {conv.waitingMinutes} د
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                            <Eye className="w-3.5 h-3.5" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">مراقبة المحادثة</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                            <Volume2 className="w-3.5 h-3.5" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">استماع صامت</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline" size="sm" className="h-7 text-[9px] gap-1 text-red-400 border-red-500/30 hover:bg-red-500/10">
                            <Shield className="w-3 h-3" />
                            تولي
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">تولي المحادثة (تجاوز المشرف)</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline" size="sm" className="h-7 text-[9px] gap-1">
                            <ArrowLeftRight className="w-3 h-3" />
                            نقل
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">نقل لموظف آخر</TooltipContent>
                      </Tooltip>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          {/* ═══ Agents Grid ═══ */}
          <TabsContent value="agents" className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {liveAgents.map((agent) => (
                <div key={agent.id} className="p-4 rounded-xl border border-border/30 bg-card/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback className="bg-primary/10 text-primary text-xs">
                            {agent.name.slice(0, 2)}
                          </AvatarFallback>
                        </Avatar>
                        <span className={`absolute -bottom-0.5 -end-0.5 w-3 h-3 rounded-full border-2 border-card ${statusColors[agent.status]}`} />
                      </div>
                      <div>
                        <p className="text-sm text-foreground">{agent.name}</p>
                        <p className="text-[9px] text-muted-foreground">{statusLabels[agent.status]}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                            <MessageCircle className="w-3.5 h-3.5" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">إرسال رسالة</TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-red-400">
                            <Pause className="w-3.5 h-3.5" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">إجبار استراحة</TooltipContent>
                      </Tooltip>
                    </div>
                  </div>

                  {/* Capacity bar */}
                  <div>
                    <div className="flex items-center justify-between text-[9px] text-muted-foreground mb-1">
                      <span>السعة</span>
                      <span>{agent.activeChats}/{agent.maxCapacity}</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-muted/20 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          agent.activeChats / agent.maxCapacity >= 0.8 ? "bg-red-500" : "bg-primary"
                        }`}
                        style={{ width: `${(agent.activeChats / agent.maxCapacity) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Stats grid */}
                  <div className="grid grid-cols-4 gap-2 text-center">
                    <div className="p-1.5 rounded bg-muted/10">
                      <p className="text-sm text-emerald-400">{agent.todayResolved}</p>
                      <p className="text-[7px] text-muted-foreground">حل</p>
                    </div>
                    <div className="p-1.5 rounded bg-muted/10">
                      <p className="text-sm text-red-400">{agent.todayMissed}</p>
                      <p className="text-[7px] text-muted-foreground">فائت</p>
                    </div>
                    <div className="p-1.5 rounded bg-muted/10">
                      <p className="text-sm text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{agent.avgResponseTime}د</p>
                      <p className="text-[7px] text-muted-foreground">استجابة</p>
                    </div>
                    <div className="p-1.5 rounded bg-muted/10">
                      <p className="text-sm text-primary">{agent.csat}</p>
                      <p className="text-[7px] text-muted-foreground">CSAT</p>
                    </div>
                  </div>

                  {/* Current activity */}
                  {agent.currentCustomer && (
                    <div className="flex items-center gap-2 text-[9px] text-muted-foreground bg-muted/10 px-2 py-1.5 rounded-lg">
                      <Activity className="w-3 h-3 text-primary" />
                      <span>يتحدث مع: <span className="text-foreground">{agent.currentCustomer}</span></span>
                      <span className="text-muted-foreground/50">({agent.currentChannel})</span>
                    </div>
                  )}

                  {agent.slaBreaches > 0 && (
                    <div className="flex items-center gap-1 text-[9px] text-red-400">
                      <AlertTriangle className="w-3 h-3" />
                      {agent.slaBreaches} مخالفة SLA اليوم
                    </div>
                  )}

                  {agent.idleMinutes > 5 && agent.status !== "offline" && agent.status !== "break" && (
                    <div className="flex items-center gap-1 text-[9px] text-blue-400">
                      <Clock className="w-3 h-3" />
                      خامل منذ {agent.idleMinutes} دقيقة
                    </div>
                  )}
                </div>
              ))}
            </div>
          </TabsContent>

          {/* ═══ SLA Dashboard ═══ */}
          <TabsContent value="sla" className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {slaMetrics.map((metric) => {
                const pct = Math.min((metric.current / metric.target) * 100, 100);
                const isGood = metric.label.includes("مخالفات") || metric.label.includes("التصعيد")
                  ? metric.current <= metric.target
                  : metric.current >= metric.target;

                return (
                  <div key={metric.label} className="p-4 rounded-xl border border-border/30 bg-card/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-foreground">{metric.label}</p>
                      <Badge className={`text-[8px] h-4 ${
                        isGood ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                      }`}>
                        {metric.trend === "up" ? "↑" : metric.trend === "down" ? "↓" : "→"}
                      </Badge>
                    </div>
                    <div className="flex items-end gap-2">
                      <span className={`text-3xl ${isGood ? "text-emerald-400" : "text-red-400"}`}>
                        {metric.current}
                      </span>
                      <span className="text-sm text-muted-foreground mb-1">{metric.unit}</span>
                      <span className="text-[9px] text-muted-foreground mb-1.5 ms-auto">
                        الهدف: {metric.target}{metric.unit}
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-muted/20 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${isGood ? "bg-emerald-500" : "bg-red-500"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </TabsContent>

          {/* ═══ Queue ═══ */}
          <TabsContent value="queue" className="mt-4">
            <div className="space-y-2">
              {liveConversations
                .filter((c) => c.status === "waiting" || c.status === "escalated")
                .sort((a, b) => b.waitingMinutes - a.waitingMinutes)
                .map((conv) => (
                  <div
                    key={conv.id}
                    className={`p-3 rounded-xl border flex items-center justify-between ${
                      conv.isEscalated ? "border-red-500/30 bg-red-500/5" : "border-border/30 bg-card/30"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-8 rounded-full ${conv.isEscalated ? "bg-red-500" : conv.slaBreach ? "bg-red-400" : "bg-primary"}`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-foreground">{conv.customerName}</span>
                          <span className="text-[8px] px-1.5 py-0.5 rounded bg-muted/30 text-muted-foreground">{conv.channel}</span>
                        </div>
                        <p className="text-[9px] text-muted-foreground">
                          في الانتظار منذ <span className={conv.waitingMinutes > 10 ? "text-red-400" : "text-foreground"}>{conv.waitingMinutes} دقيقة</span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Button size="sm" className="h-7 text-[9px] gap-1">
                        <ArrowLeftRight className="w-3 h-3" />
                        تعيين موظف
                      </Button>
                      <Button variant="outline" size="sm" className="h-7 text-[9px] gap-1 text-red-400 border-red-500/30">
                        <Shield className="w-3 h-3" />
                        تولي
                      </Button>
                    </div>
                  </div>
                ))}
              {liveConversations.filter((c) => c.status === "waiting" || c.status === "escalated").length === 0 && (
                <div className="text-center py-12 text-xs text-muted-foreground">
                  <Check className="w-8 h-8 mx-auto mb-2 text-emerald-400/30" />
                  لا توجد محادثات في الانتظار
                </div>
              )}
            </div>
          </TabsContent>

          {/* ═══ Missed Calls ═══ */}
          <TabsContent value="missed" className="mt-4">
            <div className="space-y-3">
              {/* Summary + Filters */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-red-400">
                    <PhoneMissed className="w-4 h-4" />
                    <span>{totalMissedPending} بانتظار المعالجة</span>
                  </div>
                  <span className="text-[9px] text-muted-foreground">من أصل {missedCalls.length} مكالمة اليوم</span>
                </div>
                <div className="flex gap-1.5">
                  {(["all", "pending", "assigned", "resolved"] as const).map((f) => (
                    <button
                      key={f}
                      onClick={() => setMissedFilter(f)}
                      className={`px-2.5 py-1.5 rounded-lg text-[10px] border transition-all cursor-pointer ${
                        missedFilter === f
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border/30 text-muted-foreground hover:border-primary/30"
                      }`}
                    >
                      {f === "all" ? "الكل" : f === "pending" ? "بانتظار" : f === "assigned" ? "معيّن" : "محلول"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Missed Calls List */}
              <div className="space-y-2">
                <AnimatePresence>
                  {missedCalls
                    .filter((mc) => {
                      if (missedFilter === "all") return true;
                      if (missedFilter === "pending") return mc.status === "pending" || mc.status === "no-answer";
                      if (missedFilter === "assigned") return mc.status === "callback-assigned" || mc.status === "returned";
                      return mc.status === "resolved";
                    })
                    .sort((a, b) => {
                      const order: Record<MissedCallStatus, number> = { pending: 0, "no-answer": 1, "callback-assigned": 2, returned: 3, resolved: 4 };
                      const diff = order[a.status] - order[b.status];
                      if (diff !== 0) return diff;
                      return new Date(b.missedAt).getTime() - new Date(a.missedAt).getTime();
                    })
                    .map((mc) => {
                      const tierColors = mc.tier === "بلاتيني" ? "bg-violet-500/15 text-violet-400 border-violet-500/20" : mc.tier === "ذهبي" ? "bg-primary/15 text-primary border-primary/20" : "bg-muted/20 text-muted-foreground border-border/20";
                      const isPending = mc.status === "pending";
                      const isPickerOpen = showAgentPicker === mc.id;

                      return (
                        <motion.div
                          key={mc.id}
                          layout
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -6 }}
                          className={`p-3.5 rounded-xl border transition-all ${
                            isPending
                              ? "border-red-500/30 bg-red-500/[0.04]"
                              : mc.status === "no-answer"
                                ? "border-red-500/15 bg-card/30"
                                : "border-border/30 bg-card/30"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            {/* Left: Info */}
                            <div className="flex items-start gap-3 flex-1 min-w-0">
                              {/* Priority indicator */}
                              <div className={`w-1.5 h-full min-h-[60px] rounded-full shrink-0 ${
                                mc.tier === "بلاتيني" ? "bg-violet-500" : mc.tier === "ذهبي" ? "bg-primary" : "bg-muted-foreground/30"
                              }`} />

                              <div className="flex-1 min-w-0 space-y-1.5">
                                {/* Name row */}
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-sm text-foreground">{mc.customerName}</span>
                                  <Badge className={`text-[7px] h-4 border ${tierColors}`}>{mc.tier}</Badge>
                                  <Badge className={`text-[7px] h-4 border ${missedCallStatusColors[mc.status]}`}>
                                    {missedCallStatusLabels[mc.status]}
                                  </Badge>
                                </div>

                                {/* Details */}
                                <div className="flex items-center gap-3 flex-wrap text-[9px] text-muted-foreground">
                                  <span className="flex items-center gap-1" dir="ltr">
                                    <Phone className="w-3 h-3" />
                                    {mc.customerPhone}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {new Date(mc.missedAt).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" })}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <RotateCcw className="w-3 h-3" />
                                    {mc.attempts} {mc.attempts > 1 ? "محاولات" : "محاولة"}
                                  </span>
                                  <span>{mc.duration} ثانية رنين</span>
                                  <span className="text-[8px] px-1.5 py-0.5 rounded bg-muted/20">{mc.channel}</span>
                                </div>

                                {/* Reason */}
                                <p className="text-[9px] text-muted-foreground/70">{mc.reason}</p>

                                {/* Assignment info */}
                                {mc.assignedAgent && (
                                  <div className="flex items-center gap-1.5 text-[9px]">
                                    <UserCheck className="w-3 h-3 text-primary" />
                                    <span className="text-muted-foreground">معيّن لـ</span>
                                    <span className="text-foreground">{mc.assignedAgent}</span>
                                    {mc.callbackTime && (
                                      <span className="text-muted-foreground/60">
                                        — الاتصال: {new Date(mc.callbackTime).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" })}
                                      </span>
                                    )}
                                  </div>
                                )}

                                {/* Note */}
                                {mc.note && (
                                  <p className="text-[9px] text-muted-foreground/80 border-s-2 border-primary/20 ps-2 mt-1">{mc.note}</p>
                                )}
                              </div>
                            </div>

                            {/* Right: Actions */}
                            <div className="flex flex-col items-end gap-1.5 shrink-0 relative">
                              {(mc.status === "pending" || mc.status === "no-answer") && (
                                <Button
                                  size="sm"
                                  className="h-7 text-[9px] gap-1"
                                  onClick={() => setShowAgentPicker(isPickerOpen ? null : mc.id)}
                                >
                                  <PhoneForwarded className="w-3 h-3" />
                                  تعيين إعادة اتصال
                                </Button>
                              )}
                              {mc.status === "callback-assigned" && (
                                <Button variant="outline" size="sm" className="h-7 text-[9px] gap-1">
                                  <PhoneCall className="w-3 h-3" />
                                  تأكيد الاتصال
                                </Button>
                              )}
                              {(mc.status === "returned" || mc.status === "no-answer") && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="h-7 text-[9px] gap-1 text-emerald-400 border-emerald-500/30"
                                  onClick={() => setMissedCalls((prev) => prev.map((m) => m.id === mc.id ? { ...m, status: "resolved" as MissedCallStatus } : m))}
                                >
                                  <CheckCircle2 className="w-3 h-3" />
                                  تم الحل
                                </Button>
                              )}

                              {/* Agent Picker Dropdown */}
                              <AnimatePresence>
                                {isPickerOpen && (
                                  <motion.div
                                    initial={{ opacity: 0, scale: 0.95, y: -4 }}
                                    animate={{ opacity: 1, scale: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.95, y: -4 }}
                                    className="absolute top-8 end-0 z-50 w-48 bg-card border border-border/40 rounded-xl shadow-lg p-2 space-y-1"
                                  >
                                    <p className="text-[9px] text-muted-foreground px-2 py-1">اختر موظفاً:</p>
                                    {liveAgents
                                      .filter((a) => a.status === "available" || a.status === "busy")
                                      .map((agent) => (
                                        <button
                                          key={agent.id}
                                          className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-start text-xs hover:bg-primary/10 transition-colors cursor-pointer"
                                          onClick={() => {
                                            setMissedCalls((prev) =>
                                              prev.map((m) =>
                                                m.id === mc.id
                                                  ? { ...m, status: "callback-assigned" as MissedCallStatus, assignedAgent: agent.name, callbackTime: new Date().toISOString() }
                                                  : m,
                                              ),
                                            );
                                            setShowAgentPicker(null);
                                          }}
                                        >
                                          <span className={`w-2 h-2 rounded-full ${statusColors[agent.status]}`} />
                                          <span className="text-foreground">{agent.name}</span>
                                          <span className="text-[8px] text-muted-foreground ms-auto">{agent.activeChats}/{agent.maxCapacity}</span>
                                        </button>
                                      ))}
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                </AnimatePresence>

                {missedCalls.filter((mc) => {
                  if (missedFilter === "all") return true;
                  if (missedFilter === "pending") return mc.status === "pending" || mc.status === "no-answer";
                  if (missedFilter === "assigned") return mc.status === "callback-assigned" || mc.status === "returned";
                  return mc.status === "resolved";
                }).length === 0 && (
                  <div className="text-center py-12 text-xs text-muted-foreground">
                    <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-400/30" />
                    لا توجد مكالمات مفقودة في هذا التصنيف
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </TooltipProvider>
  );
}