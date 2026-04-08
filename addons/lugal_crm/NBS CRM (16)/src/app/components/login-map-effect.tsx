import { useMemo } from "react";
import { motion } from "motion/react";
import {
  Home,
  Users,
  Package,
  ShoppingBag,
  MessageSquareDot,
  Ticket,
  UserCog,
  Target,
  TrendingUp,
  Container,
  Megaphone,
  BarChart3,
  BookMarked,
  Headset,
  Eye,
  ScrollText,
  ShieldCheck,
  Settings,
} from "lucide-react";

interface LoginMapEffectProps {
  isDark?: boolean;
}

const crmSections = [
  { id: "dashboard", label: "لوحة التحكم", icon: Home },
  { id: "customers", label: "العملاء", icon: Users },
  { id: "products", label: "المنتجات", icon: Package },
  { id: "orders", label: "الطلبات", icon: ShoppingBag },
  { id: "omni-channel", label: "القنوات الموحدة", icon: MessageSquareDot },
  { id: "tickets", label: "التذاكر", icon: Ticket },
  { id: "agents", label: "الموظفون", icon: UserCog },
  { id: "sales-pipeline", label: "خط المبيعات", icon: Target },
  { id: "forecasting", label: "التنبؤات", icon: TrendingUp },
  { id: "supply-chain", label: "سلسلة التوريد", icon: Container },
  { id: "promotions", label: "مركز العروض", icon: Megaphone },
  { id: "analytics", label: "التحليلات", icon: BarChart3 },
  { id: "knowledge-base", label: "قاعدة المعرفة", icon: BookMarked },
  { id: "call-centre", label: "مركز الاتصال", icon: Headset },
  { id: "supervisor", label: "لوحة المشرف", icon: Eye },
  { id: "event-log", label: "سجل الأحداث", icon: ScrollText },
  { id: "admin-dashboard", label: "لوحة المشرف", icon: ShieldCheck },
  { id: "settings", label: "الإعدادات", icon: Settings },
];

