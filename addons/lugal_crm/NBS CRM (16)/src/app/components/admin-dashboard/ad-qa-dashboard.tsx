import { useState } from "react";
import { motion } from "motion/react";
import {
  Headphones, MessageSquare, Star, FileText, Clock,
  Eye, Volume2, CheckCircle2, XCircle, AlertTriangle,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { ScrollArea } from "../ui/scroll-area";
import { Progress } from "../ui/progress";
import { qaEvaluations, type QAEvaluation } from "./ad-data";

export function ADQaDashboard() {
  const [selectedEval, setSelectedEval] = useState<QAEvaluation | null>(null);

  const totalEvals = qaEvaluations.length;
  const completed = qaEvaluations.filter((e) => e.actuallyEvaluated);
  const incomplete = qaEvaluations.filter((e) => !e.actuallyEvaluated);
  const avgScore = completed.length > 0
    ? Math.round(completed.reduce((s, e) => s + e.score, 0) / completed.length)
    : 0;
  const totalListenSec = qaEvaluations.reduce((s, e) => s + e.listenDuration, 0);
  const totalListenMin = Math.floor(totalListenSec / 60);

  return (
    <div className="space-y-4">
      {/* Notice */}
      <Card className="border-cyan-500/20 bg-cyan-500/5">
        <CardContent className="p-3 flex items-center gap-3">
          <Eye className="w-4 h-4 text-cyan-500 shrink-0" />
          <p className="text-xs text-muted-foreground">
            <span className="text-cyan-500">عين رقابية فقط</span> — المدقق يسمع المكالمات ويراجع الرسائل ويقيّم ويكتب ملاحظات. ممنوع: الرد على الزبون، تغيير حالة، تعديل بيانات، حذف أي شيء.
          </p>
        </CardContent>
      </Card>

      {/* KPIs */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: "إجمالي التقييمات", value: totalEvals, icon: Star, color: "text-primary" },
          { label: "مكتملة", value: completed.length, icon: CheckCircle2, color: "text-emerald-500" },
          { label: "فتح بدون تقييم", value: incomplete.length, icon: XCircle, color: "text-red-500" },
          { label: "متوسط الدرجة", value: `${avgScore}/100`, icon: FileText, color: "text-blue-500" },
          { label: "مدة الاستماع", value: `${totalListenMin} دقيقة`, icon: Headphones, color: "text-violet-500" },
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

      <div className="grid grid-cols-5 gap-4">
        {/* Evaluations List */}
        <div className="col-span-3">
          <Card className="border-border/40">
            <div className="p-3 border-b border-border/30">
              <h4 className="text-xs text-foreground flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5 text-primary" />
                سجل التقييمات
              </h4>
            </div>
            <ScrollArea className="max-h-[calc(100vh-460px)]" dir="rtl">
              <div className="divide-y divide-border/20">
                {qaEvaluations.map((ev, i) => {
                  const isSelected = selectedEval?.id === ev.id;
                  return (
                    <motion.div
                      key={ev.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => setSelectedEval(ev)}
                      className={`p-3 cursor-pointer transition-colors hover:bg-muted/10 ${isSelected ? "bg-primary/5 border-e-2 border-primary" : ""}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2.5">
                          <Avatar className="w-8 h-8 border border-border/40">
                            <AvatarFallback className="bg-primary/10 text-primary text-[9px]">
                              {ev.auditorName.slice(0, 2)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-xs text-foreground">{ev.auditorName}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <Badge className={`text-[8px] border-transparent ${
                                ev.targetType === "call" ? "bg-violet-500/10 text-violet-500"
                                  : "bg-cyan-500/10 text-cyan-500"
                              }`}>
                                {ev.targetType === "call" ? "مكالمة" : "محادثة"}
                              </Badge>
                              <span className="text-[9px] text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                                {ev.targetId}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="text-end">
                          {ev.actuallyEvaluated ? (
                            <div className="flex items-center gap-1.5">
                              <span className={`text-sm ${
                                ev.score >= 90 ? "text-emerald-500"
                                  : ev.score >= 75 ? "text-yellow-500"
                                  : "text-red-500"
                              }`}>
                                {ev.score}
                              </span>
                              <span className="text-[9px] text-muted-foreground">/100</span>
                            </div>
                          ) : (
                            <Badge className="bg-red-500/10 text-red-500 text-[8px] border-transparent">
                              <XCircle className="w-2.5 h-2.5 me-0.5" />
                              بدون تقييم
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-3 mt-2 text-[9px] text-muted-foreground">
                        <span>الوكيل: {ev.targetAgent}</span>
                        <span>•</span>
                        <span>الزبون: {ev.customerName}</span>
                        <span>•</span>
                        <span className="flex items-center gap-0.5">
                          <Volume2 className="w-2.5 h-2.5" />
                          {ev.listenDuration > 60
                            ? `${Math.floor(ev.listenDuration / 60)}:${String(ev.listenDuration % 60).padStart(2, "0")} دقيقة`
                            : `${ev.listenDuration} ثانية`
                          }
                        </span>
                        {ev.hasNotes && (
                          <>
                            <span>•</span>
                            <span className="text-emerald-500 flex items-center gap-0.5">
                              <FileText className="w-2.5 h-2.5" />
                              ملاحظات
                            </span>
                          </>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </ScrollArea>
          </Card>
        </div>

        {/* Evaluation Detail */}
        <div className="col-span-2">
          {selectedEval ? (
            <Card className="border-border/40 sticky top-0">
              <div className="p-3 border-b border-border/30">
                <h4 className="text-xs text-foreground">تفاصيل التقييم</h4>
              </div>
              <ScrollArea className="max-h-[calc(100vh-460px)]" dir="rtl">
                <div className="p-4 space-y-4">
                  {/* Target info */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-2.5 rounded-lg bg-muted/20">
                      <p className="text-[9px] text-muted-foreground">المدقق</p>
                      <p className="text-xs text-foreground">{selectedEval.auditorName}</p>
                    </div>
                    <div className="p-2.5 rounded-lg bg-muted/20">
                      <p className="text-[9px] text-muted-foreground">الوكيل</p>
                      <p className="text-xs text-foreground">{selectedEval.targetAgent}</p>
                    </div>
                    <div className="p-2.5 rounded-lg bg-muted/20">
                      <p className="text-[9px] text-muted-foreground">الزبون</p>
                      <p className="text-xs text-foreground">{selectedEval.customerName}</p>
                    </div>
                    <div className="p-2.5 rounded-lg bg-muted/20">
                      <p className="text-[9px] text-muted-foreground">مدة الاستماع</p>
                      <p className="text-xs text-foreground">
                        {selectedEval.listenDuration > 60
                          ? `${Math.floor(selectedEval.listenDuration / 60)} د ${selectedEval.listenDuration % 60} ث`
                          : `${selectedEval.listenDuration} ثانية`
                        }
                      </p>
                    </div>
                  </div>

                  {/* Score */}
                  {selectedEval.actuallyEvaluated ? (
                    <>
                      <div className="text-center p-4 rounded-xl bg-muted/10 border border-border/30">
                        <p className={`text-3xl ${
                          selectedEval.score >= 90 ? "text-emerald-500"
                            : selectedEval.score >= 75 ? "text-yellow-500"
                            : "text-red-500"
                        }`}>
                          {selectedEval.score}<span className="text-sm text-muted-foreground">/{selectedEval.maxScore}</span>
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-1">الدرجة الإجمالية</p>
                      </div>

                      {/* Criteria */}
                      <div className="space-y-2.5">
                        <p className="text-[10px] text-muted-foreground">التفصيل:</p>
                        {selectedEval.criteria.map((c, ci) => (
                          <div key={ci} className="space-y-1">
                            <div className="flex items-center justify-between text-[10px]">
                              <span className="text-foreground">{c.name}</span>
                              <span className={`${
                                c.score / c.max >= 0.9 ? "text-emerald-500"
                                  : c.score / c.max >= 0.7 ? "text-yellow-500"
                                  : "text-red-500"
                              }`}>
                                {c.score}/{c.max}
                              </span>
                            </div>
                            <Progress
                              value={(c.score / c.max) * 100}
                              className={`h-1.5 ${
                                c.score / c.max >= 0.9 ? "[&>[data-slot=progress-indicator]]:bg-emerald-500 bg-emerald-500/20"
                                  : c.score / c.max >= 0.7 ? "[&>[data-slot=progress-indicator]]:bg-yellow-500 bg-yellow-500/20"
                                  : "[&>[data-slot=progress-indicator]]:bg-red-500 bg-red-500/20"
                              }`}
                            />
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="text-center p-6 rounded-xl bg-red-500/5 border border-red-500/20">
                      <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                      <p className="text-sm text-red-500">فتح بدون تقييم</p>
                      <p className="text-[10px] text-muted-foreground mt-1">
                        استمع {selectedEval.listenDuration} ثانية فقط ثم أغلق
                      </p>
                    </div>
                  )}

                  {/* Notes */}
                  {selectedEval.notes && (
                    <div className="p-3 rounded-lg bg-muted/20 border border-border/30">
                      <p className="text-[10px] text-muted-foreground mb-1">ملاحظات المدقق:</p>
                      <p className="text-xs text-foreground">{selectedEval.notes}</p>
                    </div>
                  )}

                  <p className="text-[9px] text-muted-foreground text-center">
                    {selectedEval.evaluatedAt}
                  </p>
                </div>
              </ScrollArea>
            </Card>
          ) : (
            <Card className="border-border/40 h-full flex items-center justify-center">
              <CardContent className="p-8 text-center">
                <Eye className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">اختر تقييماً لعرض التفاصيل</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
