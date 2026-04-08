import { useState, useMemo, useCallback } from "react";

interface LeadData {
  channel: string;
  channelAr: string;
  leads: number;
  color: string;
}

interface Props {
  data: LeadData[];
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(
  cx: number, cy: number, r: number,
  startAngle: number, endAngle: number
) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
}

// ── Channel SVG icon paths (designed for 24×24 viewBox) ──────────
// Each icon is a minimal, elegant representation of the platform
const channelIconPaths: Record<string, { paths: string[]; fillRule?: "evenodd" }> = {
  whatsapp: {
    paths: [
      // Phone in speech bubble
      "M12 2C6.48 2 2 6.48 2 12c0 1.77.46 3.43 1.27 4.88L2 22l5.23-1.24A9.96 9.96 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.62 0-3.13-.47-4.41-1.28l-.31-.19-3.24.77.81-3.16-.21-.33A7.96 7.96 0 014 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8zm4.38-5.97c-.24-.12-1.42-.7-1.64-.78-.22-.08-.38-.12-.54.12-.16.24-.62.78-.76.94-.14.16-.28.18-.52.06-.24-.12-1.01-.37-1.93-1.18-.71-.63-1.19-1.41-1.33-1.65-.14-.24-.02-.37.1-.49.11-.11.24-.28.36-.42.12-.14.16-.24.24-.4.08-.16.04-.3-.02-.42-.06-.12-.54-1.3-.74-1.78-.2-.47-.4-.4-.54-.41h-.46c-.16 0-.42.06-.64.3-.22.24-.84.82-.84 2s.86 2.32.98 2.48c.12.16 1.7 2.6 4.12 3.64.58.25 1.03.4 1.38.51.58.18 1.1.16 1.52.1.46-.07 1.42-.58 1.62-1.14.2-.56.2-1.04.14-1.14-.06-.1-.22-.16-.46-.28z",
    ],
  },
  instagram: {
    paths: [
      // Camera with rounded square
      "M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 01-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 017.8 2zm-.2 2A3.6 3.6 0 004 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 003.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6zm9.65 1.5a1.25 1.25 0 110 2.5 1.25 1.25 0 010-2.5zM12 7a5 5 0 110 10 5 5 0 010-10zm0 2a3 3 0 100 6 3 3 0 000-6z",
    ],
  },
  x: {
    paths: [
      // X / Twitter logo
      "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835zm-1.161 17.52h1.833L7.084 4.126H5.117z",
    ],
  },
  snapchat: {
    paths: [
      // Ghost shape
      "M12 2c-3.18 0-5.2 2.14-5.2 5.3 0 .6.05 1.19.14 1.72-.6.08-1.27.22-1.73.42-.4.17-.67.5-.67.86 0 .76.93 1.1 1.88 1.38.18.05.34.1.44.15.12.06.16.12.14.22-.12.62-.52 1.2-1.2 1.74-.62.5-1.36.84-1.9 1.04-.3.11-.5.38-.5.7 0 .47.37.86.82.97.56.14 1.22.2 1.68.5.38.24.58.72.92 1.15.4.5.96 1.15 2.28 1.15.84 0 1.5-.2 2.06-.42a6.7 6.7 0 011.84-.42c.64 0 1.24.16 1.84.42.56.22 1.22.42 2.06.42 1.32 0 1.88-.66 2.28-1.15.34-.43.54-.91.92-1.15.46-.3 1.12-.36 1.68-.5.45-.11.82-.5.82-.97 0-.32-.2-.59-.5-.7-.54-.2-1.28-.54-1.9-1.04-.68-.54-1.08-1.12-1.2-1.74-.02-.1.02-.16.14-.22.1-.05.26-.1.44-.15.95-.28 1.88-.62 1.88-1.38 0-.36-.27-.69-.67-.86-.46-.2-1.13-.34-1.73-.42.09-.53.14-1.12.14-1.72C17.2 4.14 15.18 2 12 2z",
    ],
  },
  tiktok: {
    paths: [
      // Musical note / TikTok style
      "M16.6 5.82A4.278 4.278 0 0113.25 3h-3.1v12.4a2.592 2.592 0 01-2.593 2.545 2.592 2.592 0 01-2.593-2.593 2.592 2.592 0 012.593-2.593c.265 0 .52.04.76.114V9.702a5.765 5.765 0 00-.76-.051 5.768 5.768 0 00-5.767 5.767 5.768 5.768 0 005.767 5.767 5.768 5.768 0 005.767-5.767V9.34a7.392 7.392 0 004.325 1.392V7.58a4.283 4.283 0 01-2.394-.76z",
    ],
  },
  telegram: {
    paths: [
      // Paper plane
      "M20.665 3.717l-17.73 6.837c-1.21.486-1.203 1.161-.222 1.462l4.552 1.42 10.532-6.645c.498-.303.953-.14.579.192l-8.533 7.701h-.002l.002.001-.314 4.692c.46 0 .663-.211.921-.46l2.211-2.15 4.599 3.397c.848.467 1.457.227 1.668-.785l3.019-14.228c.309-1.239-.473-1.8-1.282-1.434z",
    ],
  },
  website: {
    paths: [
      // Globe
      "M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm6.918 6h-3.215a15.876 15.876 0 00-1.396-3.704A8.026 8.026 0 0118.918 8zM12 4.04c.782 1.04 1.414 2.2 1.856 3.46h-3.712c.442-1.26 1.074-2.42 1.856-3.46zM4.26 14a7.93 7.93 0 010-4h3.48a16.533 16.533 0 000 4H4.26zm.822 2h3.215a15.876 15.876 0 001.396 3.704A8.026 8.026 0 015.082 16zM8.297 8H5.082a8.026 8.026 0 014.611-3.704A15.876 15.876 0 008.297 8zM12 19.96c-.782-1.04-1.414-2.2-1.856-3.46h3.712c-.442 1.26-1.074 2.42-1.856 3.46zM14.34 14H9.66a14.768 14.768 0 010-4h4.68a14.768 14.768 0 010 4zm.353 5.704A15.876 15.876 0 0016.089 16h3.215a8.026 8.026 0 01-4.611 3.704zM16.26 14a16.533 16.533 0 000-4h3.48a7.93 7.93 0 010 4h-3.48z",
    ],
  },
  email: {
    paths: [
      // Envelope
      "M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-.4 4.25l-7.07 4.42c-.32.2-.74.2-1.06 0L4.4 8.25a.85.85 0 11.9-1.44L12 11l5.7-4.19a.85.85 0 01.9 1.44z",
    ],
  },
  store: {
    paths: [
      // Luxury store / boutique
      "M20 4H4v2h16V4zm1 10v-2l-1-5H4l-1 5v2h1v6h10v-6h4v6h2v-6h1zm-9 4H6v-4h6v4z",
    ],
  },
};