export function LoginMapEffect({ isDark = true }: LoginMapEffectProps) {
  const accent = isDark ? "212,175,55" : "6,182,212";
  const accentHex = isDark ? "#D4AF37" : "#06B6D4";

  const surface = isDark ? "#1a1a2e" : "#e3edf2";
  const surfaceCard = isDark ? "rgba(26,26,46,0.85)" : "rgba(227,237,242,0.85)";
  const shadowDark = isDark ? "rgba(0,0,0,0.5)" : "rgba(165,180,195,0.4)";
  const shadowLight = isDark ? "rgba(50,50,80,0.3)" : "rgba(255,255,255,0.8)";
  const textColor = isDark ? "rgba(232,232,240,0.9)" : "rgba(45,55,72,0.9)";
  const textSub = isDark ? "rgba(136,136,168,0.7)" : "rgba(113,128,150,0.7)";
  const pageBg = isDark
    ? "radial-gradient(ellipse at 50% 80%, rgba(15,12,25,1) 0%, rgba(6,8,15,1) 100%)"
    : "radial-gradient(ellipse at 50% 80%, rgba(220,248,255,1) 0%, rgba(232,244,248,1) 100%)";

  /* Split 18 items into inner ring (8) and outer ring (10) */
  const innerItems = useMemo(() => crmSections.slice(0, 8), []);
  const outerItems = useMemo(() => crmSections.slice(8), []);

  return (
    <div
      className="absolute inset-0 w-full h-full overflow-hidden"
      style={{ background: pageBg }}
      dir="rtl"
    >
      {/* Ambient glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 50% 50%, rgba(${accent},0.08) 0%, transparent 60%)`,
        }}
      />

      {/* ═══ Floating Particles Background ═══ */}
      {Array.from({ length: 20 }).map((_, i) => (
        <motion.div
          key={`p-${i}`}
          className="absolute rounded-full"
          style={{
            width: 2 + (i % 3),
            height: 2 + (i % 3),
            insetInlineStart: `${10 + (i * 4.2) % 80}%`,
            top: `${5 + (i * 5.3) % 90}%`,
            background: `rgba(${accent},${0.15 + (i % 4) * 0.08})`,
          }}
          animate={{
            y: [0, -30 - (i % 3) * 10, 0],
            opacity: [0.2, 0.7, 0.2],
            scale: [0.5, 1.2, 0.5],
          }}
          transition={{
            duration: 6 + (i % 5) * 2,
            delay: (i % 7) * 0.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}

      {/* ═══ Central Rotating Rings ═══ */}
      <div className="absolute inset-0 flex items-center justify-center">
        {/* Outer ring — rotates slowly clockwise */}
        <motion.div
          className="absolute"
          style={{ width: 520, height: 520 }}
          animate={{ rotate: 360 }}
          transition={{ duration: 90, repeat: Infinity, ease: "linear" }}
        >
          {outerItems.map((item, i) => {
            const angle = (i / outerItems.length) * 360;
            const rad = (angle * Math.PI) / 180;
            const rx = 240;
            const ry = 240;
            const x = rx * Math.cos(rad);
            const y = ry * Math.sin(rad);
            const Icon = item.icon;

            return (
              <motion.div
                key={item.id}
                className="absolute flex flex-col items-center gap-1.5"
                style={{
                  insetInlineStart: `calc(50% + ${x}px - 36px)`,
                  top: `calc(50% + ${y}px - 36px)`,
                  width: 72,
                }}
                animate={{ rotate: -360 }}
                transition={{ duration: 90, repeat: Infinity, ease: "linear" }}
              >
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center backdrop-blur-sm"
                  style={{
                    background: surfaceCard,
                    boxShadow: `4px 4px 12px ${shadowDark}, -4px -4px 12px ${shadowLight}, inset 0 0 12px rgba(${accent},0.05)`,
                    border: `1px solid rgba(${accent},0.1)`,
                  }}
                >
                  <Icon
                    className="w-5.5 h-5.5"
                    style={{ color: accentHex }}
                    strokeWidth={1.8}
                  />
                </div>
                <span
                  className="text-[9px] text-center whitespace-nowrap"
                  style={{ color: textSub }}
                >
                  {item.label}
                </span>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Inner ring — rotates slowly counter-clockwise */}
        <motion.div
          className="absolute"
          style={{ width: 320, height: 320 }}
          animate={{ rotate: -360 }}
          transition={{ duration: 70, repeat: Infinity, ease: "linear" }}
        >
          {innerItems.map((item, i) => {
            const angle = (i / innerItems.length) * 360;
            const rad = (angle * Math.PI) / 180;
            const rx = 140;
            const ry = 140;
            const x = rx * Math.cos(rad);
            const y = ry * Math.sin(rad);
            const Icon = item.icon;

            return (
              <motion.div
                key={item.id}
                className="absolute flex flex-col items-center gap-1"
                style={{
                  insetInlineStart: `calc(50% + ${x}px - 32px)`,
                  top: `calc(50% + ${y}px - 32px)`,
                  width: 64,
                }}
                animate={{ rotate: 360 }}
                transition={{ duration: 70, repeat: Infinity, ease: "linear" }}
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center backdrop-blur-sm"
                  style={{
                    background: surfaceCard,
                    boxShadow: `3px 3px 8px ${shadowDark}, -3px -3px 8px ${shadowLight}, inset 0 0 8px rgba(${accent},0.06)`,
                    border: `1px solid rgba(${accent},0.12)`,
                  }}
                >
                  <Icon
                    className="w-5 h-5"
                    style={{ color: accentHex }}
                    strokeWidth={1.8}
                  />
                </div>
                <span
                  className="text-[8px] text-center whitespace-nowrap"
                  style={{ color: textSub }}
                >
                  {item.label}
                </span>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Center glowing orb */}
        <motion.div
          className="relative z-10"
          animate={{ scale: [1, 1.08, 1] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        >
          <div
            className="w-20 h-20 rounded-full flex items-center justify-center"
            style={{
              background: surface,
              boxShadow: `8px 8px 24px ${shadowDark}, -8px -8px 24px ${shadowLight}, 0 0 40px rgba(${accent},0.15), inset 0 0 20px rgba(${accent},0.05)`,
              border: `2px solid rgba(${accent},0.2)`,
            }}
          >
            <span
              className="text-[11px] text-center"
              style={{
                color: textColor,
                lineHeight: "1.3",
              }}
            >
              نور
              <br />
              النبراس
            </span>
          </div>
        </motion.div>

        {/* Decorative ring lines */}
        <div
          className="absolute rounded-full pointer-events-none"
          style={{
            width: 290,
            height: 290,
            border: `1px dashed rgba(${accent},0.08)`,
          }}
        />
        <div
          className="absolute rounded-full pointer-events-none"
          style={{
            width: 490,
            height: 490,
            border: `1px dashed rgba(${accent},0.06)`,
          }}
        />
      </div>
    </div>
  );
}