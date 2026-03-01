import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { TrendingUp, Users, ShoppingCart, Package, Phone, Ticket, MessageSquare } from "lucide-react";
import { motion } from "motion/react";
import type { DashboardStats as ApiStats } from "../../features/dashboard/types";

interface StatCardProps {
  title: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  index: number;
}

/** Animated KPI card — used in the 4-card top row of the dashboard */
function StatCard({ title, value, sub, icon, trend = "up", index }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      whileHover={{ y: -5 }}
    >
      <Card className="relative overflow-hidden group hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 hover:border-primary/40">
        <motion.div
          className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-2xl"
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />
        <CardHeader className="flex flex-row items-center justify-between pb-2 relative">
          <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
          <motion.div
            className="p-2.5 rounded-lg bg-primary/10 border border-primary/20"
            whileHover={{ scale: 1.1, rotate: 5 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            {icon}
          </motion.div>
        </CardHeader>
        <CardContent className="relative">
          <div className="space-y-1">
            <motion.p
              className="text-3xl font-bold text-gradient-gold drop-shadow-sm"
              initial={{ scale: 0.5 }}
              animate={{ scale: 1 }}
              transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
            >
              {value}
            </motion.p>
            {sub && (
              <div className="flex items-center gap-1">
                <motion.div
                  animate={{ y: trend === "up" ? [-2, 2, -2] : [2, -2, 2] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                  <TrendingUp
                    className={`w-4 h-4 ${trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500 rotate-180" : "text-muted-foreground"}`}
                  />
                </motion.div>
                <span className={`text-xs ${trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-muted-foreground"}`}>
                  {sub}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

interface DashboardStatsProps {
  /** Real API stats. When undefined the component shows loading skeletons. */
  stats?: ApiStats | null;
}

/**
 * Top-level KPI row on the dashboard.
 * Reads from real API stats when provided; falls back to skeleton placeholders.
 */
export function DashboardStats({ stats }: DashboardStatsProps) {
  const cards: Omit<StatCardProps, "index">[] = stats
    ? [
        {
          title: "إجمالي العملاء",
          value:  stats.customers.total.toLocaleString("ar-SA"),
          sub:   `${stats.customers.new_today} جديد اليوم`,
          icon:  <Users className="w-5 h-5 text-primary" />,
          trend: "up",
        },
        {
          title: "التذاكر المفتوحة",
          value:  stats.tickets.open.toLocaleString("ar-SA"),
          sub:   `${stats.tickets.high_priority} ذات أولوية عالية`,
          icon:  <Ticket className="w-5 h-5 text-primary" />,
          trend: stats.tickets.high_priority > 0 ? "down" : "up",
        },
        {
          title: "إجمالي المكالمات",
          value:  stats.calls.total.toLocaleString("ar-SA"),
          sub:   `${stats.calls.missed} مكالمة فائتة`,
          icon:  <Phone className="w-5 h-5 text-primary" />,
          trend: stats.calls.missed > 0 ? "down" : "up",
        },
        {
          title: "الرسائل الواردة",
          value:  stats.messages.inbound.toLocaleString("ar-SA"),
          sub:   `${stats.messages.pending_reply} تنتظر الرد`,
          icon:  <MessageSquare className="w-5 h-5 text-primary" />,
          trend: stats.messages.pending_reply > 0 ? "down" : "up",
        },
      ]
    : /* Skeleton placeholders while loading */
      [
        { title: "إجمالي العملاء",    value: "—", icon: <Users className="w-5 h-5 text-primary/40" /> },
        { title: "التذاكر المفتوحة", value: "—", icon: <ShoppingCart className="w-5 h-5 text-primary/40" /> },
        { title: "إجمالي المكالمات", value: "—", icon: <Package className="w-5 h-5 text-primary/40" /> },
        { title: "الرسائل الواردة",   value: "—", icon: <TrendingUp className="w-5 h-5 text-primary/40" /> },
      ];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => (
        <StatCard key={index} {...card} index={index} />
      ))}
    </div>
  );
}
