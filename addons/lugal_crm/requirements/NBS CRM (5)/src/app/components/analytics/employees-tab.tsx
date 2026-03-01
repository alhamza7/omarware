import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Progress } from "../ui/progress";
import { Button } from "../ui/button";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
} from "recharts";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../ui/select";
import {
  MessageCircle, Phone, Clock, CheckCircle2, AlertTriangle,
  ShoppingBag, Star, ChevronDown, ChevronUp, Shield, TrendingUp, Zap,
} from "lucide-react";
import { employeeStats, kpiTierConfig } from "./analytics-data";
import type { EmployeeStat } from "./analytics-data";

type SortKey = "kpiScore" | "frtMinutes" | "ttrHours" | "totalMessages" | "conversionsOrders" | "satisfactionScore";

export function EmployeesTab() {
  const [sortBy, setSortBy] = useState<SortKey>("kpiScore");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const sorted = [...employeeStats].sort((a, b) => {
    const diff = a[sortBy] - b[sortBy];
    return sortDir === "desc" ? -diff : diff;
  });

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortBy(key); setSortDir("desc"); }
  };

  const SortIcon = ({ field }: { field: SortKey }) => {
    if (sortBy !== field) return null;
    return sortDir === "desc" ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />;
  };

  // Radar data for selected employee
  const getRadarData = (emp: EmployeeStat) => [
    { metric: "الاستجابة", value: Math.max(0, 100 - emp.frtMinutes * 10), fullMark: 100 },
    { metric: "الحل", value: Math.max(0, 100 - emp.ttrHours * 8), fullMark: 100 },
    { metric: "التحويلات", value: Math.min(100, (emp.conversionsOrders / 2) ), fullMark: 100 },
    { metric: "الرضا", value: emp.satisfactionScore * 20, fullMark: 100 },
    { metric: "التوفر", value: emp.availabilityRate, fullMark: 100 },
    { metric: "الكفاءة", value: (emp.answeredMessages / emp.totalMessages) * 100, fullMark: 100 },
  ];

  // Bar chart data
  const barData = employeeStats.map(e => ({
    name: e.name.split(" ").slice(0, 2).join(" "),
    رسائل: e.answeredMessages,
    مكالمات: e.answeredCalls,
    تحويلات: e.conversionsOrders + e.conversionsQuotations,
  }));

  return (
    <div className="space-y-6">
      {/* KPI Tier Legend */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
            <CardTitle className="text-sm">نموذج KPI العادل (غير عقابي، واعي بالأداء)</CardTitle>
          </div>
          <CardDescription className="text-[10px]">
            يقيّم الأداء بناءً على عوامل متعددة دون عقوبات - يركز على التطوير والدعم
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {Object.entries(kpiTierConfig).map(([key, tier]) => (
              <div key={key} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${tier.bg}`}>
                <div className={`w-2 h-2 rounded-full ${tier.color.replace("text-", "bg-")}`} />
                <span className={`text-[10px] ${tier.color}`}>{tier.label}</span>
                <span className="text-[9px] text-muted-foreground font-mono">({tier.range})</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Overview Bar Chart */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">مقارنة أداء الموظفين</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 9 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <ReTooltip
                  contentStyle={{
                    backgroundColor: "var(--card)", border: "1px solid var(--border)",
                    borderRadius: 12, fontSize: 11, direction: "rtl",
                  }}
                />
                <Bar dataKey="رسائل" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="مكالمات" fill="var(--chart-3)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="تحويلات" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Employee Table */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">تفاصيل أداء الموظفين</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/40 bg-muted/20">
                  <th className="text-right p-3 min-w-[160px]">الموظف</th>
                  <th className="text-right p-3 cursor-pointer hover:text-primary transition-colors" onClick={() => toggleSort("totalMessages")}>
                    <div className="flex items-center gap-1">الرسائل <SortIcon field="totalMessages" /></div>
                  </th>
                  <th className="text-right p-3">المكالمات</th>
                  <th className="text-right p-3 cursor-pointer hover:text-primary transition-colors" onClick={() => toggleSort("frtMinutes")}>
                    <div className="flex items-center gap-1">FRT <SortIcon field="frtMinutes" /></div>
                  </th>
                  <th className="text-right p-3 cursor-pointer hover:text-primary transition-colors" onClick={() => toggleSort("ttrHours")}>
                    <div className="flex items-center gap-1">TTR <SortIcon field="ttrHours" /></div>
                  </th>
                  <th className="text-right p-3">التأخيرات</th>
                  <th className="text-right p-3 cursor-pointer hover:text-primary transition-colors" onClick={() => toggleSort("conversionsOrders")}>
                    <div className="flex items-center gap-1">التحويلات <SortIcon field="conversionsOrders" /></div>
                  </th>
                  <th className="text-right p-3 cursor-pointer hover:text-primary transition-colors" onClick={() => toggleSort("satisfactionScore")}>
                    <div className="flex items-center gap-1">الرضا <SortIcon field="satisfactionScore" /></div>
                  </th>
                  <th className="text-right p-3 cursor-pointer hover:text-primary transition-colors" onClick={() => toggleSort("kpiScore")}>
                    <div className="flex items-center gap-1">KPI <SortIcon field="kpiScore" /></div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {sorted.flatMap(emp => {
                  const tier = kpiTierConfig[emp.kpiTier];
                  const isExpanded = expandedId === emp.id;
                  const rows = [
                    <tr
                      key={emp.id}
                      className="border-b border-border/20 hover:bg-primary/5 transition-colors cursor-pointer"
                      onClick={() => setExpandedId(isExpanded ? null : emp.id)}
                    >
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Avatar className="h-7 w-7 border border-border/50">
                            <AvatarFallback className="bg-primary/10 text-primary text-[9px]">{emp.avatar}</AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-foreground text-[11px]">{emp.name}</p>
                            <p className="text-[9px] text-muted-foreground">{emp.branch}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="font-mono">
                          <span className="text-foreground">{emp.answeredMessages.toLocaleString()}</span>
                          <span className="text-muted-foreground">/{emp.totalMessages.toLocaleString()}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="font-mono">
                          <span className="text-foreground">{emp.answeredCalls}</span>
                          <span className="text-muted-foreground">/{emp.totalCalls}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <Badge className={`text-[10px] font-mono ${emp.frtMinutes <= 2 ? 'bg-green-500/10 text-green-500' : emp.frtMinutes <= 4 ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive'}`}>
                          {emp.frtMinutes} د
                        </Badge>
                      </td>
                      <td className="p-3">
                        <Badge className={`text-[10px] font-mono ${emp.ttrHours <= 2.5 ? 'bg-green-500/10 text-green-500' : emp.ttrHours <= 4 ? 'bg-primary/10 text-primary' : 'bg-destructive/10 text-destructive'}`}>
                          {emp.ttrHours} س
                        </Badge>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2 font-mono">
                          <span className={emp.lateMessages > 30 ? 'text-destructive' : 'text-muted-foreground'}>{emp.lateMessages} رسالة</span>
                          <span className="text-muted-foreground/50">|</span>
                          <span className={emp.lateCalls > 10 ? 'text-destructive' : 'text-muted-foreground'}>{emp.lateCalls} مكالمة</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="font-mono">
                          <span className="text-primary">{emp.conversionsOrders}</span>
                          <span className="text-muted-foreground"> + {emp.conversionsQuotations}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1">
                          <Star className="w-3 h-3 text-primary fill-primary" />
                          <span className="font-mono">{emp.satisfactionScore}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16">
                            <Progress value={emp.kpiScore} className="h-1.5" />
                          </div>
                          <Badge className={`text-[9px] border ${tier.bg} ${tier.color}`}>
                            {emp.kpiScore} - {tier.label}
                          </Badge>
                        </div>
                      </td>
                    </tr>
                  ];

                  // Expanded Detail Row
                  if (isExpanded) {
                    rows.push(
                      <tr key={`${emp.id}-detail`} className="bg-muted/10">
                        <td colSpan={9} className="p-4">
                          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                            {/* Radar Chart */}
                            <div className="lg:col-span-1">
                              <p className="text-[10px] text-muted-foreground mb-2">ملف الأداء</p>
                              <div className="h-[200px]">
                                <ResponsiveContainer width="100%" height="100%">
                                  <RadarChart data={getRadarData(emp)}>
                                    <PolarGrid stroke="var(--border)" />
                                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 9 }} stroke="var(--muted-foreground)" />
                                    <PolarRadiusAxis tick={false} domain={[0, 100]} />
                                    <Radar name="الأداء" dataKey="value" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.2} strokeWidth={2} />
                                  </RadarChart>
                                </ResponsiveContainer>
                              </div>
                            </div>

                            {/* Detail Stats */}
                            <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-3">
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <MessageCircle className="w-3 h-3 text-green-500" />
                                  <span className="text-[9px] text-muted-foreground">معدل الرد على الرسائل</span>
                                </div>
                                <p className="font-mono text-foreground">{((emp.answeredMessages / emp.totalMessages) * 100).toFixed(1)}%</p>
                              </div>
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <Phone className="w-3 h-3 text-blue-500" />
                                  <span className="text-[9px] text-muted-foreground">معدل الرد على المكالمات</span>
                                </div>
                                <p className="font-mono text-foreground">{((emp.answeredCalls / emp.totalCalls) * 100).toFixed(1)}%</p>
                              </div>
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <Clock className="w-3 h-3 text-primary" />
                                  <span className="text-[9px] text-muted-foreground">متوسط وقت الاستجابة</span>
                                </div>
                                <p className="font-mono text-foreground">{emp.frtMinutes} دقيقة</p>
                              </div>
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <CheckCircle2 className="w-3 h-3 text-green-500" />
                                  <span className="text-[9px] text-muted-foreground">متوسط وقت الحل</span>
                                </div>
                                <p className="font-mono text-foreground">{emp.ttrHours} ساعة</p>
                              </div>
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <AlertTriangle className="w-3 h-3 text-destructive" />
                                  <span className="text-[9px] text-muted-foreground">رسائل متأخرة</span>
                                </div>
                                <p className="font-mono text-foreground">{emp.lateMessages}</p>
                              </div>
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <AlertTriangle className="w-3 h-3 text-destructive" />
                                  <span className="text-[9px] text-muted-foreground">مكالمات فائتة</span>
                                </div>
                                <p className="font-mono text-foreground">{emp.lateCalls}</p>
                              </div>
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <ShoppingBag className="w-3 h-3 text-primary" />
                                  <span className="text-[9px] text-muted-foreground">تحويل لطلبات</span>
                                </div>
                                <p className="font-mono text-primary">{emp.conversionsOrders}</p>
                              </div>
                              <div className="p-3 rounded-lg bg-card/50 border border-border/30">
                                <div className="flex items-center gap-1.5 mb-1">
                                  <Zap className="w-3 h-3 text-purple-500" />
                                  <span className="text-[9px] text-muted-foreground">بمساعدة AI</span>
                                </div>
                                <p className="font-mono text-foreground">{emp.aiAssisted}</p>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  }
                  return rows;
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}