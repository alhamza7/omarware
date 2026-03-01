import {
  Bell,
  CheckCircle2,
  Circle,
  Clock,
  Mail,
  MessageSquare,
  Phone,
  User,
  Star,
  Send,
  ThumbsUp,
  AlertTriangle,
  Ticket,
  ListTodo,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { Button } from "../ui/button";
import type { DashboardStats as ApiStats } from "../../../features/dashboard/types";

// ── RecentInteractions ───────────────────────────────────────────────────

interface Interaction {
  id:       number;
  type:     "call" | "email" | "meeting";
  customer: string;
  note:     string;
  time:     string;
  status:   string;
}

const fallbackInteractions: Interaction[] = [
  { id: 1, type: "call",    customer: "—", note: "—", time: "—", status: "pending"  },
  { id: 2, type: "email",   customer: "—", note: "—", time: "—", status: "pending"  },
  { id: 3, type: "meeting", customer: "—", note: "—", time: "—", status: "upcoming" },
];

interface RecentInteractionsProps {
  /** Pass real interaction data when available */
  interactions?: Interaction[];
}

/** Last few customer interactions (calls, emails, meetings) */
export function RecentInteractions({ interactions = fallbackInteractions }: RecentInteractionsProps) {
  return (
    <Card className="col-span-1 h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-primary" />
          التفاعلات الأخيرة
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {interactions.map((interaction) => (
          <div
            key={interaction.id}
            className="flex items-start gap-3 p-3 rounded-lg bg-secondary/30 border border-border/50 hover:bg-secondary/50 transition-colors"
          >
            <div
              className={`p-2 rounded-full ${interaction.type === "call" ? "bg-blue-500/10 text-blue-500" : interaction.type === "email" ? "bg-purple-500/10 text-purple-500" : "bg-primary/10 text-primary"}`}
            >
              {interaction.type === "call"    && <Phone   className="w-4 h-4" />}
              {interaction.type === "email"   && <Mail    className="w-4 h-4" />}
              {interaction.type === "meeting" && <User    className="w-4 h-4" />}
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-start">
                <h4 className="text-sm font-semibold">{interaction.customer}</h4>
                <span className="text-xs text-muted-foreground">{interaction.time}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{interaction.note}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ── TaskTracker ──────────────────────────────────────────────────────────

interface Task {
  id:        number;
  text:      string;
  due:       string;
  completed: boolean;
}

const fallbackTasks: Task[] = [
  { id: 1, text: "إعداد التقرير الشهري",  due: "اليوم",   completed: false },
  { id: 2, text: "متابعة عميل VIP",       due: "غداً",    completed: true  },
  { id: 3, text: "تحديث قائمة الأسعار",  due: "الخميس",  completed: false },
];

interface TaskTrackerProps {
  tasks?:     Task[];
  overdueCt?: number;
}

/** Daily task tracker — shows overdue count badge when stats are available */
export function TaskTracker({ tasks = fallbackTasks, overdueCt }: TaskTrackerProps) {
  return (
    <Card className="col-span-1 h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-500" />
          المهام اليومية
          {overdueCt != null && overdueCt > 0 && (
            <span className="ms-auto text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 font-medium">
              {overdueCt} متأخرة
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {tasks.map((task) => (
          <div
            key={task.id}
            className="flex items-center gap-3 p-2 group cursor-pointer hover:bg-secondary/50 rounded-lg transition-colors"
          >
            {task.completed
              ? <CheckCircle2 className="w-5 h-5 text-green-500/80" />
              : <Circle className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />}
            <span className={`text-sm flex-1 ${task.completed ? "line-through text-muted-foreground" : ""}`}>
              {task.text}
            </span>
            <span className="text-xs px-2 py-1 rounded-full bg-secondary text-muted-foreground">
              {task.due}
            </span>
          </div>
        ))}
        <Button variant="ghost" size="sm" className="w-full mt-2 text-primary hover:text-primary/80 border border-dashed border-primary/30">
          + إضافة مهمة جديدة
        </Button>
      </CardContent>
    </Card>
  );
}

// ── AlertsWidget ─────────────────────────────────────────────────────────

interface AlertsWidgetProps {
  /** Pass real dashboardStats to show live alert counts */
  stats?: ApiStats | null;
}

/** Shows high-priority alerts derived from real API stats when provided */
export function AlertsWidget({ stats }: AlertsWidgetProps) {
  /** Build dynamic alerts from real stats, fall back to placeholder */
  const alerts: { id: number; text: string; urgency: "high" | "medium"; detail: string }[] = stats
    ? [
        ...(stats.tickets.high_priority > 0
          ? [{ id: 1, text: `${stats.tickets.high_priority} تذاكر ذات أولوية عالية`, urgency: "high" as const, detail: `${stats.tickets.open} مفتوحة إجمالاً` }]
          : []),
        ...(stats.tasks.overdue > 0
          ? [{ id: 2, text: `${stats.tasks.overdue} مهام متأخرة`, urgency: "high" as const, detail: "يرجى المراجعة الفورية" }]
          : []),
        ...(stats.messages.sla_breached > 0
          ? [{ id: 3, text: `${stats.messages.sla_breached} رسائل تجاوزت SLA`, urgency: "medium" as const, detail: `${stats.messages.pending_reply} تنتظر الرد` }]
          : []),
        ...(stats.calls.missed > 0
          ? [{ id: 4, text: `${stats.calls.missed} مكالمة فائتة`, urgency: "medium" as const, detail: "تحتاج إلى رد عاجل" }]
          : []),
      ]
    : [
        { id: 1, text: "تجديد عقد المورد الرئيسي", urgency: "high"   as const, detail: "بعد يومين" },
        { id: 2, text: "اجتماع الفريق الأسبوعي",   urgency: "medium" as const, detail: "اليوم 4:00 م" },
      ];

  return (
    <Card className="col-span-1 bg-gradient-to-br from-destructive/10 via-card to-card border-destructive/50 shadow-lg shadow-destructive/10 relative overflow-hidden group hover:border-destructive/80 transition-colors duration-300">
      <div className="absolute top-0 end-0 w-32 h-32 bg-destructive/20 blur-3xl rounded-full -me-16 -mt-16 animate-pulse" />

      <CardHeader className="pb-2 relative z-10">
        <CardTitle className="flex items-center gap-2 text-base text-destructive font-bold">
          <div className="relative">
            <Bell className="w-5 h-5" />
            {alerts.length > 0 && (
              <>
                <span className="absolute -top-0.5 -end-0.5 w-2.5 h-2.5 bg-destructive rounded-full animate-ping opacity-75" />
                <span className="absolute -top-0.5 -end-0.5 w-2.5 h-2.5 bg-destructive rounded-full border-2 border-card" />
              </>
            )}
          </div>
          تنبيهات هامة
          {stats && (
            <span className="ms-auto text-xs font-normal text-muted-foreground">
              مباشر
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 relative z-10">
        {alerts.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            لا توجد تنبيهات حالياً
          </p>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className="flex items-start gap-3 text-sm p-3 rounded-lg bg-destructive/5 border border-destructive/20 hover:bg-destructive/10 transition-colors group/item"
            >
              <div className="mt-1.5 relative shrink-0">
                <div className="w-2 h-2 rounded-full bg-destructive group-hover/item:scale-125 transition-transform" />
                <div className="absolute inset-0 w-2 h-2 rounded-full bg-destructive animate-ping opacity-50" />
              </div>
              <div className="flex-1">
                <p className="font-semibold text-foreground leading-tight">{alert.text}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${alert.urgency === "high" ? "border-destructive/30 text-destructive bg-destructive/10" : "border-primary/30 text-primary bg-primary/10"}`}>
                    {alert.urgency === "high" ? "عاجل جداً" : "متوسط الأهمية"}
                  </span>
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {alert.detail}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
        <Button variant="ghost" size="sm" className="w-full text-destructive hover:text-destructive hover:bg-destructive/10">
          عرض كل التنبيهات
        </Button>
      </CardContent>
    </Card>
  );
}

// ── CustomerSummary ──────────────────────────────────────────────────────

interface VipCustomer {
  id:     number;
  name:   string;
  since?: string;
  status: string;
}

interface CustomerSummaryProps {
  /** Pass real VIP customer data from the customers feature */
  vipCustomers?:  VipCustomer[];
  totalVip?:      number;
}

/** Shows top VIP customers count and list */
export function CustomerSummary({ vipCustomers, totalVip }: CustomerSummaryProps) {
  const showEmpty = !vipCustomers || vipCustomers.length === 0;

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Star className="w-5 h-5 text-yellow-500" />
          أهم العملاء (VIP)
          {totalVip != null && (
            <span className="ms-auto text-xs text-muted-foreground">
              {totalVip} إجمالاً
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {showEmpty
          ? <p className="text-sm text-muted-foreground text-center py-4">لا توجد بيانات</p>
          : vipCustomers!.map((c, i) => (
              <div key={c.id} className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 flex items-center justify-center font-bold text-primary">
                  {c.name.charAt(0)}
                </div>
                <div>
                  <p className="font-semibold text-sm">{c.name}</p>
                  <p className="text-xs text-muted-foreground">{c.since ?? "—"}</p>
                </div>
                <div className="me-auto text-xs font-medium text-green-500 bg-green-500/10 px-2 py-1 rounded-full">
                  {c.status}
                </div>
              </div>
            ))}
      </CardContent>
    </Card>
  );
}

// ── CommunicationWidget ──────────────────────────────────────────────────

/** Internal communication widget — mostly a UI affordance */
export function CommunicationWidget() {
  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-blue-500" />
          المحادثات الداخلية
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="bg-secondary/30 p-3 rounded-lg border border-border/50 text-sm">
          <p className="font-semibold text-primary mb-1">مدير المبيعات</p>
          <p className="text-muted-foreground">استخدم القنوات الموحدة للتواصل مع العملاء والفريق.</p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="اكتب رسالة..."
            className="flex-1 bg-secondary/50 border border-border rounded-md px-3 py-2 text-sm focus:ring-1 focus:ring-primary outline-none"
          />
          <Button size="icon" className="shrink-0 bg-primary hover:bg-primary/90 text-primary-foreground">
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ── FeedbackWidget ───────────────────────────────────────────────────────

interface Review {
  id:      number;
  user:    string;
  rating:  number;
  comment: string;
  time:    string;
}

const fallbackReviews: Review[] = [
  { id: 1, user: "—", rating: 5, comment: "—", time: "—" },
  { id: 2, user: "—", rating: 4, comment: "—", time: "—" },
];

interface FeedbackWidgetProps {
  reviews?: Review[];
}

/** Customer reviews widget */
export function FeedbackWidget({ reviews = fallbackReviews }: FeedbackWidgetProps) {
  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ThumbsUp className="w-5 h-5 text-primary" />
          آراء العملاء
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {reviews.map((review) => (
          <div key={review.id} className="border-b border-border/50 last:border-0 pb-3 last:pb-0">
            <div className="flex justify-between mb-1">
              <span className="font-medium text-sm">{review.user}</span>
              <div className="flex text-yellow-500">
                {[...Array(review.rating)].map((_, i) => (
                  <Star key={i} className="w-3 h-3 fill-current" />
                ))}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">{review.comment}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