// Render a channel icon as SVG <g> positioned at (x, y) with given size
function ChannelIcon({
  channel, x, y, size, color, isHovered,
}: {
  channel: string; x: number; y: number; size: number;
  color: string; isHovered: boolean;
}) {
  const icon = channelIconPaths[channel];
  if (!icon) return null;
  const scale = size / 24;
  // Center the icon at (x, y)
  const tx = x - size / 2;
  const ty = y - size / 2;
  return (
    <g
      transform={`translate(${tx}, ${ty}) scale(${scale})`}
      opacity={isHovered ? 1 : 0.8}
      style={{ transition: "opacity 0.3s ease" }}
    >
      {icon.paths.map((d, pi) => (
        <path
          key={pi}
          d={d}
          fill={isHovered ? "#fff" : color}
          fillRule={icon.fillRule || "nonzero"}
          style={{ transition: "fill 0.3s ease" }}
        />
      ))}
    </g>
  );
}

export function RadialLeadsChart({ data }: Props) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Sort descending — outermost = largest value
  const sorted = useMemo(() => {
    return [...data].filter(d => d.leads > 0).sort((a, b) => b.leads - a.leads);
  }, [data]);

  const maxValue = useMemo(() => Math.max(...sorted.map(d => d.leads)), [sorted]);
  const totalLeads = useMemo(() => sorted.reduce((s, d) => s + d.leads, 0), [sorted]);

  // Layout constants
  const viewW = 620;
  const viewH = 440;
  const cx = 200;
  const cy = 215;
  const baseRadius = 40;
  const ringWidth = 13;
  const ringGap = 5;
  const startAngle = 135; // bottom-left, sweeping clockwise through top to right
  const maxSweep = 280;

  // Fix certain channel colors for dark-mode visibility
  const getColor = useCallback((item: LeadData) => {
    if (item.channel === "tiktok") return "#ff0050";
    if (item.channel === "snapchat") return "#FFDB00";
    return item.color;
  }, []);

  const handleMouseEnter = useCallback((i: number) => setHoveredIndex(i), []);
  const handleMouseLeave = useCallback(() => setHoveredIndex(null), []);

  // Labels on the right side
  const labelStartX = 420;
  const labelStartY = 28;
  const labelSpacing = 44;

  return (
    <div className="w-full h-full flex items-center justify-center overflow-hidden">
      <svg
        viewBox={`0 0 ${viewW} ${viewH}`}
        className="w-full h-full"
        style={{ maxHeight: 440 }}
      >
        <defs>
          {sorted.map((item, i) => {
            const color = getColor(item);
            return (
              <filter key={`glow-${i}`} id={`radial-glow-${i}`} x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="5" result="blur" />
                <feFlood floodColor={color} floodOpacity="0.5" result="color" />
                <feComposite in="color" in2="blur" operator="in" result="shadow" />
                <feMerge>
                  <feMergeNode in="shadow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            );
          })}
          <radialGradient id="radial-center-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.2" />
            <stop offset="70%" stopColor="var(--primary)" stopOpacity="0.05" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Background decorative elements */}
        <circle cx={cx} cy={cy} r={baseRadius - 6} fill="url(#radial-center-glow)" />
        <circle
          cx={cx} cy={cy}
          r={baseRadius - 10}
          fill="none"
          stroke="var(--border)"
          strokeWidth="0.5"
          strokeDasharray="2 3"
          opacity={0.25}
        />
        {/* Outer decorative ring */}
        <circle
          cx={cx} cy={cy}
          r={baseRadius + sorted.length * (ringWidth + ringGap) + 14}
          fill="none"
          stroke="var(--border)"
          strokeWidth="0.5"
          strokeDasharray="1 4"
          opacity={0.12}
        />

        {/* Center text */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          className="fill-foreground"
          style={{ fontSize: 16, fontFamily: "Tajawal, sans-serif" }}
        >
          {totalLeads.toLocaleString()}
        </text>
        <text
          x={cx}
          y={cy + 14}
          textAnchor="middle"
          className="fill-muted-foreground"
          style={{ fontSize: 8, fontFamily: "Tajawal, sans-serif" }}
        >
          عميل محتمل
        </text>

        {/* Inner decorative rings */}
        <circle
          cx={cx} cy={cy}
          r={baseRadius - 2}
          fill="none"
          stroke="var(--primary)"
          strokeWidth="0.8"
          opacity={0.15}
        />

        {/* Track arcs (background) */}
        {sorted.map((_, i) => {
          const r = baseRadius + i * (ringWidth + ringGap);
          const trackPath = describeArc(cx, cy, r, startAngle, startAngle + maxSweep);
          return (
            <path
              key={`track-${i}`}
              d={trackPath}
              fill="none"
              stroke="var(--border)"
              strokeWidth={ringWidth}
              strokeLinecap="round"
              opacity={0.08}
            />
          );
        })}

        {/* Data arcs + connectors */}
        {sorted.map((item, i) => {
          const r = baseRadius + i * (ringWidth + ringGap);
          const pct = item.leads / maxValue;
          const sweep = pct * maxSweep;
          const endAngle = startAngle + sweep;
          const arcPath = describeArc(cx, cy, r, startAngle, endAngle);
          const isHovered = hoveredIndex === i;
          const color = getColor(item);

          // Connector origin: use a point on the right side of the ring
          const connectorAngle = sweep > 100 ? startAngle + Math.min(sweep * 0.65, sweep - 20) : endAngle;
          const connectorOrigin = polarToCartesian(cx, cy, r + (ringWidth / 2), connectorAngle);

          // Label position
          const labelY = labelStartY + i * labelSpacing;
          const labelX = labelStartX;

          // Endpoint dot
          const endpoint = polarToCartesian(cx, cy, r, endAngle);

          // Rotated connector origin (180° around center) for hover state
          const connectorOriginRotated = {
            x: 2 * cx - connectorOrigin.x,
            y: 2 * cy - connectorOrigin.y,
          };

          return (
            <g key={item.channel}>
              {/* Arc group — rotates 180° around center on hover */}
              <g
                style={{
                  transformOrigin: `${cx}px ${cy}px`,
                  transform: isHovered ? "rotate(180deg)" : "rotate(0deg)",
                  transition: "transform 0.85s cubic-bezier(0.4, 0, 0.2, 1)",
                }}
              >
                {/* Data arc */}
                <path
                  d={arcPath}
                  fill="none"
                  stroke={color}
                  strokeWidth={isHovered ? ringWidth + 5 : ringWidth}
                  strokeLinecap="round"
                  opacity={hoveredIndex !== null && !isHovered ? 0.2 : isHovered ? 1 : 0.7}
                  filter={isHovered ? `url(#radial-glow-${i})` : undefined}
                  style={{
                    transition: "stroke-width 0.4s ease, opacity 0.4s ease, filter 0.4s ease",
                    cursor: "pointer",
                  }}
                  onMouseEnter={() => handleMouseEnter(i)}
                  onMouseLeave={handleMouseLeave}
                />

                {/* Arc endpoint dot */}
                <circle
                  cx={endpoint.x}
                  cy={endpoint.y}
                  r={isHovered ? 5 : 2.5}
                  fill={isHovered ? color : "var(--background)"}
                  stroke={color}
                  strokeWidth={isHovered ? 2.5 : 1.5}
                  style={{
                    transition: "r 0.4s ease, fill 0.4s ease, stroke-width 0.4s ease",
                    cursor: "pointer",
                  }}
                  onMouseEnter={() => handleMouseEnter(i)}
                  onMouseLeave={handleMouseLeave}
                />

                {/* Percentage on arc midpoint — counter-rotated to stay readable */}
                {isHovered && (() => {
                  const mid = polarToCartesian(cx, cy, r, startAngle + sweep * 0.4);
                  return (
                    <text
                      x={mid.x}
                      y={mid.y}
                      textAnchor="middle"
                      dominantBaseline="central"
                      style={{
                        fontSize: 10,
                        fontFamily: "monospace",
                        pointerEvents: "none",
                        fontWeight: 700,
                        transformOrigin: `${mid.x}px ${mid.y}px`,
                        transform: "rotate(180deg)",
                      }}
                      className="fill-foreground"
                    >
                      {((item.leads / totalLeads) * 100).toFixed(0)}%
                    </text>
                  );
                })()}
              </g>

              {/* Connector line (hover) — uses rotated coordinates */}
              <g
                opacity={isHovered ? 1 : 0}
                style={{ transition: "opacity 0.35s ease 0.45s" }}
              >
                <line
                  x1={connectorOriginRotated.x}
                  y1={connectorOriginRotated.y}
                  x2={labelX - 14}
                  y2={labelY + 12}
                  stroke={color}
                  strokeWidth={1.2}
                  strokeDasharray="3 2"
                  opacity={0.7}
                />
                {/* Connector origin dot */}
                <circle
                  cx={connectorOriginRotated.x}
                  cy={connectorOriginRotated.y}
                  r={3}
                  fill={color}
                  opacity={0.9}
                />
                {/* Connector end dot */}
                <circle
                  cx={labelX - 14}
                  cy={labelY + 12}
                  r={3.5}
                  fill={color}
                  opacity={0.9}
                />
              </g>

              {/* Right-side label (always visible) */}
              <g
                opacity={hoveredIndex !== null && !isHovered ? 0.2 : 1}
                style={{
                  transition: "opacity 0.35s ease",
                  cursor: "pointer",
                }}
                onMouseEnter={() => handleMouseEnter(i)}
                onMouseLeave={handleMouseLeave}
              >
                {/* Color bar indicator */}
                <rect
                  x={labelX + 85}
                  y={labelY + 2}
                  width={3}
                  height={isHovered ? 24 : 20}
                  rx={1.5}
                  fill={color}
                  opacity={isHovered ? 1 : 0.5}
                  style={{ transition: "all 0.3s ease" }}
                />

                {/* Channel name */}
                <text
                  x={labelX}
                  y={labelY + 10}
                  style={{
                    fontSize: isHovered ? 12 : 10,
                    fontFamily: "Tajawal, sans-serif",
                    fontWeight: isHovered ? 700 : 400,
                    transition: "all 0.3s ease",
                    direction: "ltr",
                  }}
                  className={isHovered ? "fill-foreground" : "fill-muted-foreground"}
                >
                  {item.channelAr}
                </text>

                {/* Leads count + percentage */}
                <text
                  x={labelX}
                  y={labelY + 24}
                  textAnchor="start"
                  style={{
                    fontSize: 9,
                    fontFamily: "monospace",
                    direction: "ltr",
                    unicodeBidi: "embed",
                  }}
                  className="fill-muted-foreground"
                >
                  {`\u200E${item.leads.toLocaleString()} عميل`}
                  {isHovered ? `\u200E  ·  ${((item.leads / totalLeads) * 100).toFixed(1)}%` : ""}
                </text>

                {/* Channel icon badge */}
                <rect
                  x={labelX + 92}
                  y={labelY}
                  width={24}
                  height={24}
                  rx={7}
                  fill={isHovered ? color : `${color}18`}
                  stroke={isHovered ? color : `${color}40`}
                  strokeWidth={isHovered ? 1.5 : 0.8}
                  style={{ transition: "all 0.3s ease" }}
                />
                <ChannelIcon
                  channel={item.channel}
                  x={labelX + 104}
                  y={labelY + 12}
                  size={13}
                  color={color}
                  isHovered={isHovered}
                />
              </g>
            </g>
          );
        })}

        {/* Decorative inner ring */}
        <circle
          cx={cx} cy={cy}
          r={baseRadius - 6}
          fill="none"
          stroke="var(--primary)"
          strokeWidth="0.5"
          opacity={0.1}
        />
      </svg>
    </div>
  );
}