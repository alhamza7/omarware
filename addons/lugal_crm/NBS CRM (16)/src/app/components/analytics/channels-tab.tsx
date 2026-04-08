import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../ui/select";
import {
  MessageCircle, Phone, TrendingUp, Users,
} from "lucide-react";
import type { TimePeriod } from "./analytics-data";
import { channelStats, channelTimeSeries } from "./analytics-data";
import { RadialLeadsChart } from "./radial-leads-chart";
import { channelIcons } from "./channel-icons";
import { ThreeAreaChart3D } from "./three-area-chart-3d";
import { InteractiveBarChart } from "./interactive-bar-chart";

const periodLabels: Record<TimePeriod, string> = {
  day: "اليوم", week: "الأسبوع", month: "الشهر", year: "السنة", overall: "الكل",
};

export function ChannelsTab() {
  const [period, setPeriod] = useState<TimePeriod>("month");
  const [chartPeriod, setChartPeriod] = useState<"day" | "month" | "year">("month");
  const [selectedChannels, setSelectedChannels] = useState<string[]>(
    channelStats.map(c => c.channel)
  );

  const toggleChannel = (ch: string) => {
    setSelectedChannels(prev =>
      prev.includes(ch) ? prev.filter(c => c !== ch) : [...prev, ch]
    );
  };

  const timeData = channelTimeSeries[period];

  // Map chart period selector to TimePeriod for 3D chart data
  const chartTimePeriodMap: Record<"day" | "month" | "year", TimePeriod> = {
    day: "day",
    month: "month",
    year: "year",
  };
  const chart3DTimeData = channelTimeSeries[chartTimePeriodMap[chartPeriod]];

  // Prepare 3D chart data
  const chart3DChannels = channelStats
    .filter(c => selectedChannels.includes(c.channel))
    .map(c => ({
      channel: c.channel,
      channelAr: c.channelAr,
      color: c.color,
      values: chart3DTimeData.map((d: any) => d[c.channel] as number),
    }));
  const chart3DLabels = chart3DTimeData.map((d: any) => d.period as string);
  const isDarkTheme = typeof document !== "undefined" && !document.body.classList.contains("light-turquoise");

  const totalMessages = channelStats.reduce((s, c) => s + c.messages, 0);
  const totalCalls = channelStats.reduce((s, c) => s + c.calls, 0);
  const totalLeads = channelStats.reduce((s, c) => s + c.leads, 0);

  // Leads data for radial chart
  const leadsData = channelStats.map(c => ({
    channel: c.channel,
    channelAr: c.channelAr,
    leads: c.leads,
    color: c.color,
  }));

  return (
    <div className="space-y-6">
      {/* Period Selector + Channel Filter */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">الفترة:</span>
          <Select value={period} onValueChange={(v) => setPeriod(v as TimePeriod)}>
            <SelectTrigger className="w-[140px] h-9 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(periodLabels).map(([k, v]) => (
                <SelectItem key={k} value={k}>{v}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {channelStats.map(c => (
            <button
              key={c.channel}
              onClick={() => toggleChannel(c.channel)}
              className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] border transition-all ${
                selectedChannels.includes(c.channel)
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border/40 bg-muted/30 text-muted-foreground opacity-50"
              }`}
            >
              {channelIcons[c.channel]}
              <span>{c.channelAr}</span>
            </button>
          ))}
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-green-500/10 text-green-500">
                <MessageCircle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">إجمالي الرسائل</p>
                <p className="text-xl font-mono text-foreground">{totalMessages.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-blue-500/10 text-blue-500">
                <Phone className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">إجمالي المكالمات</p>
                <p className="text-xl font-mono text-foreground">{totalCalls.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-purple-500/10 text-purple-500">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">إجمالي العملاء المحتملين</p>
                <p className="text-xl font-mono text-foreground">{totalLeads.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <TrendingUp className="w-5 h-5" />
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">متوسط اتحويل</p>
                <p className="text-xl font-mono text-foreground">
                  {(channelStats.reduce((s, c) => s + c.conversionRate, 0) / channelStats.length).toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Time Series Area Chart */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">حجم التفاعلات حسب القناة - {periodLabels[period]}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[380px]">
            <ThreeAreaChart3D
              channels={chart3DChannels}
              labels={chart3DLabels}
              isDark={isDarkTheme}
              activePeriod={chartPeriod}
              onPeriodChange={setChartPeriod}
            />
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Channel Volume Bar Chart */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">حجم الرسائل والمكالمات لكل قناة</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[380px]">
              <InteractiveBarChart
                data={channelStats}
                isDark={isDarkTheme}
              />
            </div>
          </CardContent>
        </Card>

        {/* Radial Leads Chart */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">توزيع العملاء المحتملين حسب القناة</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[400px]">
              <RadialLeadsChart
                data={leadsData}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Channel Table */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">تفاصيل أداء القنوات</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/40 bg-muted/20">
                  <th className="text-start p-3">القناة</th>
                  <th className="text-start p-3">الرسائل</th>
                  <th className="text-start p-3">المكالات</th>
                  <th className="text-start p-3">المحادثات</th>
                  <th className="text-start p-3">التذاكر</th>
                  <th className="text-start p-3">العملاء المحتملين</th>
                  <th className="text-start p-3">نسبة التحويل</th>
                </tr>
              </thead>
              <tbody>
                {channelStats.map(c => (
                  <tr key={c.channel} className="border-b border-border/20 hover:bg-primary/5 transition-colors">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="p-1 rounded" style={{ backgroundColor: `${c.color}15`, color: c.color }}>
                          {channelIcons[c.channel]}
                        </div>
                        <span className="text-foreground">{c.channelAr}</span>
                      </div>
                    </td>
                    <td className="p-3 font-mono">{c.messages.toLocaleString()}</td>
                    <td className="p-3 font-mono">{c.calls.toLocaleString()}</td>
                    <td className="p-3 font-mono">{c.chats.toLocaleString()}</td>
                    <td className="p-3 font-mono">{c.tickets.toLocaleString()}</td>
                    <td className="p-3 font-mono">{c.leads.toLocaleString()}</td>
                    <td className="p-3">
                      <Badge className={`text-[10px] ${c.conversionRate > 30 ? 'bg-green-500/10 text-green-500' : c.conversionRate > 20 ? 'bg-primary/10 text-primary' : 'bg-muted/30 text-muted-foreground'}`}>
                        {c.conversionRate}%
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}