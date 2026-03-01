import { useState, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface ChannelBarData {
  channel: string;
  channelAr: string;
  messages: number;
  calls: number;
  color: string;
}

interface InteractiveBarChartProps {
  data: ChannelBarData[];
  isDark?: boolean;
}

type MetricKey = "messages" | "calls" | "both";

const metricConfig: Record<MetricKey, { label: string }> = {
  both: { label: "الكل" },
  messages: { label: "رسائل" },
  calls: { label: "مكالمات" },
};

/* ─── Channel Icon SVG Paths (for rendering inside recharts) ─── */
const channelSvgPaths: Record<string, { d: string; viewBox: string }> = {
  whatsapp: {
    viewBox: "0 0 24 24",
    d: "M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51l-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z",
  },
  instagram: {
    viewBox: "0 0 24 24",
    d: "M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678a6.162 6.162 0 100 12.324 6.162 6.162 0 100-12.324zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405a1.441 1.441 0 11-2.88 0 1.441 1.441 0 012.88 0z",
  },
  x: {
    viewBox: "0 0 24 24",
    d: "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835zm-1.161 17.52h1.833L7.084 4.126H5.117z",
  },
  snapchat: {
    viewBox: "0 0 24 24",
    d: "M12 2c-3.18 0-5.2 2.14-5.2 5.3 0 .6.05 1.19.14 1.72-.6.08-1.27.22-1.73.42-.4.17-.67.5-.67.86 0 .76.93 1.1 1.88 1.38.18.05.34.1.44.15.12.06.16.12.14.22-.12.62-.52 1.2-1.2 1.74-.62.5-1.36.84-1.9 1.04-.3.11-.5.38-.5.7 0 .47.37.86.82.97.56.14 1.22.2 1.68.5.38.24.58.72.92 1.15.4.5.96 1.15 2.28 1.15.84 0 1.5-.2 2.06-.42a6.7 6.7 0 011.84-.42c.64 0 1.24.16 1.84.42.56.22 1.22.42 2.06.42 1.32 0 1.88-.66 2.28-1.15.34-.43.54-.91.92-1.15.46-.3 1.12-.36 1.68-.5.45-.11.82-.5.82-.97 0-.32-.2-.59-.5-.7-.54-.2-1.28-.54-1.9-1.04-.68-.54-1.08-1.12-1.2-1.74-.02-.1.02-.16.14-.22.1-.05.26-.1.44-.15.95-.28 1.88-.62 1.88-1.38 0-.36-.27-.69-.67-.86-.46-.2-1.13-.34-1.73-.42.09-.53.14-1.12.14-1.72C17.2 4.14 15.18 2 12 2z",
  },
  tiktok: {
    viewBox: "0 0 24 24",
    d: "M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z",
  },
  telegram: {
    viewBox: "0 0 24 24",
    d: "M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z",
  },
  website: {
    viewBox: "0 0 24 24",
    d: "M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm6.918 6h-3.215a15.876 15.876 0 00-1.396-3.704A8.026 8.026 0 0118.918 8zM12 4.04c.782 1.04 1.414 2.2 1.856 3.46h-3.712c.442-1.26 1.074-2.42 1.856-3.46zM4.26 14a7.93 7.93 0 010-4h3.48a16.533 16.533 0 000 4H4.26zm.822 2h3.215a15.876 15.876 0 001.396 3.704A8.026 8.026 0 015.082 16zM8.297 8H5.082a8.026 8.026 0 014.611-3.704A15.876 15.876 0 008.297 8zM12 19.96c-.782-1.04-1.414-2.2-1.856-3.46h3.712c-.442 1.26-1.074 2.42-1.856 3.46zM14.34 14H9.66a14.768 14.768 0 010-4h4.68a14.768 14.768 0 010 4zm.353 5.704A15.876 15.876 0 0016.089 16h3.215a8.026 8.026 0 01-4.611 3.704zM16.26 14a16.533 16.533 0 000-4h3.48a7.93 7.93 0 010 4h-3.48z",
  },
  email: {
    viewBox: "0 0 24 24",
    d: "M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-.4 4.25l-7.07 4.42c-.32.2-.74.2-1.06 0L4.4 8.25a.85.85 0 11.9-1.44L12 11l5.7-4.19a.85.85 0 01.9 1.44z",
  },
  store: {
    viewBox: "0 0 24 24",
    d: "M20 4H4v2h16V4zm1 10v-2l-1-5H4l-1 5v2h1v6h10v-6h4v6h2v-6h1zm-9 4H6v-4h6v4z",
  },
};

/* ─── Custom Y-Axis Tick with channel icons ─── */
function ChannelIconTick({ x, y, payload, sortedData, isDark }: any) {
  const channelAr = payload?.value;
  const entry = sortedData?.find((d: ChannelBarData) => d.channelAr === channelAr);
  if (!entry) return null;

  const svgData = channelSvgPaths[entry.channel];
  if (!svgData) return null;

  const iconSize = 18;

  return (
    <g transform={`translate(${x - iconSize - 6},${y - iconSize / 2})`}>
      <svg
        width={iconSize}
        height={iconSize}
        viewBox={svgData.viewBox}
        fill={entry.color}
      >
        <path d={svgData.d} />
      </svg>
    </g>
  );
}

/* ─── Custom Tooltip ─── */
function BarTooltip({ active, payload, isDark }: any) {
  if (!active || !payload?.length) return null;
  const data = payload[0]?.payload;
  if (!data) return null;

  return (
    <div
      className="rounded-xl px-4 py-3 min-w-[180px]"
      style={{
        background: isDark
          ? "linear-gradient(135deg, rgba(26,26,46,0.95), rgba(18,18,32,0.97))"
          : "linear-gradient(135deg, rgba(255,255,255,0.95), rgba(238,248,252,0.97))",
        border: isDark
          ? "1px solid rgba(212,175,55,0.2)"
          : "1px solid rgba(6,182,212,0.2)",
        boxShadow: isDark
          ? "0 12px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,55,0.08)"
          : "0 12px 40px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.5)",
        backdropFilter: "blur(16px)",
      }}
    >
      <div
        className="flex items-center gap-2 mb-2 pb-2"
        style={{
          borderBottom: isDark
            ? "1px solid rgba(212,175,55,0.12)"
            : "1px solid rgba(6,182,212,0.12)",
        }}
      >
        <span
          className="w-2.5 h-2.5 rounded-full"
          style={{ backgroundColor: data.color, boxShadow: `0 0 8px ${data.color}40` }}
        />
        <span className="text-xs" style={{ color: isDark ? "#fff" : "#000" }}>
          {data.channelAr}
        </span>
      </div>
      <div className="space-y-1.5">
        <div className="flex items-center justify-between gap-4">
          <span className="text-[11px]" style={{ color: isDark ? "rgba(255,255,255,0.6)" : "rgba(0,0,0,0.5)" }}>
            الرسائل
          </span>
          <span className="text-[11px] font-mono" style={{ color: isDark ? "#fff" : "#000" }}>
            {data.messages.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-[11px]" style={{ color: isDark ? "rgba(255,255,255,0.6)" : "rgba(0,0,0,0.5)" }}>
            المكالمات
          </span>
          <span className="text-[11px] font-mono" style={{ color: isDark ? "#fff" : "#000" }}>
            {data.calls.toLocaleString()}
          </span>
        </div>
        <div
          className="flex items-center justify-between gap-4 pt-1.5 mt-1"
          style={{
            borderTop: isDark
              ? "1px solid rgba(255,255,255,0.06)"
              : "1px solid rgba(0,0,0,0.06)",
          }}
        >
          <span className="text-[11px]" style={{ color: isDark ? "rgba(212,175,55,0.8)" : "rgba(6,182,212,0.8)" }}>
            الإجمالي
          </span>
          <span className="text-[11px] font-mono" style={{ color: isDark ? "#D4AF37" : "#06B6D4" }}>
            {(data.messages + data.calls).toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Component ─── */
export function InteractiveBarChart({ data, isDark = true }: InteractiveBarChartProps) {
  const [activeMetric, setActiveMetric] = useState<MetricKey>("both");
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [sortBy, setSortBy] = useState<"default" | "messages" | "calls">("default");

  const sortedData = [...data].sort((a, b) => {
    if (sortBy === "messages") return a.messages - b.messages;
    if (sortBy === "calls") return a.calls - b.calls;
    return 0;
  });

  const handleBarMouseEnter = useCallback((_: any, index: number) => {
    setHoveredIndex(index);
  }, []);

  const handleBarMouseLeave = useCallback(() => {
    setHoveredIndex(null);
  }, []);

  const accentColor = isDark ? "#D4AF37" : "#06B6D4";
  const accentBg = isDark ? "rgba(212,175,55," : "rgba(6,182,212,";

  return (
    <div className="relative w-full h-full flex flex-col">
      {/* ── Controls ── */}
      <div className="flex items-center justify-between gap-3 mb-3 px-1 shrink-0">
        {/* Metric Toggle */}
        <div
          className="flex items-center gap-0.5 rounded-lg p-0.5"
          style={{ background: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.04)" }}
        >
          {(Object.entries(metricConfig) as [MetricKey, { label: string }][]).map(([key, { label }]) => (
            <button
              key={key}
              onClick={() => setActiveMetric(key)}
              className="px-2.5 py-1 rounded-md text-[10px] transition-all duration-200 cursor-pointer"
              style={{
                background: activeMetric === key ? `${accentBg}0.15)` : "transparent",
                color: activeMetric === key ? accentColor : (isDark ? "#9CA3AF" : "#6B7280"),
                border: activeMetric === key
                  ? `1px solid ${accentBg}0.25)`
                  : "1px solid transparent",
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Sort Toggle */}
        <div
          className="flex items-center gap-0.5 rounded-lg p-0.5"
          style={{ background: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.04)" }}
        >
          {([
            ["default", "افتراضي"],
            ["messages", "الرسائل"],
            ["calls", "المكالمات"],
          ] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSortBy(key)}
              className="px-2 py-1 rounded-md text-[10px] transition-all duration-200 cursor-pointer"
              style={{
                background: sortBy === key ? `${accentBg}0.15)` : "transparent",
                color: sortBy === key ? accentColor : (isDark ? "#9CA3AF" : "#6B7280"),
                border: sortBy === key
                  ? `1px solid ${accentBg}0.25)`
                  : "1px solid transparent",
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Chart ── */}
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={sortedData}
            layout="vertical"
            margin={{ top: 8, right: 24, left: 0, bottom: 8 }}
            barGap={2}
            barCategoryGap="20%"
            onMouseLeave={handleBarMouseLeave}
          >
            <CartesianGrid
              strokeDasharray="2 8"
              stroke={isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.06)"}
              horizontal={false}
            />
            <XAxis
              type="number"
              tick={{ fontSize: 10, fill: isDark ? "rgba(255,255,255,0.7)" : "rgba(0,0,0,0.6)" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v))}
            />
            <YAxis
              dataKey="channelAr"
              type="category"
              width={40}
              axisLine={false}
              tickLine={false}
              orientation="left"
              tick={(props: any) => (
                <ChannelIconTick
                  {...props}
                  sortedData={sortedData}
                  isDark={isDark}
                />
              )}
            />
            <Tooltip
              content={<BarTooltip isDark={isDark} />}
              cursor={{
                fill: isDark ? "rgba(212,175,55,0.04)" : "rgba(6,182,212,0.06)",
              }}
            />

            {(activeMetric === "both" || activeMetric === "messages") && (
              <Bar
                dataKey="messages"
                name="رسائل"
                radius={[0, 6, 6, 0]}
                animationDuration={800}
                animationEasing="ease-out"
                onMouseEnter={handleBarMouseEnter}
                onMouseLeave={handleBarMouseLeave}
              >
                {sortedData.map((entry, index) => {
                  const isHovered = hoveredIndex === index;
                  return (
                    <Cell
                      key={`msg-${entry.channel}`}
                      fill={entry.color}
                      fillOpacity={hoveredIndex !== null ? (isHovered ? 0.9 : 0.25) : 0.75}
                      style={{ transition: "fill-opacity 0.3s ease" }}
                    />
                  );
                })}
              </Bar>
            )}

            {(activeMetric === "both" || activeMetric === "calls") && (
              <Bar
                dataKey="calls"
                name="مكالمات"
                radius={[0, 6, 6, 0]}
                animationDuration={1000}
                animationEasing="ease-out"
                onMouseEnter={handleBarMouseEnter}
                onMouseLeave={handleBarMouseLeave}
              >
                {sortedData.map((entry, index) => {
                  const isHovered = hoveredIndex === index;
                  return (
                    <Cell
                      key={`call-${entry.channel}`}
                      fill={entry.color}
                      fillOpacity={hoveredIndex !== null ? (isHovered ? 0.55 : 0.1) : 0.35}
                      style={{ transition: "fill-opacity 0.3s ease" }}
                    />
                  );
                })}
              </Bar>
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Legend ── */}
      <div className="flex items-center justify-center gap-5 mt-2 shrink-0">
        {(activeMetric === "both" || activeMetric === "messages") && (
          <div className="flex items-center gap-1.5">
            <span
              className="w-3 h-2 rounded-sm"
              style={{ background: accentColor, opacity: 0.75 }}
            />
            <span className="text-[10px]" style={{ color: isDark ? "rgba(255,255,255,0.7)" : "rgba(0,0,0,0.6)" }}>
              رسائل (قوي)
            </span>
          </div>
        )}
        {(activeMetric === "both" || activeMetric === "calls") && (
          <div className="flex items-center gap-1.5">
            <span
              className="w-3 h-2 rounded-sm"
              style={{ background: accentColor, opacity: 0.35 }}
            />
            <span className="text-[10px]" style={{ color: isDark ? "rgba(255,255,255,0.7)" : "rgba(0,0,0,0.6)" }}>
              مكالمات (خفيف)
            </span>
          </div>
        )}
      </div>
    </div>
  );
}