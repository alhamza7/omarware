import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Progress } from "../ui/progress";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import {
  Crown, Shield, Star, Clock, TrendingUp, Users, DollarSign, Heart,
  MessageCircle,
} from "lucide-react";
import { vipStats, vipHandlingByAgent, vipByChannel } from "./analytics-data";

export function VipTab() {
  const agentBarData = vipHandlingByAgent.map(a => ({
    name: a.name.split(" ").slice(0, 2).join(" "),
    التفاعلات: a.interactions,
    محلولة: a.resolved,
  }));

  const channelPieData = vipByChannel.map(c => ({
    name: c.channelAr,
    value: c.count,
  }));
  const channelColors = ["#25D366", "#8B5CF6", "#EA4335", "#06B6D4", "#E1306C"];

  return (
    <div className="space-y-6">
      {/* VIP KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          { icon: <Crown className="w-5 h-5" />, label: "عملاء VIP", value: vipStats.totalVip.toString(), color: "text-primary", bg: "bg-primary/10" },
          { icon: <MessageCircle className="w-5 h-5" />, label: "إجمالي التفاعلات", value: vipStats.totalInteractions.toLocaleString(), color: "text-blue-500", bg: "bg-blue-500/10" },
          { icon: <Clock className="w-5 h-5" />, label: "متوسط الاستجابة", value: `${vipStats.avgResponseTime} د`, color: "text-green-500", bg: "bg-green-500/10" },
          { icon: <Star className="w-5 h-5" />, label: "رضا VIP", value: vipStats.satisfaction.toString(), color: "text-primary", bg: "bg-primary/10" },
          { icon: <DollarSign className="w-5 h-5" />, label: "حصة الإيرادات", value: `${vipStats.revenueShare}%`, color: "text-purple-500", bg: "bg-purple-500/10" },
        ].map((kpi, i) => (
          <Card key={i} className="bg-card/30 backdrop-blur-md border-border/40">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-xl ${kpi.bg} ${kpi.color}`}>{kpi.icon}</div>
                <div>
                  <p className="text-[10px] text-muted-foreground">{kpi.label}</p>
                  <p className="text-xl font-mono text-foreground">{kpi.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Additional VIP metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card/30 backdrop-blur-md border-border/40 border-primary/20">
          <CardContent className="p-4 text-center">
            <Heart className="w-6 h-6 text-primary mx-auto mb-2" />
            <p className="text-2xl font-mono text-foreground">{vipStats.retentionRate}%</p>
            <p className="text-[10px] text-muted-foreground">معدل الاحتفاظ</p>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4 text-center">
            <Clock className="w-6 h-6 text-green-500 mx-auto mb-2" />
            <p className="text-2xl font-mono text-foreground">{vipStats.avgResolutionTime} س</p>
            <p className="text-[10px] text-muted-foreground">متوسط وقت الحل</p>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4 text-center">
            <TrendingUp className="w-6 h-6 text-destructive mx-auto mb-2" />
            <p className="text-2xl font-mono text-foreground">{vipStats.escalations}</p>
            <p className="text-[10px] text-muted-foreground">تصعيدات</p>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4 text-center">
            <Shield className="w-6 h-6 text-purple-500 mx-auto mb-2" />
            <p className="text-2xl font-mono text-foreground">{vipStats.dedicatedAgents}</p>
            <p className="text-[10px] text-muted-foreground">وكلاء مخصصون</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* VIP Handling by Agent */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">أداء الوكلاء مع عملاء VIP</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agentBarData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                  <YAxis tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                  <ReTooltip
                    contentStyle={{
                      backgroundColor: "var(--card)", border: "1px solid var(--border)",
                      borderRadius: 12, fontSize: 11, direction: "rtl",
                    }}
                  />
                  <Bar dataKey="التفاعلات" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="محلولة" fill="var(--chart-3)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* VIP by Channel */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">تفاعلات VIP حسب القناة</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={channelPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={{ stroke: "var(--muted-foreground)", strokeWidth: 0.5 }}
                  >
                    {channelPieData.map((_, i) => (
                      <Cell key={i} fill={channelColors[i]} opacity={0.85} />
                    ))}
                  </Pie>
                  <ReTooltip
                    contentStyle={{
                      backgroundColor: "var(--card)", border: "1px solid var(--border)",
                      borderRadius: 12, fontSize: 11, direction: "rtl",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Detail Table */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">تفاصيل أداء وكلاء VIP</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/40 bg-muted/20">
                  <th className="text-right p-3">الوكيل</th>
                  <th className="text-right p-3">التفاعلات</th>
                  <th className="text-right p-3">المحلولة</th>
                  <th className="text-right p-3">نسبة الحل</th>
                  <th className="text-right p-3">FRT</th>
                  <th className="text-right p-3">رضا العملاء</th>
                </tr>
              </thead>
              <tbody>
                {vipHandlingByAgent.map((a, i) => {
                  const resolveRate = ((a.resolved / a.interactions) * 100).toFixed(1);
                  return (
                    <tr key={i} className="border-b border-border/20 hover:bg-primary/5 transition-colors">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Avatar className="h-7 w-7 border border-primary/30">
                            <AvatarFallback className="bg-primary/10 text-primary text-[9px]">
                              {a.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-foreground">{a.name}</span>
                        </div>
                      </td>
                      <td className="p-3 font-mono">{a.interactions.toLocaleString()}</td>
                      <td className="p-3 font-mono text-green-500">{a.resolved.toLocaleString()}</td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Progress value={parseFloat(resolveRate)} className="w-12 h-1.5" />
                          <span className="font-mono">{resolveRate}%</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <Badge className="bg-green-500/10 text-green-500 text-[10px] font-mono">
                          {a.avgFrt} د
                        </Badge>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-1">
                          <Star className="w-3 h-3 text-primary fill-primary" />
                          <span className="font-mono">{a.satisfaction}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
