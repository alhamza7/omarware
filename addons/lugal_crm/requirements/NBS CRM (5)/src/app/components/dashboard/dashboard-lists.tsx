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
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../ui/card";
import { Button } from "../ui/button";

const interactions = [
  {
    id: 1,
    type: "call",
    customer: "أحمد العلي",
    note: "استفسار عن عطر العود",
    time: "منذ 10 دقائق",
    status: "completed",
  },
  {
    id: 2,
    type: "email",
    customer: "سارة محمد",
    note: "تأكيد الطلبية #1023",
    time: "منذ ساعة",
    status: "pending",
  },
  {
    id: 3,
    type: "meeting",
    customer: "شركة الريان",
    note: "مناقشة العقد السنوي",
    time: "اليوم 2:00 م",
    status: "upcoming",
  },
];

const tasks = [
  {
    id: 1,
    text: "إعداد التقرير الشهري",
    due: "اليوم",
    completed: false,
  },
  {
    id: 2,
    text: "متابعة عميل VIP",
    due: "غداً",
    completed: true,
  },
  {
    id: 3,
    text: "تحديث قائمة الأسعار",
    due: "الخميس",
    completed: false,
  },
];

const alerts = [
  {
    id: 1,
    text: "تجديد عقد المورد الرئيسي",
    urgency: "high",
    date: "بعد يومين",
  },
  {
    id: 2,
    text: "اجتماع الفريق الأسبوعي",
    urgency: "medium",
    date: "اليوم 4:00 م",
  },
];

const reviews = [
  {
    id: 1,
    user: "محمد ناصر",
    rating: 5,
    comment: "خدمة رائعة ومنتجات فاخرة!",
    time: "أمس",
  },
  {
    id: 2,
    user: "نورة السعد",
    rating: 4,
    comment: "التغليف مميز جداً",
    time: "قبل يومين",
  },
];

export function RecentInteractions() {
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
              {interaction.type === "call" && (
                <Phone className="w-4 h-4" />
              )}
              {interaction.type === "email" && (
                <Mail className="w-4 h-4" />
              )}
              {interaction.type === "meeting" && (
                <User className="w-4 h-4" />
              )}
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-start">
                <h4 className="text-sm font-semibold">
                  {interaction.customer}
                </h4>
                <span className="text-xs text-muted-foreground">
                  {interaction.time}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {interaction.note}
              </p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function TaskTracker() {
  return (
    <Card className="col-span-1 h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-green-500" />
          المهام اليومية
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {tasks.map((task) => (
          <div
            key={task.id}
            className="flex items-center gap-3 p-2 group cursor-pointer hover:bg-secondary/50 rounded-lg transition-colors"
          >
            {task.completed ? (
              <CheckCircle2 className="w-5 h-5 text-green-500/80" />
            ) : (
              <Circle className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            )}
            <span
              className={`text-sm flex-1 ${task.completed ? "line-through text-muted-foreground" : ""}`}
            >
              {task.text}
            </span>
            <span className="text-xs px-2 py-1 rounded-full bg-secondary text-muted-foreground">
              {task.due}
            </span>
          </div>
        ))}
        <Button
          variant="ghost"
          size="sm"
          className="w-full mt-2 text-primary hover:text-primary/80 border border-dashed border-primary/30"
        >
          + إضافة مهمة جديدة
        </Button>
      </CardContent>
    </Card>
  );
}

export function AlertsWidget() {
  return (
    <Card className="col-span-1 bg-gradient-to-br from-destructive/10 via-card to-card border-destructive/50 shadow-lg shadow-destructive/10 relative overflow-hidden group hover:border-destructive/80 transition-colors duration-300">
      {/* Pulsing background effect */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-destructive/20 blur-3xl rounded-full -mr-16 -mt-16 animate-pulse" />

      <CardHeader className="pb-2 relative z-10">
        <CardTitle className="flex items-center gap-2 text-base text-destructive font-bold">
          <div className="relative">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-destructive rounded-full animate-ping opacity-75" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-destructive rounded-full border-2 border-card" />
          </div>
          تنبيهات هامة
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 relative z-10">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="flex items-start gap-3 text-sm p-3 rounded-lg bg-destructive/5 border border-destructive/20 hover:bg-destructive/10 transition-colors group/item"
          >
            <div className="mt-1.5 relative shrink-0">
              <div className="w-2 h-2 rounded-full bg-destructive group-hover/item:scale-125 transition-transform" />
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-destructive animate-ping opacity-50" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-foreground leading-tight">
                {alert.text}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${alert.urgency === "high" ? "border-destructive/30 text-destructive bg-destructive/10" : "border-primary/30 text-primary bg-primary/10"}`}
                >
                  {alert.urgency === "high"
                    ? "عاجل جداً"
                    : "متوسط الأهمية"}
                </span>
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {alert.date}
                </span>
              </div>
            </div>
          </div>
        ))}
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-destructive hover:text-destructive hover:bg-destructive/10"
        >
          عرض كل التنبيهات
        </Button>
      </CardContent>
    </Card>
  );
}

export function CustomerSummary() {
  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Star className="w-5 h-5 text-yellow-500" />
          أهم العملاء (VIP)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 flex items-center justify-center font-bold text-primary">
              {String.fromCharCode(65 + i)}
            </div>
            <div>
              <p className="font-semibold text-sm">
                العميل {i}
              </p>
              <p className="text-xs text-muted-foreground">
                مشترِ نشط منذ 2023
              </p>
            </div>
            <div className="mr-auto text-xs font-medium text-green-500 bg-green-500/10 px-2 py-1 rounded-full">
              نشط
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

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
          <p className="font-semibold text-primary mb-1">
            مدير المبيعات
          </p>
          <p className="text-muted-foreground">
            هل تم التواصل مع عملاء جدة بخصوص العرض الجديد؟
          </p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="اكتب رسالة..."
            className="flex-1 bg-secondary/50 border border-border rounded-md px-3 py-2 text-sm focus:ring-1 focus:ring-primary outline-none"
          />
          <Button
            size="icon"
            className="shrink-0 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function FeedbackWidget() {
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
          <div
            key={review.id}
            className="border-b border-border/50 last:border-0 pb-3 last:pb-0"
          >
            <div className="flex justify-between mb-1">
              <span className="font-medium text-sm">
                {review.user}
              </span>
              <div className="flex text-yellow-500">
                {[...Array(review.rating)].map((_, i) => (
                  <Star
                    key={i}
                    className="w-3 h-3 fill-current"
                  />
                ))}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              {review.comment}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}