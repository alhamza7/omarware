import { motion } from "motion/react";
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  PhoneMissed,
  Clock,
  Star,
  TrendingUp,
  Users,
  CheckCircle2,
  BarChart3,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";

// ── Chart Data ──────────────────────────────────────

const hourlyData = [
  { hour: "8", calls: 5 },
  { hour: "9", calls: 12 },
  { hour: "10", calls: 18 },
  { hour: "11", calls: 22 },
  { hour: "12", calls: 15 },
  { hour: "13", calls: 8 },
  { hour: "14", calls: 14 },
  { hour: "15", calls: 20 },
  { hour: "16", calls: 17 },
  { hour: "17", calls: 11 },
  { hour: "18", calls: 6 },
  { hour: "19", calls: 9 },
  { hour: "20", calls: 13 },
];

const weeklyData = [
  { day: "السبت", inbound: 45, outbound: 20 },
  { day: "الأحد", inbound: 52, outbound: 25 },
  { day: "الاثنين", inbound: 48, outbound: 22 },
  { day: "الثلاثاء", inbound: 55, outbound: 28 },
  { day: "الأربعاء", inbound: 60, outbound: 30 },
  { day: "الخميس", inbound: 42, outbound: 18 },
  { day: "الجمعة", inbound: 15, outbound: 5 },
];

const satisfactionData = [
  { day: "السبت", score: 4.5 },
  { day: "الأحد", score: 4.7 },
  { day: "الاثنين", score: 4.3 },
  { day: "الثلاثاء", score: 4.8 },
  { day: "الأربعاء", score: 4.6 },
  { day: "الخميس", score: 4.9 },
  { day: "الجمعة", score: 4.7 },
];

const categoryData = [
  { name: "استفسارات عامة", value: 35 },
  { name: "طلبات", value: 25 },
  { name: "شكاوى", value: 15 },
  { name: "استبدال", value: 12 },
  { name: "VIP", value: 8 },
  { name: "أخرى", value: 5 },
];

const COLORS = [
  "var(--primary)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--muted-foreground)",
];

export function CCAnalytics() {
  return (
    <div className="space-y-6">
      {/* KPI Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[
          { label: "مكالمات اليوم", value: "80", icon: Phone, color: "text-blue-500", bg: "bg-blue-500/10", change: "+12%" },
          { label: "واردة", value: "58", icon: PhoneIncoming, color: "text-emerald-500", bg: "bg-emerald-500/10", change: "+8%" },
          { label: "صادرة", value: "18", icon: PhoneOutgoing, color: "text-cyan-500", bg: "bg-cyan-500/10", change: "+15%" },
          { label: "فائتة", value: "4", icon: PhoneMissed, color: "text-red-500", bg: "bg-red-500/10", change: "-25%" },
          { label: "متوسط الانتظار", value: "1:23", icon: Clock, color: "text-primary", bg: "bg-primary/10", change: "-10%" },
          { label: "حل أول مكالمة", value: "78%", icon: CheckCircle2, color: "text-emerald-500", bg: "bg-emerald-500/10", change: "+5%" },
        ].map((stat, i) => {
          const Icon = stat.icon;
          const isPositive = stat.change.startsWith("+");
          const isNeutral = stat.change.startsWith("-") && stat.label !== "فائتة";
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className="border-border/50">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-8 h-8 rounded-lg ${stat.bg} flex items-center justify-center shrink-0`}>
                      <Icon className={`w-4 h-4 ${stat.color}`} />
                    </div>
                    <Badge className={`text-[10px] border-transparent ${
                      (isPositive && stat.label !== "فائتة") || (!isPositive && stat.label === "فائتة")
                        ? "bg-emerald-500/10 text-emerald-500"
                        : "bg-red-500/10 text-red-500"
                    }`}>
                      {stat.change}
                    </Badge>
                  </div>
                  <p className="text-xl text-foreground">{stat.value}</p>
                  <p className="text-[10px] text-muted-foreground">{stat.label}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Call Volume */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                حجم المكالمات بالساعة
              </CardTitle>
              <CardDescription>ساعات الذروة اليوم</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hourlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="hour" stroke="var(--muted-foreground)" fontSize={11} />
                    <YAxis stroke="var(--muted-foreground)" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        color: "var(--foreground)",
                        direction: "rtl",
                      }}
                      labelFormatter={(v) => `الساعة ${v}`}
                      formatter={(v: number) => [`${v} مكالمة`, "المكالمات"]}
                    />
                    <Bar dataKey="calls" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Weekly Calls */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                المكالمات الأسبوعية
              </CardTitle>
              <CardDescription>واردة مقابل صادرة</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="day" stroke="var(--muted-foreground)" fontSize={10} />
                    <YAxis stroke="var(--muted-foreground)" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        color: "var(--foreground)",
                        direction: "rtl",
                      }}
                      formatter={(v: number, name: string) => [
                        `${v}`,
                        name === "inbound" ? "واردة" : "صادرة",
                      ]}
                    />
                    <Bar dataKey="inbound" fill="var(--primary)" radius={[4, 4, 0, 0]} name="inbound" />
                    <Bar dataKey="outbound" fill="var(--chart-2)" radius={[4, 4, 0, 0]} name="outbound" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Satisfaction Trend */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Star className="w-4 h-4 text-primary" />
                اتجاه رضا العملاء
              </CardTitle>
              <CardDescription>متوسط التقييم اليومي (من 5)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={satisfactionData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="day" stroke="var(--muted-foreground)" fontSize={10} />
                    <YAxis domain={[3.5, 5]} stroke="var(--muted-foreground)" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        color: "var(--foreground)",
                        direction: "rtl",
                      }}
                      formatter={(v: number) => [`${v}/5`, "التقييم"]}
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="var(--primary)"
                      strokeWidth={2.5}
                      dot={{ fill: "var(--primary)", strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, fill: "var(--primary)" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Call Categories */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="w-4 h-4 text-primary" />
                تصنيف المكالمات
              </CardTitle>
              <CardDescription>توزيع حسب الموضوع</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className="h-[220px] w-[220px] shrink-0" dir="ltr">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryData}
                        innerRadius={55}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {categoryData.map((_, idx) => (
                          <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "var(--card)",
                          border: "1px solid var(--border)",
                          borderRadius: "8px",
                          color: "var(--foreground)",
                          direction: "rtl",
                        }}
                        formatter={(v: number) => [`${v}%`, ""]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex-1 space-y-2">
                  {categoryData.map((cat, idx) => (
                    <div key={cat.name} className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-sm shrink-0"
                        style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                      />
                      <span className="text-xs text-muted-foreground flex-1">{cat.name}</span>
                      <span className="text-xs text-foreground">{cat.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
