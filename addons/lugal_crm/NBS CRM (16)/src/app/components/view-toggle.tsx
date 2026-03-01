import { motion } from "motion/react";
import { List, Columns3 } from "lucide-react";

interface ViewToggleProps {
  view: "list" | "kanban";
  onViewChange: (view: "list" | "kanban") => void;
  listLabel?: string;
  kanbanLabel?: string;
  isDark?: boolean;
  iconOnly?: boolean;
}

export function ViewToggle({
  view,
  onViewChange,
  listLabel = "قائمة",
  kanbanLabel = "كانبان",
  isDark = true,
  iconOnly = false,
}: ViewToggleProps) {
  const surface = isDark ? "#1a1a2e" : "#e3edf2";
  const accent = isDark ? "#D4AF37" : "#06B6D4";
  const accentBg = isDark
    ? "linear-gradient(135deg, #D4AF37, #C5A028)"
    : "linear-gradient(135deg, #06B6D4, #0891B2)";
  const outerShadow = isDark
    ? "4px 4px 10px rgba(0,0,0,0.55), -3px -3px 8px rgba(50,50,80,0.25), inset 0 1px 0 rgba(255,255,255,0.03)"
    : "4px 4px 10px rgba(165,180,195,0.4), -3px -3px 8px rgba(255,255,255,0.75), inset 0 1px 0 rgba(255,255,255,0.5)";
  const activeShadow = isDark
    ? "0 2px 10px rgba(212,175,55,0.35), inset 0 1px 0 rgba(255,255,255,0.12)"
    : "0 2px 10px rgba(6,182,212,0.3), inset 0 1px 0 rgba(255,255,255,0.5)";
  const inactiveText = isDark ? "#6B7280" : "#9CA3AF";
  const activeText = "#FFFFFF";

  return (
    <div
      className="relative flex items-center rounded-full p-[3px] gap-0"
      style={{
        background: surface,
        boxShadow: outerShadow,
      }}
    >
      {/* ── List Button ── */}
      <motion.button
        onClick={() => onViewChange("list")}
        whileHover={{ scale: view === "list" ? 1 : 1.03 }}
        whileTap={{ scale: 0.97 }}
        className={`relative z-10 flex items-center justify-center rounded-full cursor-pointer outline-none transition-colors duration-200 ${iconOnly ? "w-7 h-7" : "gap-1.5 px-3.5 py-1.5"}`}
        style={{
          background: view === "list" ? accentBg : "transparent",
          boxShadow: view === "list" ? activeShadow : "none",
          color: view === "list" ? activeText : inactiveText,
        }}
        title={listLabel}
      >
        <List className="w-3.5 h-3.5" />
        {!iconOnly && <span className="text-xs whitespace-nowrap">{listLabel}</span>}
      </motion.button>

      {/* ── Kanban Button ── */}
      <motion.button
        onClick={() => onViewChange("kanban")}
        whileHover={{ scale: view === "kanban" ? 1 : 1.03 }}
        whileTap={{ scale: 0.97 }}
        className={`relative z-10 flex items-center justify-center rounded-full cursor-pointer outline-none transition-colors duration-200 ${iconOnly ? "w-7 h-7" : "gap-1.5 px-3.5 py-1.5"}`}
        style={{
          background: view === "kanban" ? accentBg : "transparent",
          boxShadow: view === "kanban" ? activeShadow : "none",
          color: view === "kanban" ? activeText : inactiveText,
        }}
        title={kanbanLabel}
      >
        <Columns3 className="w-3.5 h-3.5" />
        {!iconOnly && <span className="text-xs whitespace-nowrap">{kanbanLabel}</span>}
      </motion.button>
    </div>
  );
}