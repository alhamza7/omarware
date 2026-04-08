import { useState } from "react";
import { motion } from "motion/react";
import {
  AlertTriangle, AlertCircle, CheckCircle2, Clock, ArrowUpCircle,
  Crown, FileText, User, MessageSquare, ListChecks, ChevronDown, ChevronUp,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import { complaints, type Complaint, type TicketStatus, type TicketSeverity } from "./ad-data";

const severityConfig: Record<TicketSeverity, { color: string; label: string }> = {
  critical: { color: "bg-red-600/15 text-red-600 dark:text-red-400 border-red-500/30", label: "حرجة" },
  high: { color: "bg-red-500/15 text-red-500 border-red-500/30", label: "عالية" },
  medium: { color: "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/30", label: "متوسطة" },
  low: { color: "bg-blue-500/15 text-blue-500 border-blue-500/30", label: "منخفضة" },
};

const statusConfig: Record<TicketStatus, { icon: typeof Clock; color: string; label: string }> = {
  open: { icon: AlertCircle, color: "text-blue-500 bg-blue-500/10", label: "مفتوح" },
  escalated: { icon: ArrowUpCircle, color: "text-red-500 bg-red-500/10", label: "مصعّد" },
  "in-progress": { icon: Clock, color: "text-yellow-500 bg-yellow-500/10", label: "جاري" },
  resolved: { icon: CheckCircle2, color: "text-emerald-500 bg-emerald-500/10", label: "محلول" },
  closed: { icon: CheckCircle2, color: "text-zinc-500 bg-zinc-500/10", label: "مغلق" },
};

export function ADComplaints() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | TicketStatus>("all");

  const filtered = complaints.filter(
    (c) => statusFilter === "all" || c.status === statusFilter
  );

  const stats = {
    total: complaints.length,
    open: complaints.filter((c) => c.status === "open").length,
    escalated: complaints.filter((c) => c.status === "escalated").length,
    inProgress: complaints.filter((c) => c.status === "in-progress").length,
    resolved: complaints.filter((c) => ["resolved", "closed"].includes(c.status)).length,
    vip: complaints.filter((c) => c.customerType === "VIP").length,
  };

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-6 gap-3">
        {[
          { label: "إجمالي التكتات", value: stats.total, icon: FileText, color: "text-foreground" },
          { label: "مفتوحة", value: stats.open, icon: AlertCircle, color: "text-blue-500" },
          { label: "مصعّدة", value: stats.escalated, icon: ArrowUpCircle, color: "text-red-500" },
          { label: "جاري المعالجة", value: stats.inProgress, icon: Clock, color: "text-yellow-500" },
          { label: "محلولة", value: stats.resolved, icon: CheckCircle2, color: "text-emerald-500" },
          { label: "عملاء VIP", value: stats.vip, icon: Crown, color: "text-primary" },
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
      <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40 w-fit">
        {([
          { key: "all" as const, label: "الكل" },
          { key: "open" as const, label: "مفتوح" },
          { key: "escalated" as const, label: "مصعّد" },
          { key: "in-progress" as const, label: "جاري" },
          { key: "resolved" as const, label: "محلول" },
        ]).map((f) => (
          <button
            key={f.key}
            onClick={() => setStatusFilter(f.key)}
            className={`px-3 py-1.5 rounded text-xs transition-all ${
              statusFilter === f.key
                ? "bg-card text-primary shadow-sm border border-primary/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Tickets Table */}
      <Card className="border-border/40">
        <ScrollArea className="max-h-[calc(100vh-420px)]" dir="rtl">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border/40 bg-muted/20">
                <th className="text-start p-3 text-muted-foreground w-8"></th>
                <th className="text-start p-3 text-muted-foreground"># Ticket</th>
                <th className="text-start p-3 text-muted-foreground">الزبون</th>
                <th className="text-start p-3 text-muted-foreground">النوع</th>
                <th className="text-center p-3 text-muted-foreground">الخطورة</th>
                <th className="text-center p-3 text-muted-foreground">الحالة</th>
                <th className="text-start p-3 text-muted-foreground">المسؤول</th>
                <th className="text-center p-3 text-muted-foreground">التاريخ</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((complaint, i) => {
                const isExpanded = expandedId === complaint.id;
                const sc = statusConfig[complaint.status];
                const StatusIcon = sc.icon;
                const sev = severityConfig[complaint.severity];

                return (
                  <motion.tr
                    key={complaint.id}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className="border-b border-border/20 hover:bg-muted/10 transition-colors cursor-pointer group"
                    onClick={() => setExpandedId(isExpanded ? null : complaint.id)}
                  >
                    <td className="p-3">
                      {isExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
                      )}
                    </td>
                    <td className="p-3 text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {complaint.ticketNumber}
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-1">
                        <span className="text-foreground">{complaint.customerName}</span>
                        {complaint.customerType === "VIP" && (
                          <Badge className="bg-primary/10 text-primary text-[8px] border-transparent px-1 h-4">VIP</Badge>
                        )}
                      </div>
                    </td>
                    <td className="p-3 text-foreground">{complaint.type}</td>
                    <td className="p-3 text-center">
                      <Badge className={`text-[9px] border ${sev.color}`}>{sev.label}</Badge>
                    </td>
                    <td className="p-3 text-center">
                      <Badge className={`text-[9px] border-transparent ${sc.color}`}>
                        <StatusIcon className="w-3 h-3 me-0.5" />
                        {sc.label}
                      </Badge>
                    </td>
                    <td className="p-3 text-foreground">{complaint.assignee}</td>
                    <td className="p-3 text-center text-muted-foreground">{complaint.createdAt.split(" ")[0]}</td>
                  </motion.tr>
                );
              })}
              {/* Expanded details render separately */}
              {filtered.map((complaint) => {
                if (expandedId !== complaint.id) return null;
                return (
                  <tr key={`${complaint.id}-detail`} className="bg-muted/5">
                    <td colSpan={8} className="p-4">
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="space-y-3"
                      >
                        <p className="text-xs text-foreground">{complaint.description}</p>

                        <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
                          {complaint.relatedConversation && (
                            <span className="flex items-center gap-1">
                              <MessageSquare className="w-3 h-3" />
                              مربوط بالمحادثة: {complaint.relatedConversation}
                            </span>
                          )}
                          {complaint.relatedEmployee && (
                            <span className="flex items-center gap-1">
                              <User className="w-3 h-3" />
                              مربوط بالموظف: {complaint.relatedEmployee}
                            </span>
                          )}
                        </div>

                        {complaint.steps.length > 0 && (
                          <div className="space-y-1.5">
                            <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                              <ListChecks className="w-3 h-3" />
                              سجل الخطوات:
                            </p>
                            <div className="ps-4 border-s-2 border-primary/20 space-y-1">
                              {complaint.steps.map((step, si) => (
                                <p key={si} className="text-[10px] text-foreground">
                                  {step}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </ScrollArea>
      </Card>
    </div>
  );
}
