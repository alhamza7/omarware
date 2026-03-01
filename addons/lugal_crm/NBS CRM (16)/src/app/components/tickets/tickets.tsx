import { useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "motion/react";
import {
  Ticket, Search, Filter, Plus, Clock, AlertTriangle, ArrowUpCircle,
  User, ChevronDown, X, Check, MoreHorizontal, Eye, FileText,
  CalendarDays, Tag, ArrowLeftRight, MessageCircle, Bell, Hash,
  ChevronLeft, ChevronRight, RefreshCw, UserCog,
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
  mockTickets,
  mockFollowUps,
  ticketStatusLabels,
  ticketStatusColors,
  ticketPriorityLabels,
  ticketPriorityColors,
  defaultClassifications,
  type Ticket as TicketType,
  type TicketStatus,
  type FollowUpItem,
} from "./tk-data";

// ── Time helpers ────────────────────────────────────────

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

// ── Main Component ──────────────────────────────────────

export function Tickets() {
  const [activeTab, setActiveTab] = useState<"tickets" | "followup" | "escalation">("tickets");
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "all">("all");
  const [classFilter, setClassFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTicket, setSelectedTicket] = useState<TicketType | null>(null);
  const [showNewTicket, setShowNewTicket] = useState(false);

  // Filter tickets
  const filteredTickets = useMemo(() => {
    let tks = [...mockTickets];
    if (statusFilter !== "all") {
      tks = tks.filter((t) => t.status === statusFilter);
    }
    if (classFilter !== "all") {
      tks = tks.filter((t) => t.classification === classFilter);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      tks = tks.filter(
        (t) =>
          t.subject.includes(searchQuery) ||
          t.number.toLowerCase().includes(q) ||
          t.customerName.includes(searchQuery),
      );
    }
    return tks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [statusFilter, classFilter, searchQuery]);

  // Stats
  const stats = useMemo(() => ({
    total: mockTickets.length,
    open: mockTickets.filter((t) => t.status === "open").length,
    inProgress: mockTickets.filter((t) => t.status === "in_progress").length,
    resolved: mockTickets.filter((t) => t.status === "resolved").length,
    breached: mockTickets.filter((t) => t.slaBreach).length,
    escalated: mockTickets.filter((t) => t.escalated).length,
  }), []);

  const followUpItems = mockFollowUps;
  const escalatedTickets = mockTickets.filter((t) => t.escalated);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">

        {/* ── Header with Stats ── */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {[
            { label: "الكل", value: stats.total, color: "text-foreground" },
            { label: "مفتوح", value: stats.open, color: "text-blue-500" },
            { label: "قيد التنفيذ", value: stats.inProgress, color: "text-primary" },
            { label: "تم الحل", value: stats.resolved, color: "text-emerald-500" },
            { label: "مخالفة SLA", value: stats.breached, color: "text-red-500" },
            { label: "مصعّد", value: stats.escalated, color: "text-red-400" },
          ].map((stat) => (
            <div key={stat.label} className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
              <p className={`text-2xl ${stat.color}`}>{stat.value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* ── Tabs ── */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <div className="flex items-center justify-between">
            <TabsList className="bg-muted/20">
              <TabsTrigger value="tickets" className="text-xs gap-1.5">
                <Ticket className="w-3.5 h-3.5" />
                التذاكر
                <Badge className="bg-muted/30 text-muted-foreground text-[8px] h-4 ms-1">{mockTickets.length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="followup" className="text-xs gap-1.5">
                <Bell className="w-3.5 h-3.5" />
                المتابعات
                <Badge className="bg-primary/15 text-primary text-[8px] h-4 ms-1">{followUpItems.length}</Badge>
              </TabsTrigger>
              <TabsTrigger value="escalation" className="text-xs gap-1.5">
                <ArrowUpCircle className="w-3.5 h-3.5" />
                التصعيدات
                {escalatedTickets.length > 0 && (
                  <Badge className="bg-red-500/15 text-red-500 text-[8px] h-4 ms-1">{escalatedTickets.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
                <RefreshCw className="w-3.5 h-3.5" />
                تحديث
              </Button>
              <Button size="sm" className="h-8 text-xs gap-1.5" onClick={() => setShowNewTicket(true)}>
                <Plus className="w-3.5 h-3.5" />
                تذكرة جديدة
              </Button>
            </div>
          </div>

          {/* ── Tickets Tab ── */}
          <TabsContent value="tickets" className="mt-4">
            {/* Filters */}
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              <div className="relative">
                <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <Input
                  placeholder="بحث بالرقم أو العميل..."
                  className="h-8 text-xs ps-8 w-56"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <div className="flex gap-1.5">
                {(["all", "open", "in_progress", "resolved", "closed"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] border transition-all ${
                      statusFilter === st
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border/30 text-muted-foreground hover:border-primary/30"
                    }`}
                  >
                    {st === "all" ? "الكل" : ticketStatusLabels[st]}
                  </button>
                ))}
              </div>

              <select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                className="h-8 text-xs bg-card border border-border/30 rounded-lg px-2 text-muted-foreground"
              >
                <option value="all">كل التصنيفات</option>
                {defaultClassifications.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Tickets Table */}
            <div className="rounded-xl border border-border/40 overflow-hidden bg-card/30">
              <Table>
                <TableHeader className="bg-muted/20">
                  <TableRow className="hover:bg-transparent border-border/30">
                    <TableHead className="text-start text-[11px] w-[130px]">رقم التذكرة</TableHead>
                    <TableHead className="text-start text-[11px]">الموضوع</TableHead>
                    <TableHead className="text-start text-[11px] w-[130px]">العميل</TableHead>
                    <TableHead className="text-start text-[11px] w-[90px]">التصنيف</TableHead>
                    <TableHead className="text-start text-[11px] w-[90px]">الحالة</TableHead>
                    <TableHead className="text-start text-[11px] w-[80px]">الأولوية</TableHead>
                    <TableHead className="text-start text-[11px] w-[100px]">المُعيّن</TableHead>
                    <TableHead className="text-start text-[11px] w-[90px]">الإنشاء</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTickets.map((tk) => (
                    <TableRow
                      key={tk.id}
                      className={`border-border/20 cursor-pointer transition-colors ${
                        tk.slaBreach
                          ? "bg-red-500/[0.04] hover:bg-red-500/[0.08]"
                          : tk.escalated
                            ? "bg-red-500/[0.02] hover:bg-red-500/[0.06]"
                            : "hover:bg-muted/10"
                      }`}
                      onClick={() => setSelectedTicket(tk)}
                    >
                      <TableCell className="font-mono text-[10px] text-muted-foreground">
                        <div className="flex items-center gap-1.5">
                          <Hash className="w-3 h-3" />
                          <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{tk.number}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-foreground truncate">{tk.subject}</span>
                          {tk.slaBreach && (
                            <Tooltip>
                              <TooltipTrigger>
                                <AlertTriangle className="w-3.5 h-3.5 text-red-500 shrink-0" />
                              </TooltipTrigger>
                              <TooltipContent className="text-xs">مخالفة SLA</TooltipContent>
                            </Tooltip>
                          )}
                          {tk.followUp && (
                            <Tooltip>
                              <TooltipTrigger>
                                <Bell className="w-3 h-3 text-primary shrink-0" />
                              </TooltipTrigger>
                              <TooltipContent className="text-xs">يحتاج متابعة</TooltipContent>
                            </Tooltip>
                          )}
                          {tk.autoCreated && (
                            <Badge className="bg-violet-500/10 text-violet-400 text-[7px] h-4 border-violet-500/20 shrink-0">
                              تلقائي
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs">{tk.customerName}</TableCell>
                      <TableCell>
                        <Badge className="bg-muted/30 text-muted-foreground text-[8px] h-4">
                          {tk.classification}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={`${ticketStatusColors[tk.status]} text-[8px] h-4`}>
                          {ticketStatusLabels[tk.status]}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={`${ticketPriorityColors[tk.priority]} text-[8px] h-4`}>
                          {ticketPriorityLabels[tk.priority]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">
                        {tk.assignedAgentName || "—"}
                      </TableCell>
                      <TableCell className="text-[10px] text-muted-foreground">
                        {timeAgo(tk.createdAt)}
                      </TableCell>
                    </TableRow>
                  ))}

                  {filteredTickets.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-12">
                        <Ticket className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                        <p className="text-xs text-muted-foreground">لا توجد تذاكر تطابق البحث</p>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </TabsContent>

          {/* ── Follow-up Tab ── */}
          <TabsContent value="followup" className="mt-4">
            <div className="space-y-3">
              {followUpItems.map((fu) => (
                <FollowUpCard key={fu.id} item={fu} />
              ))}
              {followUpItems.length === 0 && (
                <div className="text-center py-12">
                  <Bell className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                  <p className="text-xs text-muted-foreground">لا توجد متابعات حالياً</p>
                </div>
              )}
            </div>
          </TabsContent>

          {/* ── Escalation Tab ── */}
          <TabsContent value="escalation" className="mt-4">
            <div className="space-y-3">
              {escalatedTickets.map((tk) => (
                <div
                  key={tk.id}
                  className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 flex items-start gap-4"
                >
                  <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-foreground">{tk.subject}</span>
                      <Badge className={`${ticketPriorityColors[tk.priority]} text-[8px] h-4`}>
                        {ticketPriorityLabels[tk.priority]}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-[10px] text-muted-foreground">
                      <span>{tk.customerName}</span>
                      <span>•</span>
                      <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{tk.number}</span>
                      <span>•</span>
                      <span>مصعّد إلى: {tk.escalatedTo}</span>
                    </div>
                    <p className="text-[10px] text-muted-foreground/70 mt-1">{tk.description}</p>
                  </div>
                  <div className="shrink-0 flex flex-col items-end gap-1">
                    <Badge className="bg-red-500/15 text-red-500 text-[8px] h-4">{ticketStatusLabels[tk.status]}</Badge>
                    <span className="text-[9px] text-red-400">منذ {timeAgo(tk.createdAt)}</span>
                    <Button size="sm" variant="outline" className="h-6 text-[9px] mt-1 border-red-500/20 text-red-400 hover:bg-red-500/10">
                      تولي
                    </Button>
                  </div>
                </div>
              ))}
              {escalatedTickets.length === 0 && (
                <div className="text-center py-12">
                  <ArrowUpCircle className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                  <p className="text-xs text-muted-foreground">لا توجد تصعيدات حالياً</p>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* ── Ticket Detail Drawer ── */}
        {createPortal(
          <AnimatePresence>
            {selectedTicket && (
              <TicketDetail ticket={selectedTicket} onClose={() => setSelectedTicket(null)} />
            )}
          </AnimatePresence>,
          document.body
        )}

        {/* ── New Ticket Drawer ── */}
        {createPortal(
          <AnimatePresence>
            {showNewTicket && (
              <NewTicketDrawer onClose={() => setShowNewTicket(false)} />
            )}
          </AnimatePresence>,
          document.body
        )}
      </div>
    </TooltipProvider>
  );
}

// ── Follow-up Card ─────────────────────────────────────

function FollowUpCard({ item }: { item: FollowUpItem }) {
  const typeLabels: Record<string, string> = {
    ticket: "تذكرة",
    customer: "عميل",
    product: "منتج",
    credit: "ائتمان",
  };
  const typeColors: Record<string, string> = {
    ticket: "bg-blue-500/10 text-blue-400",
    customer: "bg-emerald-500/10 text-emerald-400",
    product: "bg-violet-500/10 text-violet-400",
    credit: "bg-red-500/10 text-red-400",
  };

  const isOverdue = new Date(item.dueDate).getTime() < Date.now();

  return (
    <div className={`p-4 rounded-xl border ${
      isOverdue ? "border-red-500/20 bg-red-500/5" : "border-border/30 bg-card/30"
    } flex items-start gap-3`}>
      <div className="flex flex-col items-center gap-1 shrink-0">
        <Badge className={`${typeColors[item.type]} text-[8px] h-4`}>{typeLabels[item.type]}</Badge>
        {item.escalated && <AlertTriangle className="w-3.5 h-3.5 text-red-500" />}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-foreground">{item.subject}</span>
          {isOverdue && (
            <Badge className="bg-red-500/15 text-red-500 text-[7px] h-3.5">متأخر</Badge>
          )}
        </div>
        <p className="text-[10px] text-muted-foreground mt-0.5">{item.details}</p>
        <div className="flex items-center gap-3 mt-1.5 text-[9px] text-muted-foreground">
          <span className="flex items-center gap-0.5">
            <User className="w-3 h-3" /> {item.linkedName}
          </span>
          <span>•</span>
          <span className="flex items-center gap-0.5">
            <CalendarDays className="w-3 h-3" /> {formatDate(item.dueDate)}
          </span>
          <span>•</span>
          <span>مُعيّن: {item.assignedAgentName}</span>
        </div>
      </div>

      <div className="shrink-0 flex flex-col gap-1">
        <Badge className={`text-[8px] h-4 ${
          item.status === "resolved" ? "bg-emerald-500/15 text-emerald-500" :
          item.status === "in_progress" ? "bg-primary/15 text-primary" :
          "bg-blue-500/15 text-blue-400"
        }`}>
          {item.status === "resolved" ? "تم" : item.status === "in_progress" ? "جاري" : "في الانتظار"}
        </Badge>
        {item.reminders.length > 0 && (
          <span className="text-[8px] text-muted-foreground flex items-center gap-0.5">
            <Bell className="w-2.5 h-2.5" /> {item.reminders.length} تذكير
          </span>
        )}
      </div>
    </div>
  );
}

// ── Ticket Detail Sheet ────────────────────────────────

function TicketDetail({ ticket, onClose }: { ticket: TicketType; onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex justify-start"
      dir="rtl"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/40" />
      <motion.div
        initial={{ x: 400 }}
        animate={{ x: 0 }}
        exit={{ x: 400 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="relative w-[480px] h-full bg-card border-s border-border/40 shadow-2xl flex flex-col overflow-hidden ms-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="shrink-0 p-4 border-b border-border/30 bg-card/80">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                {ticket.number}
              </span>
              <Badge className={`${ticketStatusColors[ticket.status]} text-[8px] h-4`}>
                {ticketStatusLabels[ticket.status]}
              </Badge>
              <Badge className={`${ticketPriorityColors[ticket.priority]} text-[8px] h-4`}>
                {ticketPriorityLabels[ticket.priority]}
              </Badge>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <h3 className="text-sm text-foreground">{ticket.subject}</h3>
          <p className="text-[10px] text-muted-foreground mt-1">{ticket.description}</p>
        </div>

        {/* Metadata */}
        <div className="shrink-0 p-4 border-b border-border/20 grid grid-cols-2 gap-3">
          {[
            { label: "العميل", value: ticket.customerName },
            { label: "التصنيف", value: ticket.classification },
            { label: "القناة", value: ticket.channel },
            { label: "المُعيّن", value: ticket.assignedAgentName || "غير معيّن" },
            { label: "الإنشاء", value: formatDate(ticket.createdAt) },
            { label: "SLA", value: ticket.slaBreach ? "⚠️ مخالفة" : formatDate(ticket.slaDeadline) },
          ].map((item) => (
            <div key={item.label}>
              <p className="text-[9px] text-muted-foreground">{item.label}</p>
              <p className="text-xs text-foreground mt-0.5">{item.value}</p>
            </div>
          ))}
        </div>

        {/* History */}
        <ScrollArea dir="rtl" className="flex-1 min-h-0">
          <div className="p-4">
            <h4 className="text-xs text-foreground mb-3 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-primary" />
              سجل التحديثات
            </h4>
            <div className="space-y-3 relative">
              {/* Timeline line */}
              <div className="absolute top-0 bottom-0 start-[7px] w-px bg-border/30" />

              {ticket.history.map((entry, i) => (
                <div key={entry.id} className="flex items-start gap-3 relative">
                  <div className={`w-3.5 h-3.5 rounded-full shrink-0 z-10 ${
                    i === 0 ? "bg-primary" : "bg-border/50"
                  }`} />
                  <div className="flex-1 pb-3">
                    <p className="text-[10px] text-foreground">{entry.action}</p>
                    <div className="flex items-center gap-2 mt-0.5 text-[9px] text-muted-foreground">
                      <span>{entry.actor}</span>
                      <span>•</span>
                      <span>{formatDate(entry.timestamp)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Transfers */}
            {ticket.transferHistory.length > 0 && (
              <>
                <h4 className="text-xs text-foreground mb-3 mt-4 flex items-center gap-1.5">
                  <ArrowLeftRight className="w-3.5 h-3.5 text-primary" />
                  عمليات النقل
                </h4>
                <div className="space-y-2">
                  {ticket.transferHistory.map((tr) => (
                    <div key={tr.id} className="p-3 rounded-lg border border-border/30 bg-muted/10">
                      <div className="flex items-center gap-2 text-[10px]">
                        <span className="text-muted-foreground">من</span>
                        <span className="text-foreground">{tr.from}</span>
                        <ChevronLeft className="w-3 h-3 text-muted-foreground" />
                        <span className="text-foreground">{tr.to}</span>
                      </div>
                      <p className="text-[9px] text-muted-foreground mt-1">السبب: {tr.reason}</p>
                      <Badge className={`text-[8px] h-3.5 mt-1 ${
                        tr.status === "accepted" ? "bg-emerald-500/10 text-emerald-400" :
                        tr.status === "rejected" ? "bg-red-500/10 text-red-400" :
                        "bg-primary/10 text-primary"
                      }`}>
                        {tr.status === "accepted" ? "مقبول" : tr.status === "rejected" ? "مرفوض" : "في الانتظار"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </ScrollArea>

        {/* Footer actions */}
        <div className="shrink-0 p-3 border-t border-border/30 flex items-center gap-2">
          <Button size="sm" className="h-8 text-xs flex-1 gap-1.5">
            <Check className="w-3.5 h-3.5" />
            تحديث الحالة
          </Button>
          <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
            <ArrowLeftRight className="w-3.5 h-3.5" />
            نقل
          </Button>
          <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
            <ArrowUpCircle className="w-3.5 h-3.5" />
            تصعيد
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ── New Ticket Drawer ───────────────────────────────────

const mockAgents = [
  { id: "emp-01", name: "سعود المالكي" },
  { id: "emp-02", name: "نورة الشمري" },
  { id: "emp-03", name: "فهد العتيبي" },
  { id: "emp-04", name: "ريم القحطاني" },
];

const channelOptions = [
  { value: "whatsapp", label: "واتساب" },
  { value: "instagram", label: "انستقرام" },
  { value: "phone", label: "هاتف" },
  { value: "email", label: "بريد إلكتروني" },
  { value: "website", label: "الموقع" },
  { value: "walk-in", label: "زيارة مباشرة" },
];

function NewTicketDrawer({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({
    customerName: "",
    subject: "",
    description: "",
    classification: "",
    priority: "normal" as "low" | "normal" | "high" | "urgent",
    channel: "",
    assignedAgent: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const canSubmit =
    form.customerName.trim() &&
    form.subject.trim() &&
    form.classification &&
    form.channel;

  const handleSubmit = () => {
    if (!canSubmit) return;
    setSubmitted(true);
    setTimeout(onClose, 1200);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex justify-end"
      dir="rtl"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/40" />
      <motion.div
        initial={{ x: -480 }}
        animate={{ x: 0 }}
        exit={{ x: -480 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="relative w-[480px] h-full bg-card border-e border-border/40 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="shrink-0 p-4 border-b border-border/30 bg-card/80">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Plus className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="text-sm text-foreground">تذكرة جديدة</h3>
                <p className="text-[9px] text-muted-foreground">سيتم إنشاء رقم تلقائي</p>
              </div>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Success State */}
        {submitted ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              className="w-16 h-16 rounded-full bg-emerald-500/15 flex items-center justify-center"
            >
              <Check className="w-8 h-8 text-emerald-500" />
            </motion.div>
            <div className="text-center">
              <p className="text-sm text-foreground">تم إنشاء التذكرة بنجاح</p>
              <p className="text-[10px] text-muted-foreground mt-1">
                TK-2026-0048 — {form.subject}
              </p>
            </div>
          </div>
        ) : (
          /* Form */
          <ScrollArea dir="rtl" className="flex-1 min-h-0">
            <div className="p-4 space-y-5">

              {/* ── Customer Info ── */}
              <div>
                <p className="text-[10px] text-primary mb-2.5 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" />
                  معلومات العميل
                </p>
                <div className="space-y-2.5">
                  <div>
                    <label className="text-[10px] text-muted-foreground mb-1 block">اسم العميل *</label>
                    <Input
                      placeholder="أدخل اسم العميل..."
                      className="h-8 text-xs"
                      value={form.customerName}
                      onChange={(e) => update("customerName", e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-muted-foreground mb-1 block">القناة *</label>
                    <select
                      value={form.channel}
                      onChange={(e) => update("channel", e.target.value)}
                      className="w-full h-8 text-xs bg-input-background border border-border/30 rounded-lg px-2.5 text-foreground"
                    >
                      <option value="">اختر القناة...</option>
                      {channelOptions.map((ch) => (
                        <option key={ch.value} value={ch.value}>{ch.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="h-px bg-border/20" />

              {/* ── Ticket Details ── */}
              <div>
                <p className="text-[10px] text-primary mb-2.5 flex items-center gap-1.5">
                  <Ticket className="w-3.5 h-3.5" />
                  تفاصيل التذكرة
                </p>
                <div className="space-y-2.5">
                  <div>
                    <label className="text-[10px] text-muted-foreground mb-1 block">الموضوع *</label>
                    <Input
                      placeholder="موضوع التذكرة..."
                      className="h-8 text-xs"
                      value={form.subject}
                      onChange={(e) => update("subject", e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-muted-foreground mb-1 block">الوصف</label>
                    <textarea
                      placeholder="وصف تفصيلي للمشكلة أو الطلب..."
                      className="w-full h-20 text-xs bg-input-background border border-border/30 rounded-lg px-2.5 py-2 text-foreground resize-none placeholder:text-muted-foreground/50"
                      value={form.description}
                      onChange={(e) => update("description", e.target.value)}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2.5">
                    <div>
                      <label className="text-[10px] text-muted-foreground mb-1 block">التصنيف *</label>
                      <select
                        value={form.classification}
                        onChange={(e) => update("classification", e.target.value)}
                        className="w-full h-8 text-xs bg-input-background border border-border/30 rounded-lg px-2.5 text-foreground"
                      >
                        <option value="">اختر...</option>
                        {defaultClassifications.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground mb-1 block">الأولوية</label>
                      <div className="flex gap-1">
                        {(["low", "normal", "high", "urgent"] as const).map((p) => (
                          <button
                            key={p}
                            onClick={() => update("priority", p)}
                            className={`flex-1 h-8 rounded-lg text-[9px] border transition-all ${
                              form.priority === p
                                ? `${ticketPriorityColors[p]} border-current`
                                : "border-border/30 text-muted-foreground hover:border-primary/30"
                            }`}
                          >
                            {ticketPriorityLabels[p]}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="h-px bg-border/20" />

              {/* ── Assignment ── */}
              <div>
                <p className="text-[10px] text-primary mb-2.5 flex items-center gap-1.5">
                  <UserCog className="w-3.5 h-3.5" />
                  التعيين
                </p>
                <div>
                  <label className="text-[10px] text-muted-foreground mb-1 block">تعيين إلى موظف</label>
                  <select
                    value={form.assignedAgent}
                    onChange={(e) => update("assignedAgent", e.target.value)}
                    className="w-full h-8 text-xs bg-input-background border border-border/30 rounded-lg px-2.5 text-foreground"
                  >
                    <option value="">تعيين تلقائي</option>
                    {mockAgents.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                  <p className="text-[9px] text-muted-foreground/60 mt-1">
                    اترك فارغاً للتعيين التلقائي حسب قواعد التوزيع
                  </p>
                </div>
              </div>
            </div>
          </ScrollArea>
        )}

        {/* Footer */}
        {!submitted && (
          <div className="shrink-0 p-3 border-t border-border/30 flex items-center gap-2">
            <Button
              size="sm"
              className="h-9 text-xs flex-1 gap-1.5"
              disabled={!canSubmit}
              onClick={handleSubmit}
            >
              <Check className="w-3.5 h-3.5" />
              إنشاء التذكرة
            </Button>
            <Button variant="outline" size="sm" className="h-9 text-xs" onClick={onClose}>
              إلغاء
            </Button>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}