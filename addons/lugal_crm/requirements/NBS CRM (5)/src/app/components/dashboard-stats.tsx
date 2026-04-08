import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { TrendingUp, Users, ShoppingCart, Package } from "lucide-react";
import { motion } from "motion/react";

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  icon: React.ReactNode;
  trend: "up" | "down";
  index: number;
}

function StatCard({ title, value, change, icon, trend, index }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      whileHover={{ y: -5 }}
    >
      <Card className="relative overflow-hidden group hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 hover:border-primary/40">
        {/* Background decoration */}
        <motion.div
          className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-2xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 0.8, 0.5],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
          }}
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
            <div className="flex items-center gap-1">
              <motion.div
                animate={{ y: trend === "up" ? [-2, 2, -2] : [2, -2, 2] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              >
                <TrendingUp className={`w-4 h-4 ${trend === "up" ? "text-green-500" : "text-red-500 rotate-180"}`} />
              </motion.div>
              <span className={`text-xs ${trend === "up" ? "text-green-500" : "text-red-500"}`}>
                {change}
              </span>
              <span className="text-xs text-muted-foreground">مقار��ة بالشهر الماضي</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function DashboardStats() {
  const stats = [
    {
      title: "إجمالي المبيعات",
      value: "245,890 ريال",
      change: "+12.5%",
      icon: <ShoppingCart className="w-5 h-5 text-primary" />,
      trend: "up" as const,
    },
    {
      title: "عدد العملاء",
      value: "1,234",
      change: "+8.2%",
      icon: <Users className="w-5 h-5 text-primary" />,
      trend: "up" as const,
    },
    {
      title: "المنتجات المباعة",
      value: "856",
      change: "+15.3%",
      icon: <Package className="w-5 h-5 text-primary" />,
      trend: "up" as const,
    },
    {
      title: "متوسط قيمة الطلب",
      value: "287 ريال",
      change: "+4.1%",
      icon: <TrendingUp className="w-5 h-5 text-primary" />,
      trend: "up" as const,
    },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} index={index} />
      ))}
    </div>
  );
}