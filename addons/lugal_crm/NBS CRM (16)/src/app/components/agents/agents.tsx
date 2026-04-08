import { useState, useMemo } from "react";
import { motion } from "motion/react";
import {
  Users, Search, Phone, MessageCircle, Clock, Activity, Star, Eye,
  Send, ChevronDown, BarChart3, Headset, Check, X, Circle, Shield,
  Zap, UserCheck, ListTodo, Wifi, WifiOff,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Avatar, AvatarFallback } from "../ui/avatar";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";
import { mockAgents, type OCAgent, type AgentPresence, type AgentActivity } from "../omni-channel/oc-data";

// ── Presence / Activity helpers ─────────────────────────

const presenceLabels: Record<AgentPresence, string> = {
  available: "متاح",
  busy: "مشغول",
  "on-call": "في مكالمة",
  offline: "غير متصل",
  "on-leave": "في إجازة",
};

const presenceColors: Record<AgentPresence, string> = {
  available: "bg-emerald-500",
  busy: "bg-red-500",
  "on-call": "bg-primary",
  offline: "bg-muted-foreground/50",
  "on-leave": "bg-violet-500",
};

const presenceDotColors: Record<AgentPresence, string> = {
  available: "text-emerald-500",
  busy: "text-red-500",
  "on-call": "text-primary",
  offline: "text-muted-foreground/50",
  "on-leave": "text-violet-500",
};

const activityLabels: Record<AgentActivity, string> = {
  idle: "خامل",
  "in-chat": "في محادثة",
  "on-call": "في مكالمة",
  writing: "يكتب",
  reviewing: "مراجعة",
};

// ── Extended mock employees (adding to OCAgent) ─────────

interface Employee extends OCAgent {
  position: string;
  department: string;
  email: string;
  joinDate: string;
  supervisor: string | null;
  evaluationScore?: number; // 0-5
  currentTab?: string;
}

const employees: Employee[] = [
  { ...mockAgents[0], position: "موظف مبيعات", department: "المبيعات", email: "saud@nooralnibras.com", joinDate: "2024-06-15", supervisor: "emp-04", evaluationScore: 4.5, currentTab: "omni-channel" },
  { ...mockAgents[1], position: "موظفة دعم عملاء", department: "خدمة العملاء", email: "mona@nooralnibras.com", joinDate: "2024-03-01", supervisor: "emp-04", evaluationScore: 4.2, currentTab: "tickets" },
  { ...mockAgents[2], position: "موظف تواصل اجتماعي", department: "التسويق", email: "abdullah@nooralnibras.com", joinDate: "2025-01-10", supervisor: "emp-04", evaluationScore: 3.8, currentTab: "omni-channel" },
  { ...mockAgents[3], position: "مشرف مركز الاتصال", department: "العمليات", email: "fahad@nooralnibras.com", joinDate: "2023-09-20", supervisor: null, evaluationScore: 4.8, currentTab: "admin-dashboard" },
  {
    id: "emp-05", name: "ريم الحسين", role: "agent", presence: "offline", activity: "idle",
    activeConversations: 0, maxCapacity: 5, skills: ["sales", "general"],
    channels: ["whatsapp", "sms"], totalCalls: 67, totalChats: 145,
    avgHandleTime: 4.5, todayReplied: 0, todayMissed: 0,
    position: "موظفة مبيعات", department: "المبيعات", email: "reem@nooralnibras.com",
    joinDate: "2025-06-01", supervisor: "emp-04", evaluationScore: 3.5,
  },
  {
    id: "emp-06", name: "عمر بن سلمان", role: "agent", presence: "on-leave", activity: "idle",
    activeConversations: 0, maxCapacity: 5, skills: ["vip", "complaints"],
    channels: ["whatsapp", "telegram", "instagram"], totalCalls: 210, totalChats: 380,
    avgHandleTime: 5.2, todayReplied: 0, todayMissed: 0,
    position: "موظف VIP", department: "VIP", email: "omar@nooralnibras.com",
    joinDate: "2024-01-15", supervisor: "emp-04", evaluationScore: 4.7, currentTab: undefined,
  },
];

// ── Main Component ──────────────────────────────────────

