import { useState } from "react";
import { motion } from "motion/react";
import {
  Search,
  AlertTriangle,
  ArrowUp,
  Minus,
  ArrowDown,
  MessageCircle,
  User,
  Clock,
  Tag,
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { tickets, type Ticket } from "./cc-data";

const priorityConfig: Record<Ticket["priority"], { label: string; icon: typeof AlertTriangle; color: string; bg: string }> = {
  urgent: { label: "عاجل", icon: AlertTriangle, color: "text-red-500", bg: "bg-red-500/10" },
  high: { label: "مرتفع", icon: ArrowUp, color: "text-primary", bg: "bg-primary/10" },
  normal: { label: "عادي", icon: Minus, color: "text-blue-500", bg: "bg-blue-500/10" },
  low: { label: "منخفض", icon: ArrowDown, color: "text-muted-foreground", bg: "bg-muted" },
};

const statusConfig: Record<Ticket["status"], { label: string; icon: typeof Circle; color: string; bg: string }> = {
  open: { label: "مفتوحة", icon: Circle, color: "text-red-500", bg: "bg-red-500/10" },
  "in-progress": { label: "قيد المعالجة", icon: Loader2, color: "text-primary", bg: "bg-primary/10" },
  resolved: { label: "تم الحل", icon: CheckCircle2, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  closed: { label: "مغلقة", icon: XCircle, color: "text-muted-foreground", bg: "bg-muted" },
};

export function CCTickets() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | Ticket["status"]>("all");

  const filtered = tickets.filter((t) => {
    const matchSearch =
      t.title.includes(search) || t.customerName.includes(search) || t.id.includes(search);
    const matchStatus = statusFilter === "all" || t.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const openCount = tickets.filter((t) => t.status === "open").length;
  const inProgressCount = tickets.filter((t) => t.status === "in-progress").length;
  const resolvedCount = tickets.filter((t) => t.status === "resolved").length;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "مفتوحة", value: openCount, color: "text-red-500", bg: "bg-red-500/10", icon: Circle },
          { label: "قيد المعالجة", value: inProgressCount, color: "text-primary", bg: "bg-primary/10", icon: Loader2 },
          { label: "تم الحل", value: resolvedCount, color: "text-emerald-500", bg: "bg-emerald-500/10", icon: CheckCircle2 },
          { label: "الإجمالي", value: tickets.length, color: "text-foreground", bg: "bg-secondary", icon: Tag },
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

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="بحث في التذاكر..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9 bg-secondary/30 border-border/50"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={statusFilter === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setStatusFilter("all")}
            className="text-xs"
          >
            الكل
          </Button>
          {Object.entries(statusConfig).map(([key, config]) => {
            const Icon = config.icon;
            return (
              <Button
                key={key}
                variant={statusFilter === key ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter(key as Ticket["status"])}
                className="text-xs gap-1.5"
              >
                <Icon className="w-3 h-3" />
                {config.label}
              </Button>
            );
          })}
        </div>
      </div>

      {/* Tickets List */}
      <div className="space-y-3">
        {filtered.map((ticket, i) => {
          const priority = priorityConfig[ticket.priority];
          const status = statusConfig[ticket.status];
          const PriorityIcon = priority.icon;
          const StatusIcon = status.icon;

          return (
            <motion.div
              key={ticket.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className={`hover:shadow-md transition-all group cursor-pointer ${
                ticket.priority === "urgent" ? "border-s-2 border-s-red-500 border-border/50" : "border-border/50"
              }`}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    {/* Priority Icon */}
                    <div className={`w-9 h-9 rounded-lg ${priority.bg} flex items-center justify-center shrink-0 mt-0.5`}>
                      <PriorityIcon className={`w-4 h-4 ${priority.color}`} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3 mb-1.5">
                        <div>
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className="text-[10px] font-mono text-muted-foreground">{ticket.id}</span>
                            <Badge className={`text-[10px] border-transparent ${status.bg} ${status.color} gap-0.5`}>
                              <StatusIcon className="w-2.5 h-2.5" />
                              {status.label}
                            </Badge>
                            <Badge className={`text-[10px] border-transparent ${priority.bg} ${priority.color}`}>
                              {priority.label}
                            </Badge>
                          </div>
                          <h4 className="text-sm text-foreground group-hover:text-primary transition-colors">
                            {ticket.title}
                          </h4>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap mt-2">
                        <span className="flex items-center gap-1.5">
                          <User className="w-3 h-3" />
                          {ticket.customerName}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Tag className="w-3 h-3" />
                          {ticket.category}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <MessageCircle className="w-3 h-3" />
                          {ticket.messages} رسالة
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Clock className="w-3 h-3" />
                          {ticket.updatedAt}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-[10px] h-5">
                          الوكيل: {ticket.assignee}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <CheckCircle2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>لا توجد تذاكر تطابق البحث</p>
          </div>
        )}
      </div>
    </div>
  );
}
