import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Eye,
  EyeOff,
  Lock,
  User,
  Globe,
  Sparkles,
  ShieldCheck,
  ArrowLeft,
  Sun,
  Moon,
  Fingerprint,
} from "lucide-react";
import { LoginMapEffect } from "./login-map-effect";

interface LoginPageProps {
  /** Called with credentials; resolves true on success */
  onLogin:       ((username: string, password: string) => Promise<boolean>) | (() => void);
  colorTheme?:   "dark-gold" | "light-turquoise";
  onToggleTheme?:() => void;
  /** External loading state (from API call) */
  isLoading?:    boolean;
  /** External error message from API */
  error?:        string | null;
}

export function LoginPage({ onLogin, colorTheme = "dark-gold", onToggleTheme, isLoading: externalLoading, error: externalError }: LoginPageProps) {
  const isDark = colorTheme === "dark-gold";
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const displayError = externalError ?? localError;
  const [particles, setParticles] = useState<
    { id: number; x: number; y: number; size: number; delay: number; duration: number }[]
  >([]);

  /* ── Neumorphic theme tokens ── */
  const n = isDark
    ? {
        // Dark neumorphic
        surface: "#1a1a2e",
        surfaceLight: "#22223a",
        surfaceDark: "#10101e",
        shadowLight: "rgba(50,50,80,0.35)",
        shadowDark: "rgba(0,0,0,0.65)",
        insetLight: "rgba(50,50,80,0.25)",
        insetDark: "rgba(0,0,0,0.5)",
        accent: "#D4AF37",
        accentRgb: "212,175,55",
        accentGrad: "linear-gradient(135deg, #BF953F, #D4AF37, #C6A832)",
        accentGradHover: "linear-gradient(135deg, #FCF6BA, #D4AF37, #FBF5B7)",
        accentLight: "#F5E6B8",
        text: "#E8E8F0",
        textMuted: "#8888A8",
        textSubtle: "#5A5A78",
        inputText: "#D0D0E0",
        pageBg: "#12121e",
        cardGlow: "rgba(212,175,55,0.08)",
        neonShadow: "rgba(212,175,55,",
        titleGrad: "linear-gradient(to left, #BF953F, #FCF6BA, #B38728, #FBF5B7, #AA771C)",
        btnText: "rgba(0,0,0,0.9)",
      }
    : {
        // Light neumorphic (matching reference image)
        surface: "#e3edf2",
        surfaceLight: "#ffffff",
        surfaceDark: "#c8d5dc",
        shadowLight: "rgba(255,255,255,0.85)",
        shadowDark: "rgba(165,180,195,0.45)",
        insetLight: "rgba(255,255,255,0.7)",
        insetDark: "rgba(165,180,195,0.3)",
        accent: "#06B6D4",
        accentRgb: "6,182,212",
        accentGrad: "linear-gradient(135deg, #06B6D4, #0891B2, #0E7490)",
        accentGradHover: "linear-gradient(135deg, #67E8F9, #06B6D4, #22D3EE)",
        accentLight: "#B2F0FC",
        text: "#2D3748",
        textMuted: "#718096",
        textSubtle: "#A0AEC0",
        inputText: "#4A5568",
        pageBg: "#e8f0f4",
        cardGlow: "rgba(6,182,212,0.06)",
        neonShadow: "rgba(6,182,212,",
        titleGrad: "linear-gradient(to left, #06B6D4, #22D3EE, #0891B2, #67E8F9, #0E7490)",
        btnText: "#FFFFFF",
      };

  /* ── Neumorphic shadow helpers ── */
  const neuOuter = `8px 8px 20px ${n.shadowDark}, -8px -8px 20px ${n.shadowLight}`;
  const neuOuterSm = `4px 4px 10px ${n.shadowDark}, -4px -4px 10px ${n.shadowLight}`;
  const neuInset = `inset 3px 3px 8px ${n.insetDark}, inset -3px -3px 8px ${n.insetLight}`;
  const neuPressed = `inset 2px 2px 6px ${n.insetDark}, inset -2px -2px 6px ${n.insetLight}`;

  useEffect(() => {
    const pts = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 2 + 0.5,
      delay: Math.random() * 6,
      duration: Math.random() * 10 + 8,
    }));
    setParticles(pts);
  }, []);

  /** Submit credentials — calls real API via onLogin prop */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setLocalError(null);
      if (!username.trim() || !password.trim()) {
        setLocalError('يرجى إدخال اسم المستخدم وكلمة المرور');
        return;
      }
      setIsLoading(true);
      try {
        const fn = onLogin as (u: string, p: string) => Promise<boolean>;
        if (fn.length >= 2) {
          await fn(username, password);
        } else {
          (onLogin as () => void)();
        }
      } catch {
        setLocalError('حدث خطأ أثناء تسجيل الدخول');
      } finally {
        setIsLoading(false);
      }
    },
    [onLogin, username, password],
  );

  return (
    <div
      className="min-h-screen w-full flex relative overflow-hidden"
      dir="rtl"
      style={{ background: n.pageBg }}
    >
      {/* ── Theme Toggle ── */}
      {onToggleTheme && (
        <div className="absolute top-5 start-5 z-50" dir="ltr">
          <motion.button
            onClick={onToggleTheme}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
            className="relative w-14 h-7 rounded-full cursor-pointer outline-none"
            title={isDark ? "الوضع النهاري" : "الوضع الليلي"}
            style={{
              background: n.surface,
              boxShadow: neuOuterSm,
            }}
          >
            <span className="absolute inset-0 flex items-center justify-between px-1.5 pointer-events-none">
              <Moon
                className="w-3 h-3 transition-all"
                style={{ color: isDark ? n.accent : n.textSubtle }}
              />
              <Sun
                className="w-3 h-3 transition-all"
                style={{ color: !isDark ? n.accent : n.textSubtle }}
              />
            </span>
            <motion.span
              layout
              transition={{ type: "spring", stiffness: 500, damping: 35 }}
              className="absolute top-[3px] w-[22px] h-[22px] rounded-full flex items-center justify-center"
              style={{
                left: isDark ? "3px" : "calc(100% - 25px)",
                background: n.surface,
                boxShadow: neuOuterSm,
              }}
            >
              {isDark ? (
                <Moon className="w-2.5 h-2.5" style={{ color: n.accent }} />
              ) : (
                <Sun className="w-2.5 h-2.5" style={{ color: n.accent }} />
              )}
            </motion.span>
          </motion.button>
        </div>
      )}

      {/* ── Ambient particles ── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {particles.map((p) => (
          <motion.div
            key={p.id}
            className="absolute rounded-full"
            style={{
              width: p.size,
              height: p.size,
              left: `${p.x}%`,
              top: `${p.y}%`,
              background: `radial-gradient(circle, rgba(${n.accentRgb},${p.id % 3 === 0 ? 0.6 : 0.3}), transparent)`,
            }}
            animate={{ y: [0, -50, 0], opacity: [0, 0.8, 0], scale: [0.3, 1, 0.3] }}
            transition={{ duration: p.duration, delay: p.delay, repeat: Infinity, ease: "easeInOut" }}
          />
        ))}
      </div>

      {/* ═══════════════════════════════════════════════ */}
      {/* ═══════ LEFT SIDE: Creative Effect  ═══════ */}
      {/* ═══════════════════════════════════════════════ */}
      <div className="hidden lg:flex flex-1 relative overflow-hidden">
        <LoginMapEffect isDark={isDark} />

        {/* Top fade */}
        <div
          className="absolute top-0 inset-x-0 h-32 pointer-events-none z-10"
          style={{ backgroundImage: `linear-gradient(to bottom, ${n.pageBg}, transparent)` }}
        />
        {/* Bottom fade */}
        <div
          className="absolute bottom-0 inset-x-0 h-24 pointer-events-none z-10"
          style={{ backgroundImage: `linear-gradient(to top, ${n.pageBg}, transparent)` }}
        />

        {/* ── Brand title (top) ── */}
        <div className="absolute top-0 inset-x-0 z-20 flex flex-col items-center pt-10">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1, duration: 1.2 }}
            className="text-4xl relative"
            style={{
              fontFamily: "Tajawal, sans-serif",
              color: isDark ? "#FFFFFF" : "#0F172A",
              textShadow: `0 0 10px ${n.neonShadow}0.9), 0 0 30px ${n.neonShadow}0.6), 0 0 60px ${n.neonShadow}0.35), 0 0 100px ${n.neonShadow}0.2)`,
              letterSpacing: "0.12em",
              WebkitTextStroke: isDark ? "0.5px rgba(255,255,255,0.3)" : "none",
            }}
          >
            <motion.span
              animate={{
                textShadow: [
                  `0 0 10px ${n.neonShadow}0.9), 0 0 30px ${n.neonShadow}0.6), 0 0 60px ${n.neonShadow}0.35)`,
                  `0 0 18px ${n.neonShadow}1), 0 0 50px ${n.neonShadow}0.8), 0 0 100px ${n.neonShadow}0.5)`,
                  `0 0 8px ${n.neonShadow}0.7), 0 0 22px ${n.neonShadow}0.45), 0 0 50px ${n.neonShadow}0.25)`,
                  `0 0 10px ${n.neonShadow}0.9), 0 0 30px ${n.neonShadow}0.6), 0 0 60px ${n.neonShadow}0.35)`,
                ],
              }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              عائلة نور النبراس
            </motion.span>
          </motion.h2>

          <motion.div
            className="mt-3 h-px"
            initial={{ width: 0 }}
            animate={{ width: 260 }}
            transition={{ delay: 1.8, duration: 1.5 }}
            style={{
              backgroundImage: `linear-gradient(90deg, transparent, ${n.accent}, transparent)`,
              boxShadow: `0 0 12px ${n.neonShadow}0.4)`,
            }}
          />
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.3, duration: 1 }}
            className="mt-3 text-sm"
            style={{ color: n.textMuted, textShadow: `0 0 8px ${n.neonShadow}0.1)` }}
          >
            من العراق إلى العالم
          </motion.p>
        </div>

        {/* Bottom info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.8, duration: 1 }}
          className="absolute bottom-7 inset-x-0 z-20 flex items-center justify-center gap-4"
        >
          <div className="flex items-center gap-1.5" style={{ color: n.textMuted }}>
            <Globe className="w-3.5 h-3.5" />
            <span className="text-xs">4 فروع</span>
          </div>
          <span style={{ color: n.textSubtle }}>|</span>
          <div className="flex items-center gap-1.5" style={{ color: n.textMuted }}>
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="text-xs">مشفّر بالكامل</span>
          </div>
        </motion.div>
      </div>

      {/* ═══════════════════════════════════════════════ */}
      {/* ═══════ RIGHT SIDE: Neumorphic Login ═══════ */}
      {/* ═══════════════════════════════════════════════ */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 relative">
        {/* Separator line */}
        <div
          className="hidden lg:block absolute start-0 top-[10%] bottom-[10%] w-px"
          style={{ background: `linear-gradient(to bottom, transparent, rgba(${n.accentRgb},0.12), transparent)` }}
        />

        <motion.div
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 }}
          className="w-full max-w-md"
        >
          {/* ── Logo & Brand ── */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="text-center mb-10"
          >
            {/* Neumorphic logo circle */}
            <div className="relative inline-flex items-center justify-center mb-6">
              <motion.div
                className="absolute w-24 h-24 rounded-full"
                style={{ background: n.surface, boxShadow: neuOuter }}
                animate={{ rotate: 360 }}
                transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
              />
              <motion.div
                className="absolute w-28 h-28 rounded-full"
                style={{ border: `1px dashed rgba(${n.accentRgb},0.12)` }}
                animate={{ rotate: -360 }}
                transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
              />
              <div
                className="relative w-16 h-16 rounded-full flex items-center justify-center"
                style={{
                  background: n.surface,
                  boxShadow: `${neuOuter}, inset 0 0 20px rgba(${n.accentRgb},0.05)`,
                }}
              >
                <Sparkles className="w-7 h-7" style={{ color: n.accent }} />
              </div>
            </div>

            <h1
              className="text-3xl mb-2"
              style={{
                backgroundImage: n.titleGrad,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              نور النبراس
            </h1>
            <p className="text-sm" style={{ color: n.textMuted }}>
              نظام إدارة علاقات العملاء
            </p>
          </motion.div>

          {/* ═══ Neumorphic Login Card ═══ */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6 }}
            className="rounded-3xl p-8"
            style={{
              background: n.surface,
              boxShadow: `12px 12px 30px ${n.shadowDark}, -12px -12px 30px ${n.shadowLight}, 0 0 60px ${n.cardGlow}`,
            }}
          >
            {/* Card header */}
            <h2 className="text-lg mb-1" style={{ color: n.text }}>تسجيل الدخول</h2>
            <p className="text-sm mb-8" style={{ color: n.textSubtle }}>
              أدخل بياناتك للوصول إلى لوحة التحكم
            </p>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* ── Username input (neumorphic inset) ── */}
              <div className="space-y-2">
                <label className="text-sm ps-1" style={{ color: n.textMuted }}>
                  اسم المستخدم
                </label>
                <div
                  className="relative flex items-center h-13 rounded-2xl transition-all duration-400"
                  style={{
                    background: n.surface,
                    boxShadow: focusedField === "username"
                      ? `${neuInset}, 0 0 0 2px rgba(${n.accentRgb},0.2)`
                      : neuInset,
                  }}
                >
                  {/* Icon circle */}
                  <span
                    className="flex items-center justify-center w-9 h-9 rounded-xl ms-2 transition-all duration-300"
                    style={{
                      background: n.surface,
                      boxShadow: focusedField === "username" ? neuOuterSm : "none",
                      color: focusedField === "username" ? n.accent : n.textSubtle,
                    }}
                  >
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    onFocus={() => setFocusedField("username")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="أدخل اسم المستخدم"
                    className="flex-1 h-full bg-transparent text-sm outline-none px-3"
                    style={{ color: n.inputText }}
                  />
                </div>
              </div>

              {/* ── Password input (neumorphic inset) ── */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm ps-1" style={{ color: n.textMuted }}>
                    كلمة المرور
                  </label>
                  <button
                    type="button"
                    className="text-xs transition-colors"
                    style={{ color: n.textSubtle }}
                  >
                    نسيت كلمة المرور؟
                  </button>
                </div>
                <div
                  className="relative flex items-center h-13 rounded-2xl transition-all duration-400"
                  style={{
                    background: n.surface,
                    boxShadow: focusedField === "password"
                      ? `${neuInset}, 0 0 0 2px rgba(${n.accentRgb},0.2)`
                      : neuInset,
                  }}
                >
                  <span
                    className="flex items-center justify-center w-9 h-9 rounded-xl ms-2 transition-all duration-300"
                    style={{
                      background: n.surface,
                      boxShadow: focusedField === "password" ? neuOuterSm : "none",
                      color: focusedField === "password" ? n.accent : n.textSubtle,
                    }}
                  >
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocusedField("password")}
                    onBlur={() => setFocusedField(null)}
                    placeholder="أدخل كلمة المرور"
                    className="flex-1 h-full bg-transparent text-sm outline-none px-3"
                    style={{ color: n.inputText }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="flex items-center justify-center w-9 h-9 rounded-xl me-2 cursor-pointer transition-all duration-300"
                    style={{
                      background: n.surface,
                      boxShadow: neuOuterSm,
                      color: n.textSubtle,
                    }}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* ── Remember me (neumorphic toggle) ── */}
              <div className="flex items-center gap-3">
                <div className="relative">
                  <input
                    type="checkbox"
                    id="remember"
                    className="peer sr-only"
                  />
                  <label
                    htmlFor="remember"
                    className="block w-5 h-5 rounded-lg cursor-pointer transition-all duration-300 peer-checked:bg-transparent"
                    style={{
                      background: n.surface,
                      boxShadow: neuPressed,
                    }}
                  />
                  <svg
                    className="absolute top-0.5 start-0.5 w-4 h-4 opacity-0 peer-checked:opacity-100 pointer-events-none transition-opacity duration-300"
                    style={{ color: n.accent }}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <label htmlFor="remember" className="text-sm cursor-pointer select-none" style={{ color: n.textMuted }}>
                  تذكرني
                </label>
              </div>

              {/* ── API error message ── */}
              {displayError && (
                <div
                  className="text-sm text-center px-4 py-2.5 rounded-xl"
                  style={{ background: "rgba(239,68,68,0.1)", color: "#f87171", border: "1px solid rgba(239,68,68,0.2)" }}
                >
                  {displayError}
                </div>
              )}

              {/* ── Login Button (neumorphic raised, gradient) ── */}
              <motion.button
                type="submit"
                disabled={isLoading || !!externalLoading}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                className="relative w-full h-13 rounded-2xl text-sm overflow-hidden transition-all duration-500 group/btn disabled:opacity-70 cursor-pointer"
                style={{
                  background: n.accentGrad,
                  boxShadow: `6px 6px 16px ${n.shadowDark}, -3px -3px 12px ${n.shadowLight}, 0 4px 20px rgba(${n.accentRgb},0.3)`,
                }}
              >
                <div
                  className="absolute inset-0 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-500 rounded-2xl"
                  style={{
                    background: n.surface,
                    boxShadow: `inset 3px 3px 6px ${n.shadowDark}, inset -3px -3px 6px ${n.shadowLight}`,
                  }}
                />
                <div className="relative flex items-center justify-center gap-2">
                  <AnimatePresence mode="wait">
                    {isLoading ? (
                      <motion.div
                        key="loading"
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.5 }}
                        className="flex items-center gap-3"
                      >
                        <div
                          className="w-5 h-5 border-2 rounded-full animate-spin"
                          style={{
                            borderColor: `rgba(${isDark ? "0,0,0" : "255,255,255"},0.2)`,
                            borderTopColor: isDark ? "rgba(0,0,0,0.8)" : "rgba(255,255,255,0.9)",
                          }}
                        />
                        <span style={{ color: n.btnText }}>جارِ الدخول...</span>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="text"
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.5 }}
                        className="flex items-center gap-2"
                      >
                        <ArrowLeft className="w-4 h-4" style={{ color: `${n.btnText}cc` }} />
                        <span style={{ color: n.btnText }}>دخول إلى النظام</span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.button>
            </form>

            {/* ── Divider ── */}
            <div className="flex items-center gap-4 my-6">
              <div className="flex-1 h-px" style={{ background: `linear-gradient(to left, rgba(${n.accentRgb},0.1), transparent)` }} />
              <span className="text-[10px]" style={{ color: n.textSubtle }}>أو</span>
              <div className="flex-1 h-px" style={{ background: `linear-gradient(to right, rgba(${n.accentRgb},0.1), transparent)` }} />
            </div>

            {/* ── Biometric (neumorphic button) ── */}
            <button
              className="w-full h-12 rounded-2xl text-sm flex items-center justify-center gap-2 cursor-pointer transition-all duration-300"
              style={{
                color: n.textMuted,
                background: n.surface,
                boxShadow: neuOuterSm,
              }}
            >
              <Fingerprint className="w-4.5 h-4.5" />
              الدخول ببصمة الإصبع
            </button>
          </motion.div>

          {/* ── Footer ── */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.6 }}
            className="text-center mt-8"
          >
            <p className="text-xs" style={{ color: n.textSubtle }}>
              نور النبراس للعطور &copy; 2026 — جميع الحقوق محفوظة
            </p>
            <p className="text-[10px] mt-1" dir="ltr" style={{ color: isDark ? "rgba(90,90,120,0.5)" : "rgba(160,174,192,0.6)" }}>
              <span dir="ltr">v2.4.0</span> &bull; Powered by Noor Al-Nibras CRM
            </p>
          </motion.div>
        </motion.div>
      </div>

      {/* ── Mobile: subtle accent glow at top ── */}
      <div className="lg:hidden absolute top-0 left-0 right-0 h-40 pointer-events-none overflow-hidden">
        <div
          className="absolute top-[-60%] left-1/2 -translate-x-1/2 w-[300px] h-[300px] rounded-full"
          style={{
            background: `radial-gradient(circle, rgba(${n.accentRgb},0.06) 0%, transparent 70%)`,
            filter: "blur(30px)",
          }}
        />
      </div>
    </div>
  );
}