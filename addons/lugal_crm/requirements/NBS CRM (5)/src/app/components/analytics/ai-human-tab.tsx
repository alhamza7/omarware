import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
  ResponsiveContainer, LineChart, Line, Legend, AreaChart, Area,
} from "recharts";
import {
  Bot, User, Zap, Clock, Star, TrendingUp, DollarSign, ArrowUpDown,
} from "lucide-react";
import { aiHumanStats, aiHumanTimeSeries } from "./analytics-data";

export function AiHumanTab() {
  // Comparison bar data
  const comparisonData = aiHumanStats
    .filter(s => s.category !== "avg_response_sec" && s.category !== "satisfaction" && s.category !== "cost_per_interaction")
    .map(s => ({
      name: s.categoryAr,
      "ذكاء اصطناعي": s.ai,
      بشري: s.human,
    }));

  const aiTotal = aiHumanStats.find(s => s.category === "total_interactions")!;
  const aiResolved = aiHumanStats.find(s => s.category === "resolved_first_contact")!;
  const aiResponse = aiHumanStats.find(s => s.category === "avg_response_sec")!;
  const aiSatisfaction = aiHumanStats.find(s => s.category === "satisfaction")!;
  const aiCost = aiHumanStats.find(s => s.category === "cost_per_interaction")!;
  const aiEscalated = aiHumanStats.find(s => s.category === "escalated")!;

  const totalAll = aiTotal.ai + aiTotal.human;
  const aiPercent = ((aiTotal.ai / totalAll) * 100).toFixed(1);
  const humanPercent = ((aiTotal.human / totalAll) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Header comparison cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* AI Card */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40 border-blue-500/20">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-500">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm text-foreground">الذكاء الاصطناعي</p>
                <p className="text-[10px] text-muted-foreground">{aiPercent}% من إجمالي التفاعلات</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">التفاعلات</p>
                <p className="font-mono text-lg text-foreground">{aiTotal.ai.toLocaleString()}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">حل من أول تواصل</p>
                <p className="font-mono text-lg text-green-500">{aiResolved.ai.toLocaleString()}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">متوسط الاستجابة</p>
                <p className="font-mono text-lg text-blue-500">{aiResponse.ai} ثانية</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">رضا العملاء</p>
                <div className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-primary fill-primary" />
                  <p className="font-mono text-lg text-foreground">{aiSatisfaction.ai}</p>
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">التصعيدات</p>
                <p className="font-mono text-lg text-destructive">{aiEscalated.ai.toLocaleString()}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">التكلفة/تفاعل</p>
                <p className="font-mono text-lg text-primary">{aiCost.ai} ر.س</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Human Card */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40 border-primary/20">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                <User className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm text-foreground">الوكلاء البشريون</p>
                <p className="text-[10px] text-muted-foreground">{humanPercent}% من إجمالي التفاعلات</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">التفاعلات</p>
                <p className="font-mono text-lg text-foreground">{aiTotal.human.toLocaleString()}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">حل من أول تواصل</p>
                <p className="font-mono text-lg text-green-500">{aiResolved.human.toLocaleString()}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">متوسط الاستجابة</p>
                <p className="font-mono text-lg text-blue-500">{aiResponse.human} ثانية</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">رضا العملاء</p>
                <div className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-primary fill-primary" />
                  <p className="font-mono text-lg text-foreground">{aiSatisfaction.human}</p>
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">التصعيدات</p>
                <p className="font-mono text-lg text-destructive">{aiEscalated.human.toLocaleString()}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-muted/20 border border-border/20">
                <p className="text-[9px] text-muted-foreground">التكلفة/تفاعل</p>
                <p className="font-mono text-lg text-primary">{aiCost.human} ر.س</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trend Chart - AI vs Human over time */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">تطور التفاعلات - AI مقابل البشري</CardTitle>
          <CardDescription className="text-[10px]">
            نلاحظ تزايد اعتماد AI بمرور الوقت مع استمرار تفوق البشر في الرضا
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={aiHumanTimeSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="period" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <ReTooltip
                  contentStyle={{
                    backgroundColor: "var(--card)", border: "1px solid var(--border)",
                    borderRadius: 12, fontSize: 11, direction: "rtl",
                  }}
                />
                <Area type="monotone" dataKey="aiInteractions" name="AI تفاعلات" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.15} strokeWidth={2} />
                <Area type="monotone" dataKey="humanInteractions" name="بشري تفاعلات" stroke="var(--primary)" fill="var(--primary)" fillOpacity={0.15} strokeWidth={2} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Resolution Rate Trend */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">تطور نسبة الحل (%)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={aiHumanTimeSeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="period" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" domain={[70, 100]} />
                <ReTooltip
                  contentStyle={{
                    backgroundColor: "var(--card)", border: "1px solid var(--border)",
                    borderRadius: 12, fontSize: 11, direction: "rtl",
                  }}
                />
                <Line type="monotone" dataKey="aiResolution" name="AI %" stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="humanResolution" name="بشري %" stroke="var(--primary)" strokeWidth={2.5} dot={{ r: 3 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Cost Savings Summary */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40 border-green-500/20">
        <CardContent className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-xl bg-green-500/10 text-green-500">
              <DollarSign className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm text-foreground">التوفير المقدّر من AI</p>
              <p className="text-[10px] text-muted-foreground">بناءً على فرق التكلفة لكل تفاعل</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 rounded-lg bg-muted/20 border border-border/20">
              <p className="text-[9px] text-muted-foreground">التوفير الشهري</p>
              <p className="text-xl font-mono text-green-500">
                {((aiTotal.ai * (aiCost.human - aiCost.ai)) / 12).toLocaleString(undefined, { maximumFractionDigits: 0 })} ر.س
              </p>
            </div>
            <div className="text-center p-3 rounded-lg bg-muted/20 border border-border/20">
              <p className="text-[9px] text-muted-foreground">التوفير السنوي</p>
              <p className="text-xl font-mono text-green-500">
                {(aiTotal.ai * (aiCost.human - aiCost.ai)).toLocaleString(undefined, { maximumFractionDigits: 0 })} ر.س
              </p>
            </div>
            <div className="text-center p-3 rounded-lg bg-muted/20 border border-border/20">
              <p className="text-[9px] text-muted-foreground">نسبة خفض التكلفة</p>
              <p className="text-xl font-mono text-green-500">
                {(((aiCost.human - aiCost.ai) / aiCost.human) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
