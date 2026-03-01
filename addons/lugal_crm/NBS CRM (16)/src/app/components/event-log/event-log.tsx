// ═══════════════════════════════════════════════════════════
//  Event Logging Engine
//  Immutable, filterable, comprehensive system event tracker
//  Connected to: All modules, Audit compliance
// ═══════════════════════════════════════════════════════════

import { useState, useMemo } from "react";
import { motion } from "motion/react";
import {
  ScrollText, Search, Filter, Clock, User, Lock, Shield,
  MessageCircle, Phone, FileText, Package, Truck, DollarSign,
  Settings, Star, AlertTriangle, ChevronDown, Eye, Hash,
  Calendar, Activity, Zap, RefreshCw, Download,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../ui/table";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";

// ── Types ───────────────────────────────────────────────

type EventModule =
  | "omni_channel" | "tickets" | "orders" | "customers"
  | "products" | "invoices" | "agents" | "promotions"
  | "auth" | "admin" | "rules" | "system";

type EventSeverity = "info" | "warning" | "error" | "critical" | "success";

interface SystemEvent {
  id: string;
  timestamp: string;
  module: EventModule;
  action: string;
  description: string;
  actor: string; // who triggered it
  actorRole: string;
  targetEntity?: string; // e.g. "Customer C-001"
  targetId?: string;
  severity: EventSeverity;
  metadata?: Record<string, string>;
  ip?: string;
  immutable: true; // always true — audit compliance
}

// ── Config ──────────────────────────────────────────────

const moduleLabels: Record<EventModule, string> = {
  omni_channel: "القنوات الموحدة", tickets: "التذاكر", orders: "الطلبات",
  customers: "العملاء", products: "المنتجات", invoices: "الفواتير",
  agents: "الموظفون", promotions: "العروض", auth: "المصادقة",
  admin: "الإدارة", rules: "القواعد", system: "النظام",
};

const moduleColors: Record<EventModule, string> = {
  omni_channel: "bg-blue-500/10 text-blue-400", tickets: "bg-cyan-500/10 text-cyan-400",
  orders: "bg-violet-500/10 text-violet-400", customers: "bg-emerald-500/10 text-emerald-400",
  products: "bg-primary/10 text-primary", invoices: "bg-pink-500/10 text-pink-400",
  agents: "bg-blue-400/10 text-blue-300", promotions: "bg-rose-500/10 text-rose-400",
  auth: "bg-zinc-500/10 text-zinc-400", admin: "bg-red-500/10 text-red-400",
  rules: "bg-purple-500/10 text-purple-400", system: "bg-slate-500/10 text-slate-400",
};

const severityColors: Record<EventSeverity, string> = {
  info: "text-blue-400", warning: "text-yellow-400",
  error: "text-red-500", critical: "text-red-600",
  success: "text-emerald-400",
};

const severityLabels: Record<EventSeverity, string> = {
  info: "معلومة", warning: "تحذير", error: "خطأ", critical: "حرج", success: "نجاح",
};

const moduleIcons: Record<EventModule, typeof ScrollText> = {
  omni_channel: MessageCircle, tickets: FileText, orders: Package,
  customers: User, products: Package, invoices: DollarSign,
  agents: User, promotions: Star, auth: Lock,
  admin: Shield, rules: Settings, system: Activity,
};

// ── Mock Events ─────────────────────────────────────────

const mockEvents: SystemEvent[] = [
  { id: "evt-001", timestamp: "2026-02-23T10:30:00", module: "omni_channel", action: "message.received", description: "رسالة واردة من أحمد العلي عبر واتساب", actor: "system", actorRole: "نظام", severity: "info", targetEntity: "محادثة conv-001", immutable: true },
  { id: "evt-002", timestamp: "2026-02-23T10:30:05", module: "omni_channel", action: "conversation.assigned", description: "تم تعيين المحادثة لسعود المالكي تلقائياً (قاعدة التوجيه)", actor: "rule-engine", actorRole: "محرك القواعد", targetEntity: "conv-001", severity: "info", immutable: true },
  { id: "evt-003", timestamp: "2026-02-23T10:28:00", module: "omni_channel", action: "ai.response", description: "الـ AI ردّ على زائر الموقع — خارج الدوام", actor: "AI Bot", actorRole: "بوت", severity: "info", targetEntity: "conv-008", immutable: true },
  { id: "evt-004", timestamp: "2026-02-23T10:25:00", module: "tickets", action: "ticket.created", description: "تذكرة جديدة: TK-2026-0007 — شكوى تأخير توصيل", actor: "سعود المالكي", actorRole: "موظف", targetEntity: "TK-2026-0007", severity: "info", immutable: true },
  { id: "evt-005", timestamp: "2026-02-23T10:20:00", module: "tickets", action: "sla.breach", description: "مخالفة SLA على تذكرة TK-2026-0003 — تجاوز 24 ساعة", actor: "system", actorRole: "نظام", targetEntity: "TK-2026-0003", severity: "warning", immutable: true },
  { id: "evt-006", timestamp: "2026-02-23T10:15:00", module: "orders", action: "order.status_change", description: "ORD-4521 — تحديث الحالة من 'shipped' إلى 'in_transit'", actor: "system", actorRole: "نظام", targetEntity: "ORD-4521", severity: "info", metadata: { trackingNumber: "ARX-29384756" }, immutable: true },
  { id: "evt-007", timestamp: "2026-02-23T10:00:00", module: "auth", action: "login", description: "تسجيل دخول — فارس العنزي", actor: "فارس العنزي", actorRole: "موظف", severity: "success", ip: "192.168.1.45", immutable: true },
  { id: "evt-008", timestamp: "2026-02-23T09:55:00", module: "customers", action: "customer.vip_upgrade", description: "ترقية خالد القحطاني إلى VIP — تجاوز حد الإنفاق", actor: "rule-engine", actorRole: "محرك القواعد", targetEntity: "C-003", severity: "success", immutable: true },
  { id: "evt-009", timestamp: "2026-02-23T09:45:00", module: "promotions", action: "campaign.approved", description: "اعتماد حملة 'خصم نهاية الشتاء' من المدير", actor: "فهد الراشد", actorRole: "مشرف", targetEntity: "camp-03", severity: "success", immutable: true },
  { id: "evt-010", timestamp: "2026-02-23T09:30:00", module: "invoices", action: "invoice.generated", description: "إنشاء فاتورة INV-2026-0090 لفاطمة السالم", actor: "منى الشهري", actorRole: "موظف", targetEntity: "INV-2026-0090", severity: "info", immutable: true },
  { id: "evt-011", timestamp: "2026-02-23T09:15:00", module: "rules", action: "rule.updated", description: "تعديل قاعدة SLA — خفض وقت الاستجابة الأولى من 5 إلى 3 دقائق", actor: "فهد الراشد", actorRole: "مشرف", targetEntity: "rule-sla-001", severity: "warning", immutable: true },
  { id: "evt-012", timestamp: "2026-02-23T09:00:00", module: "auth", action: "login", description: "تسجيل دخول — سعود المالكي", actor: "سعود المالكي", actorRole: "موظف", severity: "success", ip: "192.168.1.20", immutable: true },
  { id: "evt-013", timestamp: "2026-02-23T08:45:00", module: "agents", action: "agent.status_change", description: "عبدالله الحربي — تغيير الحالة إلى 'متاح'", actor: "عبدالله الحربي", actorRole: "موظف", severity: "info", immutable: true },
  { id: "evt-014", timestamp: "2026-02-23T08:36:00", module: "omni_channel", action: "escalation.triggered", description: "تصعيد محادثة خالد القحطاني — تجاوز SLA بدون رد", actor: "rule-engine", actorRole: "محرك القواعد", targetEntity: "conv-006", severity: "error", immutable: true },
  { id: "evt-015", timestamp: "2026-02-23T08:30:00", module: "admin", action: "branch.config_update", description: "تحديث إعدادات فرع جدة — تعديل ساعات العمل", actor: "فهد الراشد", actorRole: "مشرف", targetEntity: "br-02", severity: "warning", immutable: true },
  { id: "evt-016", timestamp: "2026-02-23T08:00:00", module: "system", action: "system.startup", description: "بدء تشغيل النظام — جميع الوحدات متصلة", actor: "system", actorRole: "نظام", severity: "success", immutable: true },
  { id: "evt-017", timestamp: "2026-02-22T23:55:00", module: "system", action: "backup.completed", description: "نسخة احتياطية يومية مكتملة — 2.3 GB", actor: "system", actorRole: "نظام", severity: "success", immutable: true },
  { id: "evt-018", timestamp: "2026-02-22T22:00:00", module: "omni_channel", action: "ai.after_hours", description: "تفعيل بوت AI خارج الدوام — 5 قنوات", actor: "rule-engine", actorRole: "محرك القواعد", severity: "info", immutable: true },
  { id: "evt-019", timestamp: "2026-02-22T18:00:00", module: "agents", action: "attendance.clock_out", description: "تسجيل خروج — منى الشهري (إجمالي: 9.5 ساعة)", actor: "منى الشهري", actorRole: "موظف", severity: "info", immutable: true },
  { id: "evt-020", timestamp: "2026-02-22T17:30:00", module: "products", action: "stock.low_alert", description: "تنبيه مخزون منخفض: ناتورال أبسوليوت (3 قطع متبقية)", actor: "system", actorRole: "نظام", targetEntity: "PERF-008", severity: "warning", immutable: true },
];

// ── Main Component ──────────────────────────────────────

export function EventLog() {
  const [moduleFilter, setModuleFilter] = useState<EventModule | "all">("all");
  const [severityFilter, setSeverityFilter] = useState<EventSeverity | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<SystemEvent | null>(null);

  const filteredEvents = useMemo(() => {
    let evts = [...mockEvents];
    if (moduleFilter !== "all") evts = evts.filter((e) => e.module === moduleFilter);
    if (severityFilter !== "all") evts = evts.filter((e) => e.severity === severityFilter);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      evts = evts.filter(
        (e) =>
          e.description.includes(searchQuery) ||
          e.actor.includes(searchQuery) ||
          e.action.toLowerCase().includes(q) ||
          (e.targetEntity && e.targetEntity.toLowerCase().includes(q)),
      );
    }
    return evts.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [moduleFilter, severityFilter, searchQuery]);

  const stats = useMemo(() => ({
    total: mockEvents.length,
    warnings: mockEvents.filter((e) => e.severity === "warning").length,
    errors: mockEvents.filter((e) => e.severity === "error" || e.severity === "critical").length,
    today: mockEvents.filter((e) => e.timestamp.startsWith("2026-02-23")).length,
  }), []);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">

        {/* ── Immutability badge ── */}
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground bg-muted/10 px-3 py-2 rounded-lg border border-border/20">
          <Lock className="w-3.5 h-3.5 text-primary" />
          <span>سجل الأحداث <span className="text-primary">غير قابل للتعديل</span> — جميع السجلات محفوظة للتدقيق</span>
          <Button variant="ghost" size="sm" className="h-6 text-[9px] gap-1 ms-auto">
            <Download className="w-3 h-3" />
            تصدير CSV
          </Button>
        </div>

        {/* ── Stats ── */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: "إجمالي الأحداث", value: stats.total, color: "text-foreground" },
            { label: "اليوم", value: stats.today, color: "text-primary" },
            { label: "تحذيرات", value: stats.warnings, color: "text-yellow-400" },
            { label: "أخطاء", value: stats.errors, color: "text-red-500" },
          ].map((s) => (
            <div key={s.label} className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
              <p className={`text-2xl ${s.color}`}>{s.value}</p>
              <p className="text-[9px] text-muted-foreground mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* ── Filters ── */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative">
            <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              placeholder="بحث بالوصف أو الكيان..."
              className="h-8 text-xs ps-8 w-64"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <select
            value={moduleFilter}
            onChange={(e) => setModuleFilter(e.target.value as EventModule | "all")}
            className="h-8 text-xs bg-card border border-border/30 rounded-lg px-2 text-muted-foreground"
          >
            <option value="all">كل الوحدات</option>
            {Object.entries(moduleLabels).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>

          <div className="flex gap-1">
            {(["all", "info", "success", "warning", "error"] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2 py-1 rounded-lg text-[9px] border transition-all ${
                  severityFilter === sev
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border/30 text-muted-foreground hover:border-primary/30"
                }`}
              >
                {sev === "all" ? "الكل" : severityLabels[sev]}
              </button>
            ))}
          </div>

          <span className="ms-auto text-[9px] text-muted-foreground">{filteredEvents.length} حدث</span>
        </div>

        {/* ── Events Table ── */}
        <div className="rounded-xl border border-border/40 overflow-hidden bg-card/30">
          <ScrollArea dir="rtl" className="max-h-[calc(100vh-450px)]">
            <Table>
              <TableHeader className="bg-muted/20 sticky top-0 z-10">
                <TableRow className="hover:bg-transparent border-border/30">
                  <TableHead className="text-start text-[11px] w-[140px]">الوقت</TableHead>
                  <TableHead className="text-start text-[11px] w-[100px]">الوحدة</TableHead>
                  <TableHead className="text-start text-[11px] w-[60px]">المستوى</TableHead>
                  <TableHead className="text-start text-[11px]">الوصف</TableHead>
                  <TableHead className="text-start text-[11px] w-[100px]">المنفذ</TableHead>
                  <TableHead className="text-start text-[11px] w-[100px]">الكيان</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEvents.map((evt) => {
                  const ModIcon = moduleIcons[evt.module];
                  return (
                    <TableRow
                      key={evt.id}
                      className="border-border/20 hover:bg-muted/10 cursor-pointer transition-colors"
                      onClick={() => setSelectedEvent(selectedEvent?.id === evt.id ? null : evt)}
                    >
                      <TableCell className="text-[10px] text-muted-foreground font-mono" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {new Date(evt.timestamp).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                        <br />
                        <span className="text-[8px]">{new Date(evt.timestamp).toLocaleDateString("ar-SA", { month: "short", day: "numeric" })}</span>
                      </TableCell>
                      <TableCell>
                        <Badge className={`${moduleColors[evt.module]} text-[8px] h-4 gap-1`}>
                          <ModIcon className="w-2.5 h-2.5" />
                          {moduleLabels[evt.module]}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className={`text-[9px] flex items-center gap-1 ${severityColors[evt.severity]}`}>
                          {evt.severity === "error" || evt.severity === "critical" ? <AlertTriangle className="w-3 h-3" /> : null}
                          {severityLabels[evt.severity]}
                        </span>
                      </TableCell>
                      <TableCell className="text-[10px] text-foreground/80 max-w-[300px]">
                        <span className="line-clamp-2">{evt.description}</span>
                      </TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">{evt.actor}</TableCell>
                      <TableCell className="text-[10px] text-muted-foreground font-mono">
                        {evt.targetEntity ?? "—"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </ScrollArea>
        </div>

        {/* ── Expanded Detail ── */}
        {selectedEvent && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="p-4 rounded-xl border border-primary/20 bg-primary/5 space-y-2"
          >
            <div className="flex items-center justify-between">
              <p className="text-xs text-foreground">{selectedEvent.description}</p>
              <Lock className="w-3.5 h-3.5 text-primary" />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[10px]">
              <div>
                <span className="text-muted-foreground">الإجراء: </span>
                <span className="text-foreground font-mono" style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedEvent.action}</span>
              </div>
              <div>
                <span className="text-muted-foreground">المنفذ: </span>
                <span className="text-foreground">{selectedEvent.actor} ({selectedEvent.actorRole})</span>
              </div>
              {selectedEvent.ip && (
                <div>
                  <span className="text-muted-foreground">IP: </span>
                  <span className="text-foreground font-mono" style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedEvent.ip}</span>
                </div>
              )}
              {selectedEvent.metadata && Object.entries(selectedEvent.metadata).map(([k, v]) => (
                <div key={k}>
                  <span className="text-muted-foreground">{k}: </span>
                  <span className="text-foreground font-mono" style={{ direction: "ltr", unicodeBidi: "embed" }}>{v}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </TooltipProvider>
  );
}
