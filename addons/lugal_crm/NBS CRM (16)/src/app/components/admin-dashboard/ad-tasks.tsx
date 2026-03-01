import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Phone, MessageSquare, Mail, Hash, MessagesSquare, Instagram,
  Clock, AlertTriangle, CheckCircle2, Circle, UserPlus, Crown,
  ListTodo, CalendarClock, ArrowUpDown,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../ui/select";
import { tasks, employees, type Task, type TaskStatus } from "./ad-data";

const channelIcons: Record<string, typeof Phone> = {
  phone: Phone, whatsapp: MessageSquare, email: Mail,
  instagram: Instagram, x: Hash, "live-chat": MessagesSquare,
};

const statusConfig: Record<TaskStatus, { icon: typeof Circle; color: string; label: string }> = {
  open: { icon: Circle, color: "text-blue-500", label: "مفتوح" },
  "in-progress": { icon: Clock, color: "text-yellow-500", label: "جاري" },
  completed: { icon: CheckCircle2, color: "text-emerald-500", label: "منجز" },
  overdue: { icon: AlertTriangle, color: "text-red-500", label: "متأخر" },
};

const priorityConfig: Record<string, { color: string; label: string }> = {
  urgent: { color: "bg-red-500/15 text-red-500 border-red-500/30", label: "عاجل" },
  high: { color: "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/30", label: "عالي" },
  normal: { color: "bg-blue-500/15 text-blue-500 border-blue-500/30", label: "عادي" },
  low: { color: "bg-zinc-400/15 text-zinc-500 border-zinc-400/30", label: "منخفض" },
};

export function ADTasks() {
  const [taskList, setTaskList] = useState(tasks);
  const [filter, setFilter] = useState<"all" | TaskStatus>("all");
  const [showUnassigned, setShowUnassigned] = useState(false);

  const agentOptions = employees.filter((e) => e.role === "agent");

  const filtered = taskList.filter((t) => {
    if (filter !== "all" && t.status !== filter) return false;
    if (showUnassigned && t.assignee !== null) return false;
    return true;
  });

  const stats = {
    total: taskList.length,
    open: taskList.filter((t) => t.status === "open").length,
    overdue: taskList.filter((t) => t.status === "overdue").length,
    unassigned: taskList.filter((t) => t.assignee === null).length,
    completed: taskList.filter((t) => t.status === "completed").length,
  };

  const handleAssign = (taskId: string, assignee: string) => {
    setTaskList((prev) =>
      prev.map((t) =>
        t.id === taskId ? { ...t, assignee, status: "in-progress" as TaskStatus } : t
      )
    );
  };

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: "إجمالي المهام", value: stats.total, icon: ListTodo, color: "text-foreground" },
          { label: "مفتوحة", value: stats.open, icon: Circle, color: "text-blue-500" },
          { label: "متأخرة", value: stats.overdue, icon: AlertTriangle, color: "text-red-500" },
          { label: "بدون مسؤول", value: stats.unassigned, icon: UserPlus, color: "text-yellow-500" },
          { label: "مكتملة", value: stats.completed, icon: CheckCircle2, color: "text-emerald-500" },
        ].map((kpi, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card className="border-border/40">
              <CardContent className="p-3 flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg bg-primary/5 flex items-center justify-center shrink-0 ${kpi.color}`}>
                  <kpi.icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">{kpi.label}</p>
                  <p className={`text-lg ${kpi.color}`}>{kpi.value}</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40">
          {([
            { key: "all" as const, label: "الكل" },
            { key: "open" as const, label: "مفتوح" },
            { key: "in-progress" as const, label: "جاري" },
            { key: "overdue" as const, label: "متأخر" },
            { key: "completed" as const, label: "منجز" },
          ]).map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-3 py-1.5 rounded text-xs transition-all ${
                filter === f.key
                  ? "bg-card text-primary shadow-sm border border-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <Button
          variant={showUnassigned ? "default" : "outline"}
          size="sm"
          className="text-xs gap-1.5 h-8"
          onClick={() => setShowUnassigned(!showUnassigned)}
        >
          <UserPlus className="w-3.5 h-3.5" />
          بدون مسؤول فقط
          {stats.unassigned > 0 && (
            <Badge className="bg-red-500 text-white text-[9px] h-4 min-w-[16px] px-1 border-transparent">
              {stats.unassigned}
            </Badge>
          )}
        </Button>
      </div>

      {/* Task List */}
      <Card className="border-border/40">
        <ScrollArea className="max-h-[calc(100vh-420px)]" dir="rtl">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border/40 bg-muted/20">
                <th className="text-start p-3 text-muted-foreground">المهمة</th>
                <th className="text-start p-3 text-muted-foreground">الزبون</th>
                <th className="text-start p-3 text-muted-foreground">السبب</th>
                <th className="text-center p-3 text-muted-foreground">القناة</th>
                <th className="text-start p-3 text-muted-foreground">المسؤول</th>
                <th className="text-center p-3 text-muted-foreground">موعدها</th>
                <th className="text-center p-3 text-muted-foreground">الأولوية</th>
                <th className="text-center p-3 text-muted-foreground">الحالة</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filtered.map((task, i) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    index={i}
                    agents={agentOptions}
                    onAssign={handleAssign}
                  />
                ))}
              </AnimatePresence>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-muted-foreground">
                    لا توجد مهام تطابق الفلتر
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </ScrollArea>
      </Card>
    </div>
  );
}

