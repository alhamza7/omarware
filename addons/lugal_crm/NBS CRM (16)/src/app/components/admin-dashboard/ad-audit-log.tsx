import { useState } from "react";
import { motion } from "motion/react";
import {
  LogIn, LogOut, Phone, Play, Settings, Star, FileText,
  ArrowRightLeft, MessageSquare, CheckCircle, Briefcase,
  Shield, Search, Filter, Lock,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Avatar, AvatarFallback } from "../ui/avatar";
import {
  auditLog, roleLabels,
  type AuditEntry, type AuditAction, type EmployeeRole,
} from "./ad-data";

const actionConfig: Record<AuditAction, { icon: typeof LogIn; color: string; label: string }> = {
  login: { icon: LogIn, color: "text-emerald-500", label: "تسجيل دخول" },
  logout: { icon: LogOut, color: "text-zinc-500", label: "تسجيل خروج" },
  "status-change": { icon: Settings, color: "text-blue-500", label: "تعديل حالة" },
  "call-open": { icon: Phone, color: "text-violet-500", label: "فتح مكالمة" },
  "call-listen": { icon: Phone, color: "text-cyan-500", label: "استماع لمكالمة" },
  "recording-play": { icon: Play, color: "text-pink-500", label: "تشغيل تسجيل" },
  "rule-edit": { icon: Settings, color: "text-yellow-500", label: "تعديل قاعدة" },
  evaluate: { icon: Star, color: "text-primary", label: "تقييم" },
  "ticket-open": { icon: FileText, color: "text-blue-500", label: "فتح تكت" },
  "conversation-transfer": { icon: ArrowRightLeft, color: "text-violet-500", label: "نقل محادثة" },
  "message-review": { icon: MessageSquare, color: "text-cyan-500", label: "مراجعة رسائل" },
  approval: { icon: CheckCircle, color: "text-emerald-500", label: "موافقة" },
  decision: { icon: Briefcase, color: "text-primary", label: "قرار" },
};

const roleColors: Record<EmployeeRole, string> = {
  agent: "bg-blue-500/10 text-blue-500",
  supervisor: "bg-violet-500/10 text-violet-500",
  manager: "bg-primary/10 text-primary",
  qa: "bg-cyan-500/10 text-cyan-500",
  "qa-supervisor": "bg-pink-500/10 text-pink-500",
};

export function ADAuditLog() {
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<"all" | EmployeeRole>("all");
  const [actionFilter, setActionFilter] = useState<"all" | AuditAction>("all");

  const filtered = auditLog.filter((entry) => {
    if (roleFilter !== "all" && entry.userRole !== roleFilter) return false;
    if (actionFilter !== "all" && entry.action !== actionFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        entry.userName.includes(searchQuery) ||
        entry.details.includes(searchQuery) ||
        entry.target.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Notice */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-3 flex items-center gap-3">
          <Lock className="w-4 h-4 text-primary shrink-0" />
          <div className="flex items-center gap-4 text-xs">
            <span className="text-primary">لا يمكن حذف أي سجل</span>
            <span className="text-muted-foreground">•</span>
            <span className="text-muted-foreground">فقط قراءة + فلترة</span>
            <span className="text-muted-foreground">•</span>
            <span className="text-muted-foreground">{auditLog.length} سجل مسجّل</span>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative">
          <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input
            placeholder="بحث في السجل..."
            className="h-8 text-xs ps-8 w-56"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40">
          {([
            { key: "all" as const, label: "الكل" },
            { key: "agent" as const, label: "وكيل" },
            { key: "supervisor" as const, label: "مشرف" },
            { key: "qa" as const, label: "مدقق" },
          ]).map((f) => (
            <button
              key={f.key}
              onClick={() => setRoleFilter(f.key)}
              className={`px-2.5 py-1 rounded text-[10px] transition-all ${
                roleFilter === f.key
                  ? "bg-card text-primary shadow-sm border border-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40">
          {([
            { key: "all" as const, label: "كل العمليات" },
            { key: "login" as const, label: "دخول/خروج" },
            { key: "evaluate" as const, label: "تقييم" },
            { key: "status-change" as const, label: "تغيير حالة" },
            { key: "conversation-transfer" as const, label: "نقل" },
          ]).map((f) => (
            <button
              key={f.key}
              onClick={() => setActionFilter(f.key)}
              className={`px-2.5 py-1 rounded text-[10px] transition-all ${
                actionFilter === f.key
                  ? "bg-card text-primary shadow-sm border border-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Log Table */}
      <Card className="border-border/40">
        <ScrollArea className="max-h-[calc(100vh-400px)]" dir="rtl">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border/40 bg-muted/20">
                <th className="text-center p-3 text-muted-foreground w-16">الوقت</th>
                <th className="text-start p-3 text-muted-foreground">المستخدم</th>
                <th className="text-center p-3 text-muted-foreground">الدور</th>
                <th className="text-start p-3 text-muted-foreground">العملية</th>
                <th className="text-start p-3 text-muted-foreground">العنصر</th>
                <th className="text-start p-3 text-muted-foreground">التفاصيل</th>
                <th className="text-center p-3 text-muted-foreground">IP</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry, i) => {
                const ac = actionConfig[entry.action];
                const ActionIcon = ac.icon;
                const rc = roleColors[entry.userRole];

                return (
                  <motion.tr
                    key={entry.id}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-border/20 hover:bg-muted/10 transition-colors"
                  >
                    <td className="p-3 text-center text-muted-foreground">{entry.timestamp}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <Avatar className="w-6 h-6 border border-border/30">
                          <AvatarFallback className="bg-primary/10 text-primary text-[8px]">
                            {entry.userName.slice(0, 2)}
                          </AvatarFallback>
                        </Avatar>
                        <span className="text-foreground">{entry.userName}</span>
                      </div>
                    </td>
                    <td className="p-3 text-center">
                      <Badge className={`text-[8px] border-transparent ${rc}`}>
                        {roleLabels[entry.userRole]}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-1.5">
                        <ActionIcon className={`w-3.5 h-3.5 ${ac.color}`} />
                        <span className={ac.color}>{ac.label}</span>
                      </div>
                    </td>
                    <td className="p-3 text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {entry.target}
                    </td>
                    <td className="p-3 text-muted-foreground max-w-[250px] truncate">{entry.details}</td>
                    <td className="p-3 text-center">
                      <span className="text-[9px] text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {entry.ip}
                      </span>
                    </td>
                  </motion.tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-muted-foreground">لا توجد نتائج</td>
                </tr>
              )}
            </tbody>
          </table>
        </ScrollArea>
      </Card>
    </div>
  );
}
