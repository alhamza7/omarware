import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
} from "recharts";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../ui/select";
import {
  MapPin, Users, DollarSign, Ticket, Star, Clock, TrendingUp, Building2,
} from "lucide-react";
import { branchStats } from "./analytics-data";

export function BranchesTab() {
  const [selectedBranch, setSelectedBranch] = useState<string>("all");

  const filteredBranches = selectedBranch === "all"
    ? branchStats
    : branchStats.filter(b => b.id === selectedBranch);

  const totalRevenue = branchStats.reduce((s, b) => s + b.revenue, 0);
  const totalCustomers = branchStats.reduce((s, b) => s + b.customerCount, 0);

  // Bar chart data
  const barData = branchStats.map(b => ({
    name: b.name.replace("فرع ", ""),
    الإيرادات: Math.round(b.revenue / 1000),
    العملاء: b.customerCount,
  }));

  // Radar comparison
  const radarData = [
    { metric: "العملاء", ...Object.fromEntries(branchStats.map(b => [b.name.replace("فرع ", ""), (b.customerCount / totalCustomers) * 100])) },
    { metric: "الإيرادات", ...Object.fromEntries(branchStats.map(b => [b.name.replace("فرع ", ""), (b.revenue / totalRevenue) * 100])) },
    { metric: "الرضا", ...Object.fromEntries(branchStats.map(b => [b.name.replace("فرع ", ""), b.satisfaction * 20])) },
    { metric: "سرعة الاستجابة", ...Object.fromEntries(branchStats.map(b => [b.name.replace("فرع ", ""), Math.max(0, 100 - b.avgFrt * 15)])) },
    { metric: "سرعة الحل", ...Object.fromEntries(branchStats.map(b => [b.name.replace("فرع ", ""), Math.max(0, 100 - b.avgTtr * 10)])) },
  ];

  const radarColors = ["var(--primary)", "#3B82F6", "#22C55E", "#8B5CF6", "#EC4899"];

  return (
    <div className="space-y-6">
      {/* Branch Selector */}
      <div className="flex items-center gap-3">
        <Building2 className="w-4 h-4 text-primary" />
        <span className="text-xs text-muted-foreground">الفرع:</span>
        <Select value={selectedBranch} onValueChange={setSelectedBranch}>
          <SelectTrigger className="w-[200px] h-9 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">جميع الفروع</SelectItem>
            {branchStats.map(b => (
              <SelectItem key={b.id} value={b.id}>{b.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <DollarSign className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">إجمالي الإيرادات</p>
                <p className="text-lg font-mono text-foreground">
                  {(filteredBranches.reduce((s, b) => s + b.revenue, 0) / 1000000).toFixed(1)}M
                </p>
                <p className="text-[9px] text-muted-foreground">ريال سعودي</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-blue-500/10 text-blue-500">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">إجمالي العملاء</p>
                <p className="text-lg font-mono text-foreground">
                  {filteredBranches.reduce((s, b) => s + b.customerCount, 0).toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-green-500/10 text-green-500">
                <Star className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">متوسط الرضا</p>
                <p className="text-lg font-mono text-foreground">
                  {(filteredBranches.reduce((s, b) => s + b.satisfaction, 0) / filteredBranches.length).toFixed(2)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-purple-500/10 text-purple-500">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">متوسط FRT</p>
                <p className="text-lg font-mono text-foreground">
                  {(filteredBranches.reduce((s, b) => s + b.avgFrt, 0) / filteredBranches.length).toFixed(1)} د
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue & Customers Bar Chart */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">الإيرادات والعملاء لكل فرع</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="name" tick={{ fontSize: 8 }} stroke="var(--muted-foreground)" />
                  <YAxis yAxisId="rev" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                  <YAxis yAxisId="cust" orientation="left" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                  <ReTooltip
                    contentStyle={{
                      backgroundColor: "var(--card)", border: "1px solid var(--border)",
                      borderRadius: 12, fontSize: 11, direction: "rtl",
                    }}
                  />
                  <Bar yAxisId="rev" dataKey="الإيرادات" name="الإيرادات (ألف ر.س)" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                  <Bar yAxisId="cust" dataKey="العملاء" name="العملاء" fill="var(--chart-3)" radius={[4, 4, 0, 0]} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Branch Comparison Radar */}
        {selectedBranch === "all" && (
          <Card className="bg-card/30 backdrop-blur-md border-border/40">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">مقارنة أداء الفروع</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="var(--border)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 9 }} stroke="var(--muted-foreground)" />
                    <PolarRadiusAxis tick={false} domain={[0, 100]} />
                    {branchStats.map((b, i) => (
                      <Radar
                        key={b.id}
                        name={b.name.replace("فرع ", "")}
                        dataKey={b.name.replace("فرع ", "")}
                        stroke={radarColors[i]}
                        fill={radarColors[i]}
                        fillOpacity={0.1}
                        strokeWidth={2}
                      />
                    ))}
                    <Legend wrapperStyle={{ fontSize: 9 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Branch Detail Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredBranches.map(b => (
          <Card key={b.id} className="bg-card/30 backdrop-blur-md border-border/40 hover:border-primary/30 transition-colors">
            <CardContent className="p-4 space-y-3">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-foreground">{b.name}</p>
                  <div className="flex items-center gap-1 text-[10px] text-muted-foreground mt-0.5">
                    <MapPin className="w-3 h-3" />
                    <span>{b.city}</span>
                    <span className="text-muted-foreground/40 mx-1">|</span>
                    <span>{b.employeeCount} موظف</span>
                  </div>
                </div>
                <Badge className="bg-primary/10 text-primary text-[9px]">
                  {b.id}
                </Badge>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 rounded-lg bg-muted/20 border border-border/20">
                  <p className="text-[9px] text-muted-foreground">الإيرادات</p>
                  <p className="font-mono text-sm text-primary">{(b.revenue / 1000000).toFixed(1)}M ر.س</p>
                </div>
                <div className="p-2 rounded-lg bg-muted/20 border border-border/20">
                  <p className="text-[9px] text-muted-foreground">العملاء</p>
                  <p className="font-mono text-sm text-foreground">{b.customerCount.toLocaleString()}</p>
                </div>
                <div className="p-2 rounded-lg bg-muted/20 border border-border/20">
                  <p className="text-[9px] text-muted-foreground">FRT</p>
                  <p className="font-mono text-sm text-foreground">{b.avgFrt} دقيقة</p>
                </div>
                <div className="p-2 rounded-lg bg-muted/20 border border-border/20">
                  <p className="text-[9px] text-muted-foreground">TTR</p>
                  <p className="font-mono text-sm text-foreground">{b.avgTtr} ساعة</p>
                </div>
              </div>

              {/* Tickets */}
              <div>
                <p className="text-[9px] text-muted-foreground mb-1.5">التذاكر</p>
                <div className="flex gap-2 text-[10px]">
                  <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 font-mono">مفتوحة: {b.ticketsOpen}</span>
                  <span className="px-1.5 py-0.5 rounded bg-green-500/10 text-green-500 font-mono">مغلقة: {b.ticketsClosed}</span>
                  <span className="px-1.5 py-0.5 rounded bg-destructive/10 text-destructive font-mono">متأخرة: {b.ticketsStale}</span>
                </div>
              </div>

              {/* Satisfaction */}
              <div>
                <div className="flex items-center justify-between text-[10px] mb-1">
                  <span className="text-muted-foreground">رضا العملاء</span>
                  <div className="flex items-center gap-1">
                    <Star className="w-3 h-3 text-primary fill-primary" />
                    <span className="font-mono text-foreground">{b.satisfaction}</span>
                  </div>
                </div>
                <Progress value={b.satisfaction * 20} className="h-1.5" />
              </div>

              {/* Top Agent */}
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground">أفضل موظف</span>
                <span className="text-primary">{b.topAgent}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