export function Agents() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterPresence, setFilterPresence] = useState<AgentPresence | "all">("all");
  const [selectedAgent, setSelectedAgent] = useState<Employee | null>(null);

  const filteredEmps = useMemo(() => {
    let emps = [...employees];
    if (filterPresence !== "all") {
      emps = emps.filter((e) => e.presence === filterPresence);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      emps = emps.filter(
        (e) => e.name.includes(searchQuery) || e.email.toLowerCase().includes(q),
      );
    }
    // Online first
    const order: AgentPresence[] = ["available", "busy", "on-call", "on-leave", "offline"];
    return emps.sort((a, b) => order.indexOf(a.presence) - order.indexOf(b.presence));
  }, [searchQuery, filterPresence]);

  const stats = useMemo(() => ({
    total: employees.length,
    available: employees.filter((e) => e.presence === "available").length,
    busy: employees.filter((e) => e.presence === "busy" || e.presence === "on-call").length,
    offline: employees.filter((e) => e.presence === "offline" || e.presence === "on-leave").length,
  }), []);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">

        {/* ── Live Status Bar ── */}
        <div className="flex items-center gap-4 p-4 rounded-xl border border-border/30 bg-card/30">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-foreground">الحالة المباشرة</span>
          </div>
          <div className="flex gap-4 ms-4 text-[10px] text-muted-foreground">
            <span>{stats.available} متاح</span>
            <span className="text-border/60">|</span>
            <span>{stats.busy} مشغول</span>
            <span className="text-border/60">|</span>
            <span>{stats.offline} غير متصل</span>
            <span className="text-border/60">|</span>
            <span>{stats.total} إجمالي</span>
          </div>
        </div>

        {/* ── Filters ── */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input
              placeholder="بحث بالاسم أو البريد..."
              className="h-8 text-xs ps-8 w-56"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex gap-1.5">
            {(["all", "available", "busy", "on-call", "offline", "on-leave"] as const).map((p) => (
              <button
                key={p}
                onClick={() => setFilterPresence(p)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] border transition-all ${
                  filterPresence === p
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border/30 text-muted-foreground hover:border-primary/30"
                }`}
              >
                {p !== "all" && <Circle className={`w-2 h-2 fill-current ${presenceDotColors[p]}`} />}
                {p === "all" ? "الكل" : presenceLabels[p]}
              </button>
            ))}
          </div>
        </div>

        {/* ── Agent Cards Grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredEmps.map((emp) => (
            <AgentCard
              key={emp.id}
              emp={emp}
              isSelected={selectedAgent?.id === emp.id}
              onClick={() => setSelectedAgent(selectedAgent?.id === emp.id ? null : emp)}
            />
          ))}
        </div>

        {filteredEmps.length === 0 && (
          <div className="text-center py-12">
            <Users className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
            <p className="text-xs text-muted-foreground">لا يوجد موظفون مطابقون</p>
          </div>
        )}

        {/* ── Selected Agent Detail ── */}
        {selectedAgent && (
          <AgentDetail emp={selectedAgent} onClose={() => setSelectedAgent(null)} />
        )}
      </div>
    </TooltipProvider>
  );
}

// ── Agent Card ──────────────────────────────────────────

function AgentCard({
  emp,
  isSelected,
  onClick,
}: {
  emp: Employee;
  isSelected: boolean;
  onClick: () => void;
}) {
  const isOnline = emp.presence === "available" || emp.presence === "busy" || emp.presence === "on-call";

  return (
    <motion.button
      onClick={onClick}
      className={`w-full text-start p-4 rounded-xl border transition-all ${
        isSelected
          ? "border-primary bg-primary/5 dark:bg-primary/10 shadow-sm shadow-primary/10"
          : "border-border/30 bg-card/30 hover:border-primary/30 hover:bg-card/50"
      }`}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex items-start gap-3">
        {/* Avatar with presence */}
        <div className="relative shrink-0">
          <Avatar className="h-11 w-11">
            <AvatarFallback className="bg-primary/10 text-primary text-sm">
              {emp.name.slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <span className={`absolute bottom-0 end-0 w-3 h-3 rounded-full border-2 border-card ${presenceColors[emp.presence]}`} />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-foreground truncate">{emp.name}</span>
            {emp.role === "supervisor" && (
              <Shield className="w-3.5 h-3.5 text-primary shrink-0" />
            )}
          </div>
          <p className="text-[10px] text-muted-foreground">{emp.position}</p>

          {/* Live status */}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <Badge className={`text-[8px] h-4 ${
              emp.presence === "available" ? "bg-emerald-500/10 text-emerald-400" :
              emp.presence === "busy" ? "bg-red-500/10 text-red-400" :
              emp.presence === "on-call" ? "bg-primary/10 text-primary" :
              emp.presence === "on-leave" ? "bg-violet-500/10 text-violet-400" :
              "bg-muted/30 text-muted-foreground"
            }`}>
              {presenceLabels[emp.presence]}
            </Badge>
            {isOnline && emp.activity !== "idle" && (
              <Badge className="bg-muted/20 text-muted-foreground text-[8px] h-4">
                {activityLabels[emp.activity]}
              </Badge>
            )}
            {isOnline && emp.currentTab && (
              <span className="text-[8px] text-muted-foreground/60 flex items-center gap-0.5">
                <Eye className="w-2.5 h-2.5" /> {emp.currentTab}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-2 mt-3 pt-3 border-t border-border/20">
        {[
          { icon: Phone, label: "مكالمات", value: emp.totalCalls },
          { icon: MessageCircle, label: "محادثات", value: emp.totalChats },
          { icon: Clock, label: "معدل", value: `${emp.avgHandleTime}د` },
          { icon: Activity, label: "اليوم", value: emp.todayReplied },
        ].map((stat) => (
          <div key={stat.label} className="text-center">
            <stat.icon className="w-3 h-3 text-muted-foreground mx-auto mb-0.5" />
            <p className="text-[10px] text-foreground">{stat.value}</p>
            <p className="text-[7px] text-muted-foreground">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Capacity bar */}
      {isOnline && (
        <div className="mt-2">
          <div className="flex items-center justify-between text-[8px] text-muted-foreground mb-0.5">
            <span>السعة</span>
            <span>{emp.activeConversations}/{emp.maxCapacity}</span>
          </div>
          <div className="h-1.5 rounded-full bg-muted/30 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                emp.activeConversations / emp.maxCapacity > 0.8 ? "bg-red-500" :
                emp.activeConversations / emp.maxCapacity > 0.5 ? "bg-primary" :
                "bg-emerald-500"
              }`}
              style={{ width: `${(emp.activeConversations / emp.maxCapacity) * 100}%` }}
            />
          </div>
        </div>
      )}
    </motion.button>
  );
}

