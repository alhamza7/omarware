import { useMemo, useState, useCallback, useEffect, useRef } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";

interface Channel3DData {
  channel: string;
  channelAr: string;
  color: string;
  values: number[];
}

interface ThreeAreaChart3DProps {
  channels: Channel3DData[];
  labels: string[];
  isDark?: boolean;
  activePeriod?: "day" | "month" | "year";
  onPeriodChange?: (period: "day" | "month" | "year") => void;
}

/* ═══════════════════════════════════════════
   Animated Floating Particles (Canvas)
   ═══════════════════════════════════════════ */
function FloatingParticles({ isDark }: { isDark: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }
    };
    resize();

    const particles = Array.from({ length: 24 }, () => ({
      x: Math.random() * (canvas.width || 600),
      y: Math.random() * (canvas.height || 400),
      r: Math.random() * 1.6 + 0.3,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.15 - 0.12,
      opacity: Math.random() * 0.35 + 0.08,
      phase: Math.random() * Math.PI * 2,
    }));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const time = Date.now() * 0.001;

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        const flicker = 0.5 + 0.5 * Math.sin(time * 1.5 + p.phase);
        const alpha = p.opacity * flicker;

        // Core dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = isDark
          ? `rgba(212, 175, 55, ${alpha})`
          : `rgba(6, 182, 212, ${alpha})`;
        ctx.fill();

        // Soft glow halo
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 3.5, 0, Math.PI * 2);
        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 3.5);
        grad.addColorStop(0, isDark
          ? `rgba(212, 175, 55, ${alpha * 0.25})`
          : `rgba(6, 182, 212, ${alpha * 0.25})`);
        grad.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = grad;
        ctx.fill();
      });

      frameRef.current = requestAnimationFrame(animate);
    };
    animate();

    const ro = new ResizeObserver(resize);
    if (canvas.parentElement) ro.observe(canvas.parentElement);

    return () => {
      cancelAnimationFrame(frameRef.current);
      ro.disconnect();
    };
  }, [isDark]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 2 }}
    />
  );
}

/* ═══════════════════════════════════════════
   Animated Cursor Line (breathes)
   ═══════════════════════════════════════════ */
function AnimatedCursor({ points, height, isDark }: any) {
  if (!points?.[0]) return null;
  const { x } = points[0];
  const color = isDark ? "212,175,55" : "6,182,212";
  return (
    <g>
      {/* Glow behind line */}
      <line
        x1={x} y1={0} x2={x} y2={height}
        stroke={`rgba(${color},0.12)`}
        strokeWidth={8}
      />
      {/* Main dashed line */}
      <line
        x1={x} y1={0} x2={x} y2={height}
        stroke={`rgba(${color},0.4)`}
        strokeWidth={1}
      >
        <animate attributeName="stroke-opacity" values="0.2;0.5;0.2" dur="2s" repeatCount="indefinite" />
      </line>
    </g>
  );
}

/* ═══════════════════════════════════════════
   Pulsing Active Dot
   ═══════════════════════════════════════════ */
function PulsingDot({ cx, cy, stroke, fill }: any) {
  return (
    <g>
      {/* Outer expanding ring */}
      <circle cx={cx} cy={cy} r={8} fill="none" stroke={stroke} strokeWidth={1}>
        <animate attributeName="r" values="5;14;5" dur="2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.5;0;0.5" dur="2s" repeatCount="indefinite" />
      </circle>
      {/* Mid glow */}
      <circle cx={cx} cy={cy} r={6} fill={stroke} opacity={0.12}>
        <animate attributeName="r" values="4;8;4" dur="1.5s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.18;0.04;0.18" dur="1.5s" repeatCount="indefinite" />
      </circle>
      {/* Core dot */}
      <circle cx={cx} cy={cy} r={3.5} fill={fill} stroke={stroke} strokeWidth={2} />
      {/* Inner highlight */}
      <circle cx={cx - 0.8} cy={cy - 0.8} r={1} fill="rgba(255,255,255,0.55)" />
    </g>
  );
}

/* ═══════════════════════════════════════════
   Luxury Glass Tooltip
   ═══════════════════════════════════════════ */
