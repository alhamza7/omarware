import { useState } from "react";
import { motion } from "motion/react";
import {
  Phone, MessageSquare, Mail, Instagram, Hash, MessagesSquare,
  Clock, Headphones, TrendingUp, AlertTriangle,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Progress } from "../ui/progress";
import { ScrollArea } from "../ui/scroll-area";
import {
  employees, statusColors, channelLabels, slaColors, roleLabels,
  type Employee, type EmployeeRole,
} from "./ad-data";

const channelIcons: Record<string, typeof Phone> = {
  phone: Phone, whatsapp: MessageSquare, email: Mail,
  instagram: Instagram, x: Hash, "live-chat": MessagesSquare,
};

export function ADEmployees() {
  const [roleFilter, setRoleFilter] = useState<"all" | EmployeeRole>("all");

  const filtered = employees.filter(
    (e) => roleFilter === "all" || e.role === roleFilter
  );

  const stats = {
    total: employees.length,
    online: employees.filter((e) => e.status !== "offline").length,
    busy: employees.filter((e) => e.status === "busy").length,
    onBreak: employees.filter((e) => e.status === "break").length,
    slaBreached: employees.filter((e) => e.sla === "breached").length,
    avgSLA: Math.round(employees.filter(e => e.slaPercent > 0).reduce((s, e) => s + e.slaPercent, 0) / employees.filter(e => e.slaPercent > 0).length),
  };

  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-6 gap-3">
        {[
          { label: "إجمالي الموظفين", value: stats.total, color: "text-foreground", icon: Headphones },
          { label: "متصل الآن", value: stats.online, color: "text-emerald-500", icon: TrendingUp },
          { label: "مشغول", value: stats.busy, color: "text-red-500", icon: Phone },
          { label: "استراحة", value: stats.onBreak, color: "text-yellow-500", icon: Clock },
          { label: "مخالفة SLA", value: stats.slaBreached, color: "text-red-500", icon: AlertTriangle },
          { label: "متوسط SLA", value: `${stats.avgSLA}%`, color: "text-primary", icon: TrendingUp },
        ].map((kpi, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card className="border-border/40">
              <CardContent className="p-3 flex items-center gap-3">
                <div className={`w-9 h-9 rounded-lg bg-primary/5 flex items-center justify-center shrink-0 ${kpi.color}`}>
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
      <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40 w-fit">
        {([
          { key: "all" as const, label: "الكل" },
          { key: "agent" as const, label: "وكلاء" },
          { key: "supervisor" as const, label: "مشرفين" },
          { key: "qa" as const, label: "مدققين" },
        ]).map((f) => (
          <button
            key={f.key}
            onClick={() => setRoleFilter(f.key)}
            className={`px-3 py-1.5 rounded text-xs transition-all ${
              roleFilter === f.key
                ? "bg-card text-primary shadow-sm border border-primary/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Employee Table */}
      <Card className="border-border/40">
        <ScrollArea className="max-h-[calc(100vh-420px)]" dir="rtl">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/40 bg-muted/20">
                  <th className="text-start p-3 text-muted-foreground">الموظف</th>
                  <th className="text-center p-3 text-muted-foreground">الحالة</th>
                  <th className="text-center p-3 text-muted-foreground">القناة</th>
                  <th className="text-center p-3 text-muted-foreground">محادثات مفتوحة</th>
                  <th className="text-center p-3 text-muted-foreground">مكالمات</th>
                  <th className="text-center p-3 text-muted-foreground">رسائل</th>
                  <th className="text-center p-3 text-muted-foreground">آخر استجابة</th>
                  <th className="text-center p-3 text-muted-foreground">SLA</th>
                  <th className="text-center p-3 text-muted-foreground">متوسط الرد</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((emp, i) => (
                  <EmployeeRow key={emp.id} emp={emp} index={i} />
                ))}
              </tbody>
            </table>
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}

function EmployeeRow({ emp, index }: { emp: Employee; index: number }) {
  const sc = statusColors[emp.status];
  const slaC = slaColors[emp.sla];
  const ChannelIcon = emp.channel ? channelIcons[emp.channel] : null;
  const ch = emp.channel ? channelLabels[emp.channel] : null;

  return (
    <motion.tr
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      className="border-b border-border/20 hover:bg-muted/10 transition-colors"
    >
      {/* Employee */}
      <td className="p-3">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Avatar className="w-8 h-8 border border-border/40">
              <AvatarFallback className="bg-primary/10 text-primary text-[10px]">{emp.avatar}</AvatarFallback>
            </Avatar>
            <span className={`absolute -bottom-0.5 -end-0.5 w-2.5 h-2.5 rounded-full border-2 border-card ${sc.dot}`} />
          </div>
          <div>
            <p className="text-foreground">{emp.name}</p>
            <p className="text-[10px] text-muted-foreground">{roleLabels[emp.role]} • {emp.shift}</p>
          </div>
        </div>
      </td>

      {/* Status */}
      <td className="p-3 text-center">
        <Badge className={`${sc.bg} ${sc.text} text-[10px] border-transparent`}>
          {sc.label}
        </Badge>
      </td>

      {/* Channel */}
      <td className="p-3 text-center">
        {ChannelIcon && ch ? (
          <div className="flex items-center justify-center gap-1">
            <ChannelIcon className={`w-3.5 h-3.5 ${ch.color}`} />
            <span className={`text-[10px] ${ch.color}`}>{ch.label}</span>
          </div>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </td>

      {/* Open conversations */}
      <td className="p-3 text-center">
        <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs ${
          emp.openConversations > 6
            ? "bg-red-500/10 text-red-500"
            : emp.openConversations > 3
            ? "bg-yellow-500/10 text-yellow-500"
            : "bg-muted/30 text-foreground"
        }`}>
          {emp.openConversations}
        </span>
      </td>

      {/* Calls */}
      <td className="p-3 text-center text-foreground">{emp.callsToday}</td>

      {/* Messages */}
      <td className="p-3 text-center text-foreground">{emp.messagesHandled}</td>

      {/* Last response */}
      <td className="p-3 text-center">
        <span className={`text-[10px] ${
          emp.lastResponse.includes("دقيقتين") || emp.lastResponse.includes("دقيقة")
            ? "text-emerald-500"
            : emp.lastResponse.includes("25") || emp.lastResponse === "—"
            ? "text-red-500"
            : "text-yellow-500"
        }`}>
          {emp.lastResponse}
        </span>
      </td>

      {/* SLA */}
      <td className="p-3">
        <div className="flex flex-col items-center gap-1">
          <div className="flex items-center gap-1.5">
            <span className={`text-[10px] ${slaC.text}`}>{emp.slaPercent > 0 ? `${emp.slaPercent}%` : "—"}</span>
          </div>
          {emp.slaPercent > 0 && (
            <div className="w-16">
              <Progress
                value={emp.slaPercent}
                className={`h-1.5 ${
                  emp.sla === "breached" ? "[&>[data-slot=progress-indicator]]:bg-red-500 bg-red-500/20"
                    : emp.sla === "warning" ? "[&>[data-slot=progress-indicator]]:bg-yellow-500 bg-yellow-500/20"
                    : ""
                }`}
              />
            </div>
          )}
        </div>
      </td>

      {/* Avg response */}
      <td className="p-3 text-center">
        <span className="text-muted-foreground">{emp.avgResponseTime}</span>
      </td>
    </motion.tr>
  );
}