// ── Agent Detail Panel ──────────────────────────────────

function AgentDetail({ emp, onClose }: { emp: Employee; onClose: () => void }) {
  const renderStars = (score: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`w-3 h-3 ${i < Math.floor(score) ? "text-primary fill-primary" : "text-muted-foreground/30"}`}
      />
    ));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-5 rounded-xl border border-primary/20 bg-card/50 space-y-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Avatar className="h-14 w-14">
              <AvatarFallback className="bg-primary/10 text-primary">{emp.name.slice(0, 2)}</AvatarFallback>
            </Avatar>
            <span className={`absolute bottom-0.5 end-0.5 w-3.5 h-3.5 rounded-full border-2 border-card ${presenceColors[emp.presence]}`} />
          </div>
          <div>
            <h3 className="text-foreground flex items-center gap-2">
              {emp.name}
              {emp.role === "supervisor" && <Shield className="w-4 h-4 text-primary" />}
            </h3>
            <p className="text-xs text-muted-foreground">{emp.position} — {emp.department}</p>
            <p className="text-[10px] text-muted-foreground/60" style={{ direction: "ltr", unicodeBidi: "embed" }}>{emp.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
                <MessageCircle className="w-3.5 h-3.5" />
                رسالة
              </Button>
            </TooltipTrigger>
            <TooltipContent className="text-xs">إرسال رسالة مباشرة</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
                <ListTodo className="w-3.5 h-3.5" />
                مهمة
              </Button>
            </TooltipTrigger>
            <TooltipContent className="text-xs">تعيين مهمة CRM</TooltipContent>
          </Tooltip>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Detail grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <DetailBox label="تاريخ الانضمام" value={emp.joinDate} />
        <DetailBox label="المشرف" value={emp.supervisor ? employees.find((e) => e.id === emp.supervisor)?.name || "—" : "لا يوجد"} />
        <DetailBox label="التقييم" value={
          <div className="flex items-center gap-1 mt-0.5">
            {emp.evaluationScore ? renderStars(emp.evaluationScore) : "—"}
            {emp.evaluationScore && <span className="text-[9px] text-muted-foreground ms-1">{emp.evaluationScore}</span>}
          </div>
        } />
        <DetailBox label="المهارات" value={
          <div className="flex flex-wrap gap-1 mt-0.5">
            {emp.skills.map((s) => (
              <span key={s} className="text-[7px] px-1.5 py-0.5 rounded bg-muted/30 text-muted-foreground">{s}</span>
            ))}
          </div>
        } />
      </div>

      {/* Performance stats */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {[
          { label: "مكالمات إجمالية", value: emp.totalCalls, icon: Phone },
          { label: "محادثات إجمالية", value: emp.totalChats, icon: MessageCircle },
          { label: "معدل التعامل", value: `${emp.avgHandleTime} د`, icon: Clock },
          { label: "ردود اليوم", value: emp.todayReplied, icon: Check },
          { label: "فائت اليوم", value: emp.todayMissed, icon: X },
          { label: "السعة", value: `${emp.activeConversations}/${emp.maxCapacity}`, icon: Activity },
        ].map((stat) => (
          <div key={stat.label} className="p-3 rounded-lg border border-border/20 bg-muted/10 text-center">
            <stat.icon className="w-4 h-4 text-primary mx-auto mb-1" />
            <p className="text-foreground text-sm">{stat.value}</p>
            <p className="text-[8px] text-muted-foreground">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Channels */}
      <div>
        <p className="text-[10px] text-muted-foreground mb-2">القنوات المُعيّنة</p>
        <div className="flex gap-1.5 flex-wrap">
          {emp.channels.map((ch) => (
            <Badge key={ch} className="bg-muted/20 text-muted-foreground text-[9px] h-5">
              {ch}
            </Badge>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

// ── Detail Box ──────────────────────────────────────────

function DetailBox({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-[9px] text-muted-foreground">{label}</p>
      {typeof value === "string" ? (
        <p className="text-xs text-foreground mt-0.5">{value}</p>
      ) : (
        value
      )}
    </div>
  );
}