function LuxuryTooltip({ active, payload, label, isDark }: any) {
  if (!active || !payload?.length) return null;

  const sorted = [...payload].sort((a: any, b: any) => (b.value ?? 0) - (a.value ?? 0));
  const total = sorted.reduce((s: number, e: any) => s + (e.value ?? 0), 0);

  return (
    <div
      className="rounded-2xl px-4 py-3 min-w-[210px]"
      style={{
        background: isDark
          ? "linear-gradient(135deg, rgba(26,26,46,0.94), rgba(18,18,32,0.97))"
          : "linear-gradient(135deg, rgba(255,255,255,0.94), rgba(238,248,252,0.97))",
        border: isDark
          ? "1px solid rgba(212,175,55,0.22)"
          : "1px solid rgba(6,182,212,0.22)",
        boxShadow: isDark
          ? "0 14px 44px rgba(0,0,0,0.5), 0 0 24px rgba(212,175,55,0.06), inset 0 1px 0 rgba(212,175,55,0.08)"
          : "0 14px 44px rgba(0,0,0,0.1), 0 0 24px rgba(6,182,212,0.06), inset 0 1px 0 rgba(255,255,255,0.5)",
        backdropFilter: "blur(20px)",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-2 pb-2"
        style={{
          borderBottom: isDark
            ? "1px solid rgba(212,175,55,0.12)"
            : "1px solid rgba(6,182,212,0.12)",
        }}
      >
        <span className="text-xs text-muted-foreground">{label}</span>
        <span
          className="text-[10px] font-mono px-2 py-0.5 rounded-full"
          style={{
            background: isDark ? "rgba(212,175,55,0.1)" : "rgba(6,182,212,0.1)",
            color: isDark ? "#D4AF37" : "#06B6D4",
          }}
        >
          {total.toLocaleString()}
        </span>
      </div>
      {/* Rows */}
      <div className="space-y-1.5">
        {sorted.map((entry: any, i: number) => {
          const pct = total > 0 ? ((entry.value / total) * 100).toFixed(1) : "0";
          return (
            <div key={i} className="flex items-center gap-2">
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{
                  backgroundColor: entry.color,
                  boxShadow: `0 0 6px ${entry.color}50`,
                }}
              />
              <span className="text-[11px] text-foreground/75 flex-1 truncate">
                {entry.name}
              </span>
              <span className="text-[10px] font-mono text-foreground/40 me-1">
                {pct}%
              </span>
              <span className="text-[11px] font-mono text-foreground">
                {Number(entry.value).toLocaleString()}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   Interactive Legend (click to toggle)
   ═══════════════════════════════════════════ */
function InteractiveLegend({
  payload,
  hidden,
  onToggle,
}: {
  payload?: any[];
  hidden: Set<string>;
  onToggle: (name: string) => void;
}) {
  if (!payload?.length) return null;
  return (
    <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1.5 mt-3 px-4">
      {payload.map((entry: any, i: number) => {
        const isHidden = hidden.has(entry.value);
        return (
          <button
            key={i}
            onClick={() => onToggle(entry.value)}
            className="flex items-center gap-1.5 text-[10px] transition-all duration-300 px-2 py-0.5 rounded-full hover:scale-105 cursor-pointer"
            style={{
              opacity: isHidden ? 0.3 : 1,
              background: isHidden ? "transparent" : `${entry.color}10`,
              border: `1px solid ${isHidden ? "transparent" : `${entry.color}20`}`,
            }}
          >
            <span
              className="w-3 h-1.5 rounded-full inline-block transition-all duration-300"
              style={{
                backgroundColor: entry.color,
                opacity: isHidden ? 0.3 : 0.9,
                boxShadow: isHidden ? "none" : `0 0 6px ${entry.color}40`,
              }}
            />
            <span className="text-foreground/70">{entry.value}</span>
          </button>
        );
      })}
    </div>
  );
}

/* ═══════════════════════════════════════════
   Main Chart Component
   ═══════════════════════════════════════════ */
export function ThreeAreaChart3D({
  channels,
  labels,
  isDark = true,
  activePeriod,
  onPeriodChange,
}: ThreeAreaChart3DProps) {
  const [hiddenChannels, setHiddenChannels] = useState<Set<string>>(new Set());

  const toggleChannel = useCallback((name: string) => {
    setHiddenChannels((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }, []);

  const chartData = useMemo(() => {
    if (!channels.length || !labels.length) return [];
    return labels.map((label, i) => {
      const point: Record<string, any> = { period: label };
      channels.forEach((ch) => {
        point[ch.channelAr] = ch.values[i] ?? 0;
      });
      return point;
    });
  }, [channels, labels]);

  if (!chartData.length) {
    return (
      <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm">
        لا توجد بيانات للعرض
      </div>
    );
  }

  return (
    <div className="relative w-full h-full overflow-hidden rounded-xl">
      {/* ── Period Selector (Day / Month / Year) ── */}
      {onPeriodChange && activePeriod && (
        <div className="absolute top-2 end-3 flex items-center gap-1 rounded-lg p-0.5" style={{ zIndex: 10, background: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.05)" }}>
          {([["day", "يومي"], ["month", "شهري"], ["year", "سنوي"]] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => onPeriodChange(key)}
              className="px-3 py-1 rounded-md text-[11px] transition-all duration-200 cursor-pointer"
              style={{
                background: activePeriod === key
                  ? (isDark ? "rgba(212,175,55,0.18)" : "rgba(6,182,212,0.18)")
                  : "transparent",
                color: activePeriod === key
                  ? (isDark ? "#D4AF37" : "#06B6D4")
                  : (isDark ? "#9CA3AF" : "#6B7280"),
                border: activePeriod === key
                  ? `1px solid ${isDark ? "rgba(212,175,55,0.3)" : "rgba(6,182,212,0.3)"}`
                  : "1px solid transparent",
              }}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* ── Ambient radial glow ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: isDark
            ? "radial-gradient(ellipse 60% 45% at 50% 85%, rgba(212,175,55,0.045) 0%, transparent 70%)"
            : "radial-gradient(ellipse 60% 45% at 50% 85%, rgba(6,182,212,0.06) 0%, transparent 70%)",
          zIndex: 0,
        }}
      />

      {/* ── Top edge shimmer line ── */}
      <div
        className="absolute top-0 inset-x-0 h-px pointer-events-none"
        style={{
          background: isDark
            ? "linear-gradient(90deg, transparent 10%, rgba(212,175,55,0.18) 50%, transparent 90%)"
            : "linear-gradient(90deg, transparent 10%, rgba(6,182,212,0.18) 50%, transparent 90%)",
          zIndex: 3,
        }}
      />

      {/* ── Floating particles ── */}
      <FloatingParticles isDark={isDark} />

      {/* ── Chart ── */}
      <div className="relative w-full h-full" style={{ zIndex: 1 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 20, right: 16, left: 8, bottom: 40 }}
          >
            <defs>
              {channels.map((ch) => {
                const color = ch.color;
                return [
                  /* Rich multi-stop fill gradient */
                  <linearGradient
                    key={`fill-${ch.channel}`}
                    id={`areaFill-${ch.channel}`}
                    x1="0" y1="0" x2="0" y2="1"
                  >
                    <stop offset="0%" stopColor={color} stopOpacity={0.48} />
                    <stop offset="30%" stopColor={color} stopOpacity={0.18} />
                    <stop offset="65%" stopColor={color} stopOpacity={0.05} />
                    <stop offset="100%" stopColor={color} stopOpacity={0} />
                  </linearGradient>,
                ];
              }).flat()}
            </defs>

            <CartesianGrid
              strokeDasharray="2 8"
              stroke={isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)"}
              vertical={false}
            />

            <XAxis
              dataKey="period"
              tick={{ fontSize: 11, fill: isDark ? "#FFFFFF" : "#000000" }}
              axisLine={{ stroke: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.12)" }}
              tickLine={false}
              dy={10}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 11, fill: isDark ? "#FFFFFF" : "#000000" }}
              axisLine={false}
              tickLine={false}
              width={45}
              tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v))}
            />

            <Tooltip
              content={<LuxuryTooltip isDark={isDark} />}
              cursor={<AnimatedCursor isDark={isDark} />}
            />

            <Legend
              content={
                <InteractiveLegend
                  hidden={hiddenChannels}
                  onToggle={toggleChannel}
                />
              }
            />

            {channels.map((ch, idx) => {
              const isHidden = hiddenChannels.has(ch.channelAr);
              return (
                <Area
                  key={ch.channel}
                  type="monotone"
                  dataKey={ch.channelAr}
                  stroke={ch.color}
                  strokeWidth={isHidden ? 0 : 2.2}
                  fill={`url(#areaFill-${ch.channel})`}
                  fillOpacity={isHidden ? 0 : 1}
                  animationDuration={1200 + idx * 200}
                  animationEasing="ease-out"
                  dot={false}
                  activeDot={
                    isHidden
                      ? false
                      : (props: any) => (
                          <PulsingDot
                            {...props}
                            stroke={ch.color}
                            fill={isDark ? "#1a1a2e" : "#e3edf2"}
                          />
                        )
                  }
                  hide={isHidden}
                />
              );
            })}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}