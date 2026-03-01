import { useState, useEffect, useRef } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Sector,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../ui/card";
import { Button } from "../ui/button";
import {
  TrendingUp,
  Activity,
  ArrowUpRight,
  Users,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

import { Tabs, TabsList, TabsTrigger } from "../ui/tabs";

const initialSalesData = [
  { name: "يناير", sales: 4000, target: 2400 },
  { name: "فبراير", sales: 3000, target: 1398 },
  { name: "مارس", sales: 2000, target: 9800 },
  { name: "أبريل", sales: 2780, target: 3908 },
  { name: "مايو", sales: 1890, target: 4800 },
  { name: "يونيو", sales: 2390, target: 3800 },
  { name: "يوليو", sales: 3490, target: 4300 },
];

const dailySalesData = [
  { name: "السبت", sales: 1200, target: 1000 },
  { name: "الأحد", sales: 1500, target: 1200 },
  { name: "الاثنين", sales: 1800, target: 1400 },
  { name: "الثلاثاء", sales: 2000, target: 1600 },
  { name: "الأربعاء", sales: 2500, target: 2000 },
  { name: "الخميس", sales: 3000, target: 2400 },
  { name: "الجمعة", sales: 3500, target: 2800 },
];

const yearlySalesData = [
  { name: "2019", sales: 15000, target: 12000 },
  { name: "2020", sales: 18000, target: 15000 },
  { name: "2021", sales: 22000, target: 18000 },
  { name: "2022", sales: 28000, target: 24000 },
  { name: "2023", sales: 35000, target: 30000 },
  { name: "2024", sales: 42000, target: 38000 },
];

const customerSegments = [
  { name: "VIP", value: 400 },
  { name: "جدد", value: 300 },
  { name: "عائدون", value: 300 },
  { name: "خاملون", value: 200 },
];

// Neon Palette
const COLORS = ["#FFD60A", "#06B6D4", "#A855F7", "#10B981"];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-card/95 backdrop-blur-md border border-border p-4 rounded-xl shadow-2xl min-w-[180px]"
      >
        <p className="text-sm font-bold mb-3 text-foreground border-b border-border/50 pb-2">
          {label}
        </p>
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_rgba(212,175,55,0.6)]" />
              <span className="text-xs text-muted-foreground font-medium">
                المبيعات
              </span>
            </div>
            <span className="text-sm font-bold text-primary font-mono tabular-nums">
              SAR {payload[0].value.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-muted-foreground/30" />
              <span className="text-xs text-muted-foreground font-medium">
                الهدف
              </span>
            </div>
            <span className="text-sm font-bold text-muted-foreground font-mono tabular-nums">
              SAR {payload[1].value.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Growth Indicator */}
        <div className="mt-3 pt-2 border-t border-border/50 flex items-center gap-1.5 text-xs text-green-500 font-medium">
          <TrendingUp className="w-3 h-3" />
          <span>+12.5% عن الشهر السابق</span>
        </div>
      </motion.div>
    );
  }
  return null;
};

const GlowingActiveDot = (props: any) => {
  const { cx, cy, stroke } = props;
  return (
    <svg
      x={cx - 10}
      y={cy - 10}
      width={20}
      height={20}
      className="overflow-visible pointer-events-none"
    >
      <defs>
        <radialGradient
          id="glowGradient"
          cx="50%"
          cy="50%"
          r="50%"
        >
          <stop
            offset="0%"
            stopColor={stroke}
            stopOpacity="0.8"
          />
          <stop
            offset="100%"
            stopColor={stroke}
            stopOpacity="0"
          />
        </radialGradient>
      </defs>
      <circle
        cx="10"
        cy="10"
        r="8"
        fill="url(#glowGradient)"
        className="animate-pulse"
        opacity="0.6"
      />
      <circle
        cx="10"
        cy="10"
        r="4"
        fill="#fff"
        stroke={stroke}
        strokeWidth="2"
      />
    </svg>
  );
};

