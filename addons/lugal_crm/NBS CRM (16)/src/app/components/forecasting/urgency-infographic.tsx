import { useState } from "react";
import { motion } from "motion/react";
import { AlertCircle, AlertTriangle, CheckCircle, Archive } from "lucide-react";

interface UrgencyItem {
  name: string;
  value: number;
  fill: string;
}

const icons = [AlertCircle, AlertTriangle, CheckCircle, Archive];

export function UrgencyInfographic({ data }: { data: UrgencyItem[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const total = data.reduce((s, d) => s + d.value, 0);

  // Positions for 4 segments: top-right, bottom-right, bottom-left, top-left
  const segments = data.map((item, i) => {
    const angleDeg = -45 + i * 90; // -45, 45, 135, 225
    const angleRad = (angleDeg * Math.PI) / 180;
    const arrowDist = 72;
    const labelDist = 120;
    return {
      ...item,
      icon: icons[i],
      angleDeg,
      angleRad,
      ax: Math.cos(angleRad) * arrowDist,
      ay: Math.sin(angleRad) * arrowDist,
      lx: Math.cos(angleRad) * labelDist,
      ly: Math.sin(angleRad) * labelDist,
    };
  });

  // Arrow/pentagon shape pointing outward from center
  function arrowPath(angleDeg: number): string {
    const r1 = 36; // inner radius (start near center ring)
    const r2 = 88; // outer radius (arrow tip)
    const spread = 28; // angular spread in degrees
    const tipLen = 16;
    const a = (angleDeg * Math.PI) / 180;
    const aLeft = ((angleDeg - spread) * Math.PI) / 180;
    const aRight = ((angleDeg + spread) * Math.PI) / 180;
    const aMidLeft = ((angleDeg - spread * 0.55) * Math.PI) / 180;
    const aMidRight = ((angleDeg + spread * 0.55) * Math.PI) / 180;

    const p1x = Math.cos(aLeft) * r1;
    const p1y = Math.sin(aLeft) * r1;
    const p2x = Math.cos(aMidLeft) * (r2 - tipLen);
    const p2y = Math.sin(aMidLeft) * (r2 - tipLen);
    const p3x = Math.cos(a) * r2; // tip
    const p3y = Math.sin(a) * r2;
    const p4x = Math.cos(aMidRight) * (r2 - tipLen);
    const p4y = Math.sin(aMidRight) * (r2 - tipLen);
    const p5x = Math.cos(aRight) * r1;
    const p5y = Math.sin(aRight) * r1;

    return `M${p1x},${p1y} L${p2x},${p2y} L${p3x},${p3y} L${p4x},${p4y} L${p5x},${p5y} Z`;
  }

  // Small icon circle position (between center and arrow)
  function iconPos(angleDeg: number) {
    const r = 30;
    const a = (angleDeg * Math.PI) / 180;
    return { x: Math.cos(a) * r, y: Math.sin(a) * r };
  }

  return (
    <div className="relative w-full flex items-center justify-center" style={{ height: 220 }}>
      <svg
        viewBox="-160 -115 320 230"
        className="w-full h-full overflow-visible"
        style={{ direction: "ltr" }}
      >
        <defs>
          {data.map((item, i) => (
            <linearGradient
              key={`grad-${i}`}
              id={`arrowGrad${i}`}
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop offset="0%" stopColor={item.fill} stopOpacity={0.9} />
              <stop offset="100%" stopColor={item.fill} stopOpacity={0.6} />
            </linearGradient>
          ))}
          <filter id="arrowShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.3" />
          </filter>
          <filter id="centerGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feFlood floodColor="var(--color-primary)" floodOpacity="0.15" result="color" />
            <feComposite in="color" in2="blur" operator="in" result="glow" />
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Connection arcs between segments */}
        {segments.map((_, i) => {
          const a1 = (-45 + i * 90 + 28) * (Math.PI / 180);
          const a2 = (-45 + (i + 1) * 90 - 28) * (Math.PI / 180);
          const r = 34;
          return (
            <path
              key={`arc-${i}`}
              d={`M${Math.cos(a1) * r},${Math.sin(a1) * r} A${r},${r} 0 0,1 ${Math.cos(a2) * r},${Math.sin(a2) * r}`}
              fill="none"
              stroke="var(--color-border)"
              strokeWidth="1"
              strokeDasharray="3 3"
              opacity={0.4}
            />
          );
        })}

        {/* Arrow segments */}
        {segments.map((seg, i) => {
          const isHovered = hoveredIdx === i;
          const pct = total > 0 ? Math.round((seg.value / total) * 100) : 0;
          const Icon = seg.icon;
          const icp = iconPos(seg.angleDeg);

          return (
            <g
              key={seg.name}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
              style={{ cursor: "pointer" }}
            >
              {/* Arrow shape */}
              <motion.path
                d={arrowPath(seg.angleDeg)}
                fill={`url(#arrowGrad${i})`}
                stroke={isHovered ? "#fff" : seg.fill}
                strokeWidth={isHovered ? 1.5 : 0.5}
                filter="url(#arrowShadow)"
                initial={{ scale: 1, opacity: 0 }}
                animate={{
                  scale: isHovered ? 1.08 : 1,
                  opacity: 1,
                }}
                transition={{ duration: 0.3, delay: i * 0.1 }}
                style={{ transformOrigin: "0px 0px" }}
              />

              {/* Value on the arrow */}
              <text
                x={seg.ax * 0.92}
                y={seg.ay * 0.92}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#fff"
                fontSize="11"
                style={{ textShadow: "0 1px 3px rgba(0,0,0,0.5)" }}
              >
                {seg.value}
              </text>

              {/* Small icon circle at connection to center */}
              <circle
                cx={icp.x}
                cy={icp.y}
                r="9"
                fill="var(--color-card)"
                stroke={seg.fill}
                strokeWidth="1.5"
              />
              {/* Icon rendered as a small shape */}
              <foreignObject
                x={icp.x - 6}
                y={icp.y - 6}
                width="12"
                height="12"
              >
                <div
                  className="flex items-center justify-center w-full h-full"
                  style={{ color: seg.fill }}
                >
                  <Icon size={10} />
                </div>
              </foreignObject>

              {/* Label line + text */}
              <line
                x1={seg.ax * 1.05}
                y1={seg.ay * 1.05}
                x2={seg.lx * 0.85}
                y2={seg.ly * 0.85}
                stroke={seg.fill}
                strokeWidth="1"
                opacity={0.5}
                strokeDasharray="2 2"
              />

              {/* Label badge */}
              <rect
                x={seg.lx * 0.85 - 28}
                y={seg.ly * 0.85 - 12}
                width="56"
                height="24"
                rx="6"
                fill={seg.fill}
                opacity={isHovered ? 0.95 : 0.85}
              />
              <text
                x={seg.lx * 0.85}
                y={seg.ly * 0.85 - 2}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#fff"
                fontSize="9"
                fontFamily="Tajawal, sans-serif"
              >
                {seg.name}
              </text>
              <text
                x={seg.lx * 0.85}
                y={seg.ly * 0.85 + 8}
                textAnchor="middle"
                dominantBaseline="central"
                fill="rgba(255,255,255,0.8)"
                fontSize="7"
                fontFamily="Tajawal, sans-serif"
              >
                {pct}%
              </text>
            </g>
          );
        })}

        {/* Center circle */}
        <circle
          cx="0"
          cy="0"
          r="22"
          fill="var(--color-card)"
          stroke="var(--color-border)"
          strokeWidth="1.5"
          filter="url(#centerGlow)"
        />
        <circle
          cx="0"
          cy="0"
          r="19"
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="0.5"
          opacity="0.4"
        />
        <text
          x="0"
          y="-4"
          textAnchor="middle"
          dominantBaseline="central"
          fill="var(--color-foreground)"
          fontSize="13"
        >
          {total}
        </text>
        <text
          x="0"
          y="8"
          textAnchor="middle"
          dominantBaseline="central"
          fill="var(--color-muted-foreground)"
          fontSize="6"
          fontFamily="Tajawal, sans-serif"
        >
          منتج
        </text>
      </svg>

      {/* Hover tooltip */}
      {hoveredIdx !== null && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-1 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-lg border border-border/40 bg-popover/95 backdrop-blur-sm text-[10px] text-foreground whitespace-nowrap z-10 pointer-events-none"
          style={{ direction: "rtl" }}
        >
          <span style={{ color: data[hoveredIdx].fill }}>●</span>{" "}
          {data[hoveredIdx].name}: {data[hoveredIdx].value} منتج (
          {total > 0 ? Math.round((data[hoveredIdx].value / total) * 100) : 0}%)
        </motion.div>
      )}
    </div>
  );
}