function TaskRow({
  task, index, agents, onAssign,
}: {
  task: Task;
  index: number;
  agents: typeof employees;
  onAssign: (taskId: string, assignee: string) => void;
}) {
  const sc = statusConfig[task.status];
  const StatusIcon = sc.icon;
  const pc = priorityConfig[task.priority];
  const ChIcon = channelIcons[task.channel];

  const isToday = task.dueDate === "2026-02-23";
  const isYesterday = task.dueDate === "2026-02-22";

  return (
    <motion.tr
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ delay: index * 0.03 }}
      className="border-b border-border/20 hover:bg-muted/10 transition-colors"
    >
      <td className="p-3">
        <div className="flex items-center gap-2">
          <StatusIcon className={`w-4 h-4 ${sc.color}`} />
          <span className="text-foreground">{task.title}</span>
        </div>
      </td>
      <td className="p-3">
        <div className="flex items-center gap-1">
          <span className="text-foreground">{task.customerName}</span>
          {task.vip && <Crown className="w-3 h-3 text-primary" />}
        </div>
      </td>
      <td className="p-3 text-muted-foreground">{task.reason}</td>
      <td className="p-3 text-center">
        {ChIcon && <ChIcon className="w-3.5 h-3.5 mx-auto text-muted-foreground" />}
      </td>
      <td className="p-3">
        {task.assignee ? (
          <span className="text-foreground">{task.assignee}</span>
        ) : (
          <Select onValueChange={(v) => onAssign(task.id, v)}>
            <SelectTrigger className="h-7 text-[10px] w-28 border-dashed border-yellow-500/50 text-yellow-500">
              <SelectValue placeholder="تعيين موظف" />
            </SelectTrigger>
            <SelectContent>
              {agents.map((a) => (
                <SelectItem key={a.id} value={a.name} className="text-xs">
                  {a.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </td>
      <td className="p-3 text-center">
        <span className={`text-[10px] ${
          task.status === "overdue" ? "text-red-500" : isToday ? "text-yellow-500" : "text-foreground"
        }`}>
          {isToday ? `اليوم ${task.dueTime}` : isYesterday ? "أمس" : task.dueDate}
        </span>
      </td>
      <td className="p-3 text-center">
        <Badge className={`text-[9px] border ${pc.color}`}>{pc.label}</Badge>
      </td>
      <td className="p-3 text-center">
        <Badge className={`text-[9px] border-transparent ${
          task.status === "completed" ? "bg-emerald-500/10 text-emerald-500"
            : task.status === "overdue" ? "bg-red-500/10 text-red-500"
            : task.status === "in-progress" ? "bg-yellow-500/10 text-yellow-500"
            : "bg-blue-500/10 text-blue-500"
        }`}>
          {sc.label}
        </Badge>
      </td>
    </motion.tr>
  );
}
