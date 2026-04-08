import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  Ticket, CheckCircle2, AlertTriangle, Clock, TrendingUp, TrendingDown, ArrowUpDown,
} from "lucide-react";
import { ticketStats, ticketsByChannel } from "./analytics-data";

export function TicketsTab() {
  const totalTickets = ticketStats.reduce((s, t) => s + t.count, 0);

  // Pie chart data
  const pieData = ticketStats.map(t => ({
    name: t.statusAr,
    value: t.count,
    color: t.color,
  }));

  // Stacked bar data for channels
  const channelBarData = ticketsByChannel.map(c => ({
    name: c.channelAr,
    مفتوحة: c.open,
    مغلقة: c.closed,
    متأخرة: c.stale,
  }));

  return (
    <div className="space-y-6">
      {/* Ticket Status KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {ticketStats.map(t => {
          const icons: Record<string, React.ReactNode> = {
            open: <Ticket className="w-5 h-5" />,
            closed: <CheckCircle2 className="w-5 h-5" />,
            stale: <AlertTriangle className="w-5 h-5" />,
            "in-progress": <Clock className="w-5 h-5" />,
            escalated: <ArrowUpDown className="w-5 h-5" />,
          };
          return (
            <Card key={t.status} className="bg-card/30 backdrop-blur-md border-border/40">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2 rounded-xl" style={{ backgroundColor: `${t.color}15`, color: t.color }}>
                    {icons[t.status]}
                  </div>
                  <Badge className={`text-[9px] font-mono ${t.trend > 0 ? 'bg-green-500/10 text-green-500' : 'bg-destructive/10 text-destructive'}`}>
                    {t.trend > 0 ? <TrendingUp className="w-2.5 h-2.5 me-0.5" /> : <TrendingDown className="w-2.5 h-2.5 me-0.5" />}
                    {Math.abs(t.trend)}%
                  </Badge>
                </div>
                <p className="text-2xl font-mono text-foreground">{t.count.toLocaleString()}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{t.statusAr}</p>
                <div className="mt-2 h-1 rounded-full bg-muted/30 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${(t.count / totalTickets) * 100}%`, backgroundColor: t.color }}
                  />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ticket Distribution Pie */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">توزيع التذاكر حسب الحالة</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={105}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} opacity={0.85} />
                    ))}
                  </Pie>
                  <ReTooltip
                    contentStyle={{
                      backgroundColor: "var(--card)", border: "1px solid var(--border)",
                      borderRadius: 12, fontSize: 11, direction: "rtl",
                    }}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: 11 }}
                    formatter={(value) => <span style={{ color: "var(--foreground)" }}>{value}</span>}
                  />
                  {/* Center label */}
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="text-center -mt-4">
              <p className="text-2xl font-mono text-foreground">{totalTickets.toLocaleString()}</p>
              <p className="text-[10px] text-muted-foreground">إجمالي التذاكر</p>
            </div>
          </CardContent>
        </Card>

        {/* Tickets by Channel Stacked Bar */}
        <Card className="bg-card/30 backdrop-blur-md border-border/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">التذاكر حسب القناة والحالة</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[340px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={channelBarData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis type="number" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" width={60} />
                  <ReTooltip
                    contentStyle={{
                      backgroundColor: "var(--card)", border: "1px solid var(--border)",
                      borderRadius: 12, fontSize: 11, direction: "rtl",
                    }}
                  />
                  <Bar dataKey="مغلقة" stackId="a" fill="#22C55E" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="مفتوحة" stackId="a" fill="#3B82F6" />
                  <Bar dataKey="متأخرة" stackId="a" fill="#EF4444" radius={[0, 4, 4, 0]} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Channel Ticket Table */}
      <Card className="bg-card/30 backdrop-blur-md border-border/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">تفاصيل التذاكر لكل قناة</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/40 bg-muted/20">
                  <th className="text-start p-3">القناة</th>
                  <th className="text-start p-3">مفتوحة</th>
                  <th className="text-start p-3">مغلقة</th>
                  <th className="text-start p-3">متأخرة / راكدة</th>
                  <th className="text-start p-3">الإجمالي</th>
                  <th className="text-start p-3">نسبة الإغلاق</th>
                </tr>
              </thead>
              <tbody>
                {ticketsByChannel.map(c => {
                  const total = c.open + c.closed + c.stale;
                  const closeRate = ((c.closed / total) * 100).toFixed(1);
                  return (
                    <tr key={c.channel} className="border-b border-border/20 hover:bg-primary/5 transition-colors">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: c.color }} />
                          <span className="text-foreground">{c.channelAr}</span>
                        </div>
                      </td>
                      <td className="p-3 font-mono text-blue-500">{c.open}</td>
                      <td className="p-3 font-mono text-green-500">{c.closed}</td>
                      <td className="p-3 font-mono text-destructive">{c.stale}</td>
                      <td className="p-3 font-mono">{total}</td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-muted/30 overflow-hidden">
                            <div className="h-full rounded-full bg-green-500 transition-all" style={{ width: `${closeRate}%` }} />
                          </div>
                          <span className="font-mono text-green-500">{closeRate}%</span>
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