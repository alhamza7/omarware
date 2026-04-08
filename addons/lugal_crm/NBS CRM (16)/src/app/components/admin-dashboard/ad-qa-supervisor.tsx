import { useState } from "react";
import { motion } from "motion/react";
import {
  Eye, Clock, Headphones, MessageSquare, FileText, Star,
  AlertTriangle, TrendingUp, TrendingDown, BarChart3,
  CheckCircle2, XCircle, Timer,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Progress } from "../ui/progress";
import { ScrollArea } from "../ui/scroll-area";
import { qaAuditors, qaEvaluations, type QAAuditor } from "./ad-data";

const fmt = (n: number) => new Intl.NumberFormat("ar-SA").format(n);

export function ADQaSupervisor() {
  const [period, setPeriod] = useState<"today" | "week" | "month">("today");
  const [selectedAuditor, setSelectedAuditor] = useState<QAAuditor | null>(null);

  const getEvalCount = (auditor: QAAuditor) => {
    switch (period) {
      case "today": return auditor.evaluationsToday;
      case "week": return auditor.evaluationsWeek;
      case "month": return auditor.evaluationsMonth;
    }
  };

  const totalEvals = qaAuditors.reduce((s, a) => s + getEvalCount(a), 0);
  const avgProductivity = Math.round(qaAuditors.reduce((s, a) => s + a.productivity, 0) / qaAuditors.length);
  const totalOpenedLeft = qaAuditors.reduce((s, a) => s + a.openedAndLeft, 0);

  return (
    <div className="space-y-4">
      {/* Period Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40">
          {([
            { key: "today" as const, label: "اليوم" },
            { key: "week" as const, label: "الأسبوع" },
            { key: "month" as const, label: "الشهر" },
          ]).map((f) => (
            <button
              key={f.key}
              onClick={() => setPeriod(f.key)}
              className={`px-3 py-1.5 rounded text-xs transition-all ${
                period === f.key
                  ? "bg-card text-primary shadow-sm border border-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        <Badge className="bg-primary/10 text-primary border-transparent text-xs gap-1">
          <Eye className="w-3 h-3" />
          مشرف المدققين
        </Badge>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "إجمالي التقييمات", value: totalEvals, icon: Star, color: "text-primary" },
          { label: "متوسط الإنتاجية", value: `${avgProductivity}%`, icon: TrendingUp, color: avgProductivity >= 80 ? "text-emerald-500" : "text-yellow-500" },
          { label: "عدد المدققين", value: qaAuditors.length, icon: Eye, color: "text-cyan-500" },
          { label: "فتح بدون تقييم", value: totalOpenedLeft, icon: AlertTriangle, color: totalOpenedLeft > 0 ? "text-red-500" : "text-emerald-500" },
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

      {/* Auditor Cards */}
      <div className="grid grid-cols-2 gap-4">
        {qaAuditors.map((auditor, i) => {
          const isSelected = selectedAuditor?.id === auditor.id;
          const hasIssues = auditor.openedAndLeft > 0 || auditor.productivity < 70 || auditor.idleTime > "1:00";
          const evalsForAuditor = qaEvaluations.filter((e) => e.auditorId === auditor.id);
          const completedEvals = evalsForAuditor.filter((e) => e.actuallyEvaluated);
          const incompleteEvals = evalsForAuditor.filter((e) => !e.actuallyEvaluated);

          return (
            <motion.div
              key={auditor.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card
                className={`border-border/40 cursor-pointer transition-all hover:border-primary/30 ${
                  isSelected ? "border-primary/50 ring-1 ring-primary/20" : ""
                } ${hasIssues ? "border-s-2 border-s-red-500/50" : "border-s-2 border-s-emerald-500/50"}`}
                onClick={() => setSelectedAuditor(isSelected ? null : auditor)}
              >
                <CardContent className="p-4 space-y-4">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-11 h-11 border-2 border-border/40">
                        <AvatarFallback className="bg-primary/10 text-primary text-sm">{auditor.avatar}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-sm text-foreground">{auditor.name}</p>
                        <p className="text-[10px] text-muted-foreground">مدقق جودة</p>
                      </div>
                    </div>
                    <div className="text-end">
                      <div className={`text-lg ${
                        auditor.productivity >= 90 ? "text-emerald-500"
                          : auditor.productivity >= 70 ? "text-yellow-500"
                          : "text-red-500"
                      }`}>
                        {auditor.productivity}%
                      </div>
                      <p className="text-[9px] text-muted-foreground">إنتاجية</p>
                    </div>
                  </div>

                  {/* Productivity Bar */}
                  <div>
                    <Progress
                      value={auditor.productivity}
                      className={`h-2 ${
                        auditor.productivity >= 90 ? "[&>[data-slot=progress-indicator]]:bg-emerald-500 bg-emerald-500/20"
                          : auditor.productivity >= 70 ? "[&>[data-slot=progress-indicator]]:bg-yellow-500 bg-yellow-500/20"
                          : "[&>[data-slot=progress-indicator]]:bg-red-500 bg-red-500/20"
                      }`}
                    />
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="p-2 rounded-md bg-muted/20 text-center">
                      <Headphones className="w-3.5 h-3.5 mx-auto text-violet-500 mb-1" />
                      <p className="text-sm text-foreground">{getEvalCount(auditor)}</p>
                      <p className="text-[8px] text-muted-foreground">تقييم</p>
                    </div>
                    <div className="p-2 rounded-md bg-muted/20 text-center">
                      <Timer className="w-3.5 h-3.5 mx-auto text-blue-500 mb-1" />
                      <p className="text-sm text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {Math.floor(auditor.avgListenDuration / 60)}:{String(auditor.avgListenDuration % 60).padStart(2, "0")}
                      </p>
                      <p className="text-[8px] text-muted-foreground">متوسط الاستماع</p>
                    </div>
                    <div className="p-2 rounded-md bg-muted/20 text-center">
                      <Star className="w-3.5 h-3.5 mx-auto text-primary mb-1" />
                      <p className="text-sm text-foreground">{auditor.avgScore}</p>
                      <p className="text-[8px] text-muted-foreground">متوسط الدرجة</p>
                    </div>
                  </div>

                  {/* Time Usage */}
                  <div className="grid grid-cols-4 gap-2 text-center">
                    <div>
                      <p className="text-[9px] text-muted-foreground">دخول</p>
                      <p className="text-xs text-foreground">{auditor.loginTime}</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-muted-foreground">خروج</p>
                      <p className="text-xs text-foreground">{auditor.logoutTime || "—"}</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-muted-foreground">نشط</p>
                      <p className="text-xs text-emerald-500">{auditor.activeTime}</p>
                    </div>
                    <div>
                      <p className="text-[9px] text-muted-foreground">خامل</p>
                      <p className={`text-xs ${auditor.idleTime > "1:00" ? "text-red-500" : "text-muted-foreground"}`}>
                        {auditor.idleTime}
                      </p>
                    </div>
                  </div>

                  {/* Quality indicators */}
                  <div className="flex items-center justify-between text-[10px] pt-2 border-t border-border/20">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1 text-emerald-500">
                        <CheckCircle2 className="w-3 h-3" />
                        {auditor.withNotes} بملاحظات
                      </span>
                      <span className="flex items-center gap-1 text-yellow-500">
                        <FileText className="w-3 h-3" />
                        {auditor.withoutNotes} بدون ملاحظات
                      </span>
                    </div>
                    {auditor.openedAndLeft > 0 && (
                      <span className="flex items-center gap-1 text-red-500">
                        <XCircle className="w-3 h-3" />
                        {auditor.openedAndLeft} فتح وطلع
                      </span>
                    )}
                  </div>

                  {/* Issues/Alerts */}
                  {hasIssues && (
                    <div className="p-2 rounded-lg bg-red-500/5 border border-red-500/20 space-y-1">
                      <p className="text-[10px] text-red-500 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        تنبيهات:
                      </p>
                      {auditor.openedAndLeft > 0 && (
                        <p className="text-[9px] text-red-400 ps-4">• فتح {auditor.openedAndLeft} مكالمة بدون تقييم</p>
                      )}
                      {auditor.productivity < 70 && (
                        <p className="text-[9px] text-red-400 ps-4">• إنتاجية منخفضة ({auditor.productivity}%)</p>
                      )}
                      {auditor.idleTime > "1:00" && (
                        <p className="text-[9px] text-red-400 ps-4">• وقت خمول مرتفع ({auditor.idleTime})</p>
                      )}
                    </div>
                  )}

                  {/* Detailed messages/conversations reviewed */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 rounded-md bg-muted/10 border border-border/20">
                      <div className="flex items-center gap-1.5 mb-1">
                        <MessageSquare className="w-3 h-3 text-cyan-500" />
                        <span className="text-[9px] text-muted-foreground">رسائل راجعها</span>
                      </div>
                      <p className="text-sm text-foreground">{auditor.messagesReviewed}</p>
                    </div>
                    <div className="p-2 rounded-md bg-muted/10 border border-border/20">
                      <div className="flex items-center gap-1.5 mb-1">
                        <MessageSquare className="w-3 h-3 text-violet-500" />
                        <span className="text-[9px] text-muted-foreground">محادثات كاملة</span>
                      </div>
                      <p className="text-sm text-foreground">{auditor.conversationsReviewed}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Comparison */}
      <Card className="border-border/40">
        <CardContent className="p-4">
          <h4 className="text-xs text-foreground flex items-center gap-1.5 mb-3">
            <BarChart3 className="w-3.5 h-3.5 text-primary" />
            مقارنة أداء المدققين
          </h4>
          <div className="space-y-3">
            {qaAuditors.map((auditor) => (
              <div key={auditor.id} className="flex items-center gap-3">
                <Avatar className="w-7 h-7 border border-border/30 shrink-0">
                  <AvatarFallback className="bg-primary/10 text-primary text-[8px]">{auditor.avatar}</AvatarFallback>
                </Avatar>
                <span className="text-xs text-foreground w-24 truncate">{auditor.name}</span>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] text-muted-foreground w-14 shrink-0">إنتاجية</span>
                    <div className="flex-1">
                      <Progress
                        value={auditor.productivity}
                        className={`h-1.5 ${
                          auditor.productivity >= 90 ? "[&>[data-slot=progress-indicator]]:bg-emerald-500 bg-emerald-500/20"
                            : auditor.productivity >= 70 ? "[&>[data-slot=progress-indicator]]:bg-yellow-500 bg-yellow-500/20"
                            : "[&>[data-slot=progress-indicator]]:bg-red-500 bg-red-500/20"
                        }`}
                      />
                    </div>
                    <span className="text-[9px] text-muted-foreground w-8 text-end">{auditor.productivity}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] text-muted-foreground w-14 shrink-0">م. ال��رجة</span>
                    <div className="flex-1">
                      <Progress
                        value={auditor.avgScore}
                        className={`h-1.5 ${
                          auditor.avgScore >= 85 ? "[&>[data-slot=progress-indicator]]:bg-blue-500 bg-blue-500/20"
                            : "[&>[data-slot=progress-indicator]]:bg-yellow-500 bg-yellow-500/20"
                        }`}
                      />
                    </div>
                    <span className="text-[9px] text-muted-foreground w-8 text-end">{auditor.avgScore}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Fair monitoring note */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-3 flex items-center gap-3">
          <Eye className="w-4 h-4 text-primary shrink-0" />
          <p className="text-[10px] text-muted-foreground">
            <span className="text-primary">نفس المنطق يُطبق على الجميع (عدالة كاملة):</span>{" "}
            Agent → رسائل + سرعة + مكالمات + وقت فعلي • Supervisor → تدخلات + مشاكل محلولة + نقل + قواعد • Manager → قرارات + موافقات + مدة استخدام • لا أحد فوق النظام.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
