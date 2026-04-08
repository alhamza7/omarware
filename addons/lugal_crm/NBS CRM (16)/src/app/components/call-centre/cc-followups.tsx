import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  CalendarDays,
  Clock,
  User,
  AlertTriangle,
  CheckCircle2,
  Bell,
  Plus,
  X,
  Send,
  Phone,
  StickyNote,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { followUps, type FollowUp } from "./cc-data";

const statusConfig: Record<FollowUp["status"], { label: string; color: string; bg: string; icon: typeof Clock }> = {
  pending: { label: "معلّقة", color: "text-primary", bg: "bg-primary/10", icon: Clock },
  completed: { label: "مكتملة", color: "text-emerald-500", bg: "bg-emerald-500/10", icon: CheckCircle2 },
  overdue: { label: "متأخرة", color: "text-red-500", bg: "bg-red-500/10", icon: AlertTriangle },
};

export function CCFollowUps() {
  const [items, setItems] = useState(followUps);
  const [filter, setFilter] = useState<"all" | FollowUp["status"]>("all");
  const [showNewForm, setShowNewForm] = useState(false);
  const [newCustomer, setNewCustomer] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [newReason, setNewReason] = useState("");

  const filtered = filter === "all" ? items : items.filter((f) => f.status === filter);

  const pendingCount = items.filter((f) => f.status === "pending").length;
  const overdueCount = items.filter((f) => f.status === "overdue").length;
  const completedCount = items.filter((f) => f.status === "completed").length;

  const markComplete = (id: string) => {
    setItems((prev) => prev.map((f) => (f.id === id ? { ...f, status: "completed" as const } : f)));
  };

  const handleAdd = () => {
    if (!newCustomer.trim() || !newReason.trim()) return;
    const newItem: FollowUp = {
      id: `fu${Date.now()}`,
      customerName: newCustomer,
      customerId: "C-NEW",
      agentName: "أحمد العلي",
      scheduledDate: newDate || "2026-02-23",
      scheduledTime: newTime || "10:00",
      reason: newReason,
      status: "pending",
      notes: "",
      priority: "normal",
    };
    setItems((prev) => [newItem, ...prev]);
    setNewCustomer("");
    setNewDate("");
    setNewTime("");
    setNewReason("");
    setShowNewForm(false);
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "معلّقة", value: pendingCount, color: "text-primary", bg: "bg-primary/10", icon: Clock },
          { label: "متأخرة", value: overdueCount, color: "text-red-500", bg: "bg-red-500/10", icon: AlertTriangle },
          { label: "مكتملة", value: completedCount, color: "text-emerald-500", bg: "bg-emerald-500/10", icon: CheckCircle2 },
          { label: "الإجمالي", value: items.length, color: "text-foreground", bg: "bg-secondary", icon: CalendarDays },
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="border-border/50">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-lg ${stat.bg} flex items-center justify-center shrink-0`}>
                    <Icon className={`w-4.5 h-4.5 ${stat.color}`} />
                  </div>
                  <div>
                    <p className={`text-xl ${stat.color}`}>{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          {[
            { key: "all" as const, label: "الكل" },
            { key: "pending" as const, label: "معلّقة" },
            { key: "overdue" as const, label: "متأخرة" },
            { key: "completed" as const, label: "مكتملة" },
          ].map((f) => (
            <Button
              key={f.key}
              variant={filter === f.key ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(f.key)}
              className="text-xs"
            >
              {f.label}
            </Button>
          ))}
        </div>
        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => setShowNewForm(true)}
        >
          <Plus className="w-4 h-4" />
          جدولة متابعة
        </Button>
      </div>

      {/* New Follow-up Form */}
      <AnimatePresence>
        {showNewForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="border-primary/30 bg-primary/5">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CalendarDays className="w-4 h-4 text-primary" />
                    جدولة متابعة جديدة
                  </CardTitle>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setShowNewForm(false)}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input
                    placeholder="اسم العميل"
                    value={newCustomer}
                    onChange={(e) => setNewCustomer(e.target.value)}
                    className="bg-background"
                  />
                  <Input
                    type="date"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="bg-background"
                  />
                  <Input
                    type="time"
                    value={newTime}
                    onChange={(e) => setNewTime(e.target.value)}
                    className="bg-background"
                  />
                </div>
                <Input
                  placeholder="سبب المتابعة"
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  className="bg-background"
                />
                <Button onClick={handleAdd} size="sm" className="gap-2">
                  <Send className="w-3.5 h-3.5" />
                  إضافة
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Follow-ups List */}
      <div className="space-y-3">
        {filtered.map((fu, i) => {
          const status = statusConfig[fu.status];
          const StatusIcon = status.icon;

          return (
            <motion.div
              key={fu.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className={`transition-all hover:shadow-md ${
                fu.status === "overdue"
                  ? "border-s-2 border-s-red-500 border-border/50"
                  : fu.status === "completed"
                  ? "border-border/50 opacity-70"
                  : "border-border/50"
              }`}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    {/* Status Icon */}
                    <div className={`w-10 h-10 rounded-xl ${status.bg} flex items-center justify-center shrink-0`}>
                      <StatusIcon className={`w-5 h-5 ${status.color}`} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3 mb-1.5">
                        <div>
                          <div className="flex items-center gap-2 mb-0.5">
                            <h4 className="text-sm text-foreground">{fu.customerName}</h4>
                            <Badge className={`text-[10px] border-transparent gap-0.5 ${status.bg} ${status.color}`}>
                              <StatusIcon className="w-2.5 h-2.5" />
                              {status.label}
                            </Badge>
                            {fu.priority === "high" && (
                              <Badge className="text-[10px] border-transparent bg-red-500/10 text-red-500">
                                أولوية عالية
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground">{fu.reason}</p>
                        </div>
                      </div>

                      {/* Details */}
                      <div className="flex items-center gap-4 text-xs text-muted-foreground mt-2 flex-wrap">
                        <span className="flex items-center gap-1.5">
                          <CalendarDays className="w-3 h-3" />
                          {new Date(fu.scheduledDate).toLocaleDateString("ar-SA")}
                        </span>
                        <span className="flex items-center gap-1.5" dir="ltr">
                          <Clock className="w-3 h-3" />
                          {fu.scheduledTime}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <User className="w-3 h-3" />
                          {fu.agentName}
                        </span>
                      </div>

                      {/* Notes */}
                      {fu.notes && (
                        <div className="flex items-start gap-1.5 mt-2 text-xs text-muted-foreground">
                          <StickyNote className="w-3 h-3 shrink-0 mt-0.5" />
                          <p>{fu.notes}</p>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    {fu.status !== "completed" && (
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs h-7 gap-1.5"
                        >
                          <Phone className="w-3 h-3" />
                          اتصال
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs h-7 text-emerald-500 hover:text-emerald-500 hover:bg-emerald-500/10 gap-1.5"
                          onClick={() => markComplete(fu.id)}
                        >
                          <CheckCircle2 className="w-3 h-3" />
                          تم
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <CalendarDays className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>لا توجد متابعات {filter !== "all" ? statusConfig[filter as FollowUp["status"]]?.label : ""}</p>
          </div>
        )}
      </div>
    </div>
  );
}