export function SalesChart({
  theme = "dark-gold",
}: {
  theme?: "dark-gold" | "light-turquoise";
}) {
  const [timeRange, setTimeRange] = useState("monthly");
  const [data, setData] = useState(initialSalesData);
  const [isMounted, setIsMounted] = useState(false);
  const chartContainerRef = useRef<HTMLDivElement>(null);

  const isDark = theme === "dark-gold";
  const primaryColor = isDark ? "#EAB308" : "#06b6d4";
  const secondaryColor = isDark ? "#22c55e" : "#10b981";

  useEffect(() => {
    // Delay mounting slightly to ensure layout is complete
    const frame = requestAnimationFrame(() => {
      setIsMounted(true);
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (timeRange === "daily") setData(dailySalesData);
    else if (timeRange === "yearly") setData(yearlySalesData);
    else setData(initialSalesData);
  }, [timeRange]);

  useEffect(() => {
    const interval = setInterval(() => {
      setData((prevData) => {
        return prevData.map((item, index) => {
          if (index === prevData.length - 1) {
            let maxVal = 6000,
              minVal = 3000;
            if (timeRange === "yearly") {
              maxVal = 45000;
              minVal = 35000;
            }
            if (timeRange === "daily") {
              maxVal = 4000;
              minVal = 2500;
            }

            const fluctuation =
              Math.floor(Math.random() * 500) - 200;
            const newSales = Math.max(
              minVal,
              Math.min(maxVal, item.sales + fluctuation),
            );
            return { ...item, sales: newSales };
          }
          return item;
        });
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [timeRange]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="col-span-2 h-full min-w-0"
    >
      <Card
        className={`relative overflow-hidden shadow-2xl h-full flex flex-col group transition-colors duration-500
            ${isDark ? "bg-[#0a0a0a] border-white/5" : "bg-white/80 backdrop-blur-xl border-cyan-100 shadow-cyan-500/5"}
        `}
      >
        {/* Ambient Glows */}
        <div
          className={`absolute top-0 end-0 w-[600px] h-[600px] rounded-full blur-[140px] -me-48 -mt-48 pointer-events-none transition-colors duration-500
            ${isDark ? "bg-yellow-500/5" : "bg-cyan-500/5"}
        `}
        />
        <div
          className={`absolute bottom-0 start-0 w-[400px] h-[400px] rounded-full blur-[120px] -ms-32 -mb-32 pointer-events-none transition-colors duration-500
            ${isDark ? "bg-yellow-600/5" : "bg-blue-500/5"}
        `}
        />

        <CardHeader
          className={`relative z-10 flex flex-col md:flex-row items-center justify-between pb-6 border-b mx-6 mt-2 px-0 transition-colors duration-500
            ${isDark ? "border-white/5" : "border-cyan-100/50"}
        `}
        >
          {/* Title Section (Right in RTL) */}
          <div className="flex flex-col items-start gap-1 text-start w-full md:w-auto">
            <CardTitle
              className={`flex items-center gap-3 text-2xl font-bold tracking-tight transition-colors duration-500
                    ${isDark ? "text-white" : "text-slate-800"}
                `}
            >
              أداء المبيعات
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isDark ? "bg-green-500" : "bg-cyan-500"}`}
                ></span>
                <span
                  className={`relative inline-flex rounded-full h-2.5 w-2.5 shadow-[0_0_8px_rgba(34,197,94,0.6)] ${isDark ? "bg-green-500" : "bg-cyan-500"}`}
                ></span>
              </span>
            </CardTitle>
            <CardDescription
              className={`font-medium transition-colors duration-500
                    ${isDark ? "text-zinc-400" : "text-slate-500"}
                `}
            >
              متابعة حية للأداء مقارنة بالأهداف المحددة
            </CardDescription>
          </div>

          {/* Controls Section (Left in RTL) */}
          <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-start mt-4 md:mt-0">
            {/* Stats Box */}
            <div
              className={`flex items-center gap-3 backdrop-blur-md px-4 py-2 rounded-xl border shadow-inner transition-colors duration-500
                    ${isDark ? "bg-white/5 border-white/5" : "bg-white border-cyan-100 shadow-sm"}
                `}
            >
              <div className="flex flex-col items-start">
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider transition-colors duration-500
                          ${isDark ? "text-zinc-500" : "text-slate-400"}
                      `}
                >
                  إجمالي المبيعات
                </span>
                <span
                  className={`text-lg font-bold font-mono tracking-tight drop-shadow-sm transition-colors duration-500
                          ${isDark ? "text-yellow-400" : "text-cyan-600"}
                      `}
                >
                  SAR 19,450
                </span>
              </div>
              <div
                className={`w-px h-8 mx-1 ${isDark ? "bg-white/10" : "bg-slate-200"}`}
              />
              <div
                className={`p-2 rounded-lg border transition-colors duration-500
                       ${isDark ? "bg-yellow-500/10 border-yellow-500/20" : "bg-cyan-500/10 border-cyan-200"}
                   `}
              >
                <Activity
                  className={`w-5 h-5 ${isDark ? "text-yellow-500" : "text-cyan-500"}`}
                />
              </div>
            </div>

            {/* Tabs */}
            <Tabs
              defaultValue="monthly"
              value={timeRange}
              onValueChange={setTimeRange}
            >
              <TabsList
                className={`p-1 h-10 rounded-xl border transition-colors duration-500
                        ${isDark ? "bg-black/40 border-white/10" : "bg-slate-100 border-slate-200"}
                    `}
              >
                <TabsTrigger
                  className={`rounded-lg text-xs font-medium transition-all px-4
                            ${
                              isDark
                                ? "data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-500 hover:text-zinc-300"
                                : "data-[state=active]:bg-white data-[state=active]:text-cyan-600 data-[state=active]:shadow-sm text-slate-500 hover:text-slate-700"
                            }
                        `}
                  value="daily"
                >
                  يومي
                </TabsTrigger>
                <TabsTrigger
                  className={`rounded-lg text-xs font-medium transition-all px-4
                             ${
                               isDark
                                 ? "data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-500 hover:text-zinc-300"
                                 : "data-[state=active]:bg-white data-[state=active]:text-cyan-600 data-[state=active]:shadow-sm text-slate-500 hover:text-slate-700"
                             }
                        `}
                  value="monthly"
                >
                  شهري
                </TabsTrigger>
                <TabsTrigger
                  className={`rounded-lg text-xs font-medium transition-all px-4
                             ${
                               isDark
                                 ? "data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-500 hover:text-zinc-300"
                                 : "data-[state=active]:bg-white data-[state=active]:text-cyan-600 data-[state=active]:shadow-sm text-slate-500 hover:text-slate-700"
                             }
                        `}
                  value="yearly"
                >
                  سنوي
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>

        <CardContent className="relative z-10 pt-8 flex-1 px-2 sm:px-6">
          <div
            ref={chartContainerRef}
            className="h-[350px] w-full"
            style={{ minHeight: 350, minWidth: 200 }}
          >
            {isMounted && (
              <ResponsiveContainer
                width="100%"
                height="100%"
                debounce={50}
                minWidth={0}
              >
                <AreaChart
                  data={data}
                  margin={{
                    top: 10,
                    right: 10,
                    left: 0,
                    bottom: 10,
                  }}
                >
                  <defs>
                    <linearGradient
                      id="colorSalesGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor={primaryColor}
                        stopOpacity={0.4}
                      />
                      <stop
                        offset="50%"
                        stopColor={primaryColor}
                        stopOpacity={0.1}
                      />
                      <stop
                        offset="100%"
                        stopColor={primaryColor}
                        stopOpacity={0.0}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    strokeDasharray="4 4"
                    stroke={isDark ? "#27272a" : "#e2e8f0"}
                    vertical={false}
                    opacity={0.5}
                  />

                  <XAxis
                    dataKey="name"
                    stroke={isDark ? "#52525b" : "#94a3b8"}
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    tickMargin={20}
                    fontWeight={500}
                  />

                  <YAxis
                    stroke={isDark ? "#52525b" : "#94a3b8"}
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) =>
                      `${value / 1000}k`
                    }
                    width={40}
                  />

                  <Tooltip
                    content={<CustomTooltip />}
                    cursor={{
                      stroke: primaryColor,
                      strokeWidth: 1,
                      strokeDasharray: "4 4",
                      opacity: 0.5,
                    }}
                  />

                  <Area
                    type="monotone"
                    dataKey="target"
                    stroke={isDark ? "#52525b" : "#cbd5e1"}
                    strokeWidth={2}
                    strokeDasharray="6 6"
                    fill="none"
                    opacity={0.4}
                    isAnimationActive={true}
                  />

                  <Area
                    type="monotone"
                    dataKey="sales"
                    stroke={primaryColor}
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorSalesGradient)"
                    activeDot={
                      <GlowingActiveDot stroke={primaryColor} />
                    }
                    animationDuration={1500}
                    animationEasing="ease-out"
                  ></Area>
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

const renderActiveShape = (props: any) => {
  const RADIAN = Math.PI / 180;
  const {
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    payload,
    percent,
    value,
  } = props;
  const sin = Math.sin(-RADIAN * midAngle);
  const cos = Math.cos(-RADIAN * midAngle);

  const solidColor =
    COLORS[
      customerSegments.findIndex((c) => c.name === payload.name)
    ] || fill;

  // Line calculations
  const sx = cx + (outerRadius + 0) * cos;
  const sy = cy + (outerRadius + 0) * sin;
  const mx = cx + (outerRadius + 30) * cos;
  const my = cy + (outerRadius + 30) * sin;

  // Robust side determination
  // cos >= 0 is Right side, cos < 0 is Left side
  const isRight = cos >= 0;

  // Extend line further to avoid chart overlap
  const ex = mx + (isRight ? 1 : -1) * 30;
  const ey = my;

  const textAnchor = isRight ? "start" : "end";

  // Position text with padding from the line end
  const textX = ex + (isRight ? 1 : -1) * 12;

  // Percentage Position - Inside Slice (Center of the arc section)
  const radiusMid = (innerRadius + outerRadius) / 2;
  const percentX = cx + radiusMid * cos;
  const percentY = cy + radiusMid * sin;

  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 8}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        className="drop-shadow-xl"
        style={{
          filter: `drop-shadow(0px 0px 10px ${solidColor}60)`,
        }}
      />

      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 10}
        outerRadius={outerRadius + 12}
        fill={solidColor}
        opacity={0.3}
      />

      {/* Callout Line */}
      <motion.path
        d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`}
        stroke={solidColor}
        strokeWidth={2}
        fill="none"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      />

      {/* End Dot */}
      <motion.circle
        cx={ex}
        cy={ey}
        r={3}
        fill={solidColor}
        stroke="var(--background)"
        strokeWidth={1}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.2, delay: 0.2 }}
      />

      {/* Percentage INSIDE Slice */}
      <motion.text
        x={percentX}
        y={percentY}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#ffffff"
        className="text-sm font-black drop-shadow-md pointer-events-none"
        style={{
          textShadow: "0 1px 3px rgba(0,0,0,0.5)",
          fontSize: "13px",
        }}
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </motion.text>

      {/* Unified Text Label Group */}
      {/* Using balanced dy values to perfectly center the text block vertically relative to the line */}
      <motion.text
        x={textX}
        y={ey}
        textAnchor={textAnchor}
        initial={{
          opacity: 0,
          x: textX + (isRight ? -10 : 10),
        }}
        animate={{ opacity: 1, x: textX }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="fill-foreground text-sm font-bold"
      >
        {/* Value Label (Top) - Centered visually above the line */}
        <tspan
          x={textX}
          dy="-0.6em"
          fill="var(--muted-foreground)"
          fontSize="12px"
          fontWeight="500"
        >
          {value} عميل
        </tspan>

        {/* Name Label (Bottom) - Centered visually below the line */}
        <tspan
          x={textX}
          dy="1.6em"
          fill="var(--foreground)"
          fontSize="14px"
          fontWeight="bold"
        >
          {payload.name}
        </tspan>
      </motion.text>
    </g>
  );
};

export function CustomerSegmentationChart({
  theme = "dark-gold",
}: {
  theme?: "dark-gold" | "light-turquoise";
}) {
  const [activeIndex, setActiveIndex] = useState<
    number | undefined
  >(undefined);
  const [isMounted, setIsMounted] = useState(false);
  const pieContainerRef = useRef<HTMLDivElement>(null);

  const isDark = theme === "dark-gold";
  const colors = isDark
    ? ["#FFD60A", "#06B6D4", "#A855F7", "#10B981"] // Neon for Dark
    : ["#0891b2", "#3b82f6", "#8b5cf6", "#14b8a6"]; // Cool for Light

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  const onPieLeave = () => {
    setActiveIndex(undefined);
  };

  const totalValue = customerSegments.reduce(
    (sum, item) => sum + item.value,
    0,
  );

  const activeItem =
    activeIndex !== undefined
      ? customerSegments[activeIndex]
      : null;
  const displayValue = activeItem
    ? activeItem.value
    : totalValue;
  const displayName = activeItem
    ? activeItem.name
    : "إجمالي العملاء";
  const displayColor = activeItem
    ? colors[activeIndex! % colors.length]
    : isDark
      ? "#fbbf24"
      : "#0891b2";

  useEffect(() => {
    // Delay mounting slightly to ensure layout is complete
    const frame = requestAnimationFrame(() => {
      setIsMounted(true);
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="h-full min-w-0"
    >
      <Card
        className={`hover:shadow-lg transition-all duration-300 overflow-hidden group h-full flex flex-col relative
            ${isDark ? "bg-[#0a0a0a] border-white/5" : "bg-white/80 backdrop-blur-xl border-cyan-100 shadow-cyan-500/5"}
        `}
      >
        {/* Subtle Ambient Background */}
        <div
          className={`absolute top-0 start-0 w-[400px] h-[400px] rounded-full blur-[120px] -ms-48 -mt-48 pointer-events-none transition-colors duration-500
            ${isDark ? "bg-yellow-500/5" : "bg-cyan-500/5"}
        `}
        />
        <div
          className={`absolute bottom-0 end-0 w-[300px] h-[300px] rounded-full blur-[100px] -me-32 -mb-32 pointer-events-none transition-colors duration-500
            ${isDark ? "bg-cyan-500/5" : "bg-blue-500/5"}
        `}
        />

        <CardHeader
          className={`pb-2 relative z-10 border-b mx-6 mt-2 px-0 transition-colors duration-500
             ${isDark ? "border-white/5" : "border-cyan-100/50"}
        `}
        >
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="icon"
              className={`h-8 w-8 transition-colors
                    ${isDark ? "text-zinc-500 hover:text-white hover:bg-white/5" : "text-slate-400 hover:text-cyan-600 hover:bg-cyan-50"}
                `}
            >
              <ArrowUpRight className="w-4 h-4" />
            </Button>
            <CardTitle
              className={`text-lg flex items-center gap-3 font-bold transition-colors duration-500
                    ${isDark ? "text-white" : "text-slate-800"}
                `}
            >
              تصنيف العملاء
              <div
                className={`p-2 rounded-lg border shadow-sm transition-colors duration-500
                        ${isDark ? "bg-white/5 border-white/5 text-yellow-500" : "bg-cyan-50 border-cyan-100 text-cyan-600"}
                    `}
              >
                <Users className="w-4 h-4" />
              </div>
            </CardTitle>
          </div>
          <CardDescription
            className={`text-start font-medium transition-colors duration-500
                ${isDark ? "text-zinc-400" : "text-slate-500"}
            `}
          >
            تحليل قاعدة العملاء النشطة وتوزيع الفئات
          </CardDescription>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col justify-center relative z-10 pt-6">
          <div
            ref={pieContainerRef}
            className="h-[280px] w-full relative mx-auto"
            style={{ minHeight: 280, minWidth: 200 }}
            onMouseLeave={onPieLeave}
          >
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10 pb-2">
              <AnimatePresence mode="wait">
                <motion.div
                  key={displayName}
                  initial={{ opacity: 0, scale: 0.9, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9, y: -10 }}
                  transition={{ duration: 0.2 }}
                  className="flex flex-col items-center"
                >
                  <span
                    className="text-4xl font-extrabold tracking-tight tabular-nums transition-colors duration-300"
                    style={{
                      color:
                        activeIndex !== undefined
                          ? displayColor
                          : isDark
                            ? "#fbbf24"
                            : "#0891b2",
                      textShadow: isDark
                        ? "0 0 20px rgba(251, 191, 36, 0.2)"
                        : "none",
                    }}
                  >
                    {displayValue.toLocaleString()}
                  </span>
                  <span
                    className={`text-xs uppercase tracking-widest font-bold mt-2 transition-colors duration-500
                                ${isDark ? "text-zinc-500" : "text-slate-400"}
                            `}
                  >
                    {displayName}
                  </span>
                </motion.div>
              </AnimatePresence>
            </div>

            {isMounted && (
              <ResponsiveContainer
                width="100%"
                height="100%"
                debounce={50}
                minWidth={0}
              >
                <PieChart
                  margin={{
                    top: 20,
                    right: 30,
                    left: 30,
                    bottom: 20,
                  }}
                >
                  <defs>
                    {colors.map((color, index) => (
                      <linearGradient
                        key={`pieGradient-${index}`}
                        id={`pieGradient-${index}`}
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor={color}
                          stopOpacity={0.9}
                        />
                        <stop
                          offset="100%"
                          stopColor={color}
                          stopOpacity={0.2}
                        />
                      </linearGradient>
                    ))}
                  </defs>
                  <Pie
                    data={customerSegments}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                    stroke="none"
                    cornerRadius={5}
                    onMouseEnter={onPieEnter}
                    onMouseLeave={onPieLeave}
                    activeIndex={activeIndex}
                    activeShape={renderActiveShape}
                  >
                    {customerSegments.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={`url(#pieGradient-${index})`}
                        stroke={colors[index % colors.length]}
                        strokeWidth={1}
                        strokeOpacity={0.3}
                        className="transition-all duration-300 ease-out cursor-pointer outline-none"
                        style={{
                          filter:
                            activeIndex !== undefined &&
                            activeIndex !== index
                              ? "grayscale(0.8) opacity(0.3)"
                              : isDark
                                ? "drop-shadow(0 0 8px rgba(0,0,0,0.5))"
                                : "drop-shadow(0 4px 6px rgba(0,0,0,0.1))",
                          outline: "none",
                        }}
                      />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="flex flex-wrap justify-center gap-3 -mt-2 px-4 pb-2">
            {customerSegments.map((entry, index) => (
              <motion.div
                key={`legend-${index}`}
                className={`flex items-center gap-2 cursor-pointer transition-all duration-300 px-3 py-1.5 rounded-full border hover:bg-opacity-50
                             ${
                               isDark
                                 ? "border-white/5 hover:bg-white/10"
                                 : "border-slate-200 hover:bg-slate-50"
                             }
                             ${
                               activeIndex === index
                                 ? isDark
                                   ? "bg-white/10 shadow-sm scale-105 border-yellow-500/30"
                                   : "bg-white shadow-sm scale-105 border-cyan-200"
                                 : activeIndex !== undefined
                                   ? "opacity-40"
                                   : "opacity-100"
                             }
                        `}
                onMouseEnter={() => onPieEnter(null, index)}
                onMouseLeave={onPieLeave}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.95 }}
              >
                <span
                  className={`text-xs font-semibold order-2 transition-colors duration-500
                            ${isDark ? "text-zinc-300" : "text-slate-600"}
                        `}
                >
                  {entry.name}
                </span>
                <div
                  className="w-2.5 h-2.5 rounded-full shadow-sm order-1"
                  style={{
                    backgroundColor:
                      colors[index % colors.length],
                    boxShadow: `0 0 8px ${colors[index % colors.length]}60`,
                  }}
                />
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}