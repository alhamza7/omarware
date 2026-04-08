import { useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Checkbox } from "./ui/checkbox";
import { ScrollArea } from "./ui/scroll-area";
import {
  Settings2,
  Table2,
  Rows3,
  FileText,
  Palette,
  ImageIcon,
  Upload,
  X,
  RotateCcw,
  GripVertical,
  Eye,
  EyeOff,
  ChevronUp,
  ChevronDown,
  Check,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────
export interface ColumnVisibility {
  key: string;
  label: string;
  visible: boolean;
  active: boolean;
}

export interface FormSettings {
  columnVisibility: ColumnVisibility[];
  bgMode: "solid" | "image";
  bgColor: string;
  bgTextColor: string;
  bgImage: string | null;
  bgOpacity: number;
}

interface FormSettingsDialogProps {
  open: boolean;
  onClose: () => void;
  settings: FormSettings;
  onApply: (settings: FormSettings) => void;
}

// ─── Background color palettes with text colors ─────────
// Each color has a carefully chosen text color for maximum readability
interface BgColorOption {
  id: string;
  color: string;
  label: string;
  textColor: string; // explicit hex for text
  category: string;
}

const BG_COLORS_DARK: BgColorOption[] = [
  // ── أساسيات ──
  { id: "default", color: "transparent", label: "افتراضي", textColor: "", category: "أساسيات" },
  { id: "pure-black", color: "#000000", label: "أسود نقي", textColor: "#E0E0E0", category: "أساسيات" },
  { id: "charcoal", color: "#1C1C1C", label: "فحمي", textColor: "#E8E8E8", category: "أساسيات" },
  { id: "dark-gray", color: "#2D2D2D", label: "رمادي داكن", textColor: "#F0F0F0", category: "أساسيات" },

  // ── أزرق وكحلي ──
  { id: "deep-navy", color: "#0D1B2A", label: "كحلي عميق", textColor: "#B8D4E8", category: "أزرق وكحلي" },
  { id: "navy-blue", color: "#1B2838", label: "أزرق بحري", textColor: "#A8CCE0", category: "أزرق وكحلي" },
  { id: "royal-blue", color: "#1A237E", label: "أزرق ملكي", textColor: "#B8C8F0", category: "أزرق وكحلي" },
  { id: "midnight-blue", color: "#191970", label: "منتصف الليل", textColor: "#C8D8FF", category: "أزرق وكحلي" },

  // ── أخضر وزمردي ──
  { id: "dark-emerald", color: "#064E3B", label: "زمردي غامق", textColor: "#A7F3D0", category: "أخضر وزمردي" },
  { id: "forest-green", color: "#1B4332", label: "أخضر غابة", textColor: "#B0E8C8", category: "أخضر وزمردي" },
  { id: "dark-teal", color: "#134E4A", label: "أخضر بترولي", textColor: "#99F6E4", category: "أخضر وزمردي" },
  { id: "deep-cyan", color: "#164E63", label: "سماوي عميق", textColor: "#A5F3FC", category: "أخضر وزمردي" },

  // ── أحمر ونبيذي ──
  { id: "dark-wine", color: "#4A0E2E", label: "نبيذي", textColor: "#F8B4D0", category: "أحمر ونبيذي" },
  { id: "burgundy", color: "#5B1A30", label: "بورغندي", textColor: "#F8C4D8", category: "أحمر ونبيذي" },
  { id: "dark-maroon", color: "#3B0D0D", label: "كستنائي", textColor: "#F0B8B8", category: "أحمر ونبيذي" },
  { id: "dark-rose", color: "#881337", label: "وردي داكن", textColor: "#FFC8D8", category: "أحمر ونبيذي" },

  // ── ذهبي وبني ──
  { id: "dark-gold", color: "#2A2410", label: "ذهبي داكن", textColor: "#F0DCA0", category: "ذهبي وبني" },
  { id: "coffee", color: "#3E2723", label: "بني قهوة", textColor: "#E8C8A0", category: "ذهبي وبني" },
  { id: "chocolate", color: "#4A3728", label: "شوكولا", textColor: "#F0D8B8", category: "ذهبي وبني" },
  { id: "bronze", color: "#3D2B1F", label: "برونزي", textColor: "#E8D0B0", category: "ذهبي وبني" },

  // ── بنفسجي ──
  { id: "deep-purple", color: "#311B92", label: "بنفسجي عميق", textColor: "#D1C4E9", category: "بنفسجي" },
  { id: "dark-plum", color: "#2D0A4E", label: "خوخي غامق", textColor: "#D8B4F0", category: "بنفسجي" },
  { id: "dark-indigo", color: "#1A0A3E", label: "نيلي", textColor: "#C8B0F0", category: "بنفسجي" },
  { id: "dark-violet", color: "#4A148C", label: "بنفسجي", textColor: "#E0C8FF", category: "بنفسجي" },
];

const BG_COLORS_LIGHT: BgColorOption[] = [
  // ── أساسيات ──
  { id: "default", color: "transparent", label: "افتراضي", textColor: "", category: "أساسيات" },
  { id: "white", color: "#FFFFFF", label: "أبيض نقي", textColor: "#1A1A2E", category: "أساسيات" },
  { id: "soft-gray", color: "#F1F5F9", label: "رمادي ناعم", textColor: "#1E293B", category: "أساسيات" },
  { id: "warm-white", color: "#FEFCE8", label: "أبيض دافئ", textColor: "#422006", category: "أساسيات" },

  // ── أزرق وسماوي ──
  { id: "soft-blue", color: "#DBEAFE", label: "أزرق فاتح", textColor: "#1E3A5F", category: "أزرق وسماوي" },
  { id: "sky-blue", color: "#E0F2FE", label: "سماوي صافي", textColor: "#0C4A6E", category: "أزرق وسماوي" },
  { id: "soft-cyan", color: "#CFFAFE", label: "سماوي فاتح", textColor: "#164E63", category: "أزرق وسماوي" },
  { id: "ice-blue", color: "#E8F4FD", label: "أزرق ثلجي", textColor: "#1E3A5F", category: "أزرق وسماوي" },

  // ── أخضر ونعناعي ──
  { id: "soft-mint", color: "#D1FAE5", label: "نعناعي", textColor: "#064E3B", category: "أخضر ونعناعي" },
  { id: "soft-emerald", color: "#DCFCE7", label: "زمردي فاتح", textColor: "#14532D", category: "أخضر ونعناعي" },
  { id: "sage", color: "#E8F0E4", label: "أخضر مريمية", textColor: "#2D4A2D", category: "أخضر ونعناعي" },
  { id: "soft-teal", color: "#CCFBF1", label: "بترولي فاتح", textColor: "#134E4A", category: "أخضر ونعناعي" },

  // ── وردي ودافئ ──
  { id: "soft-rose", color: "#FFE4E6", label: "وردي ناعم", textColor: "#881337", category: "وردي ودافئ" },
  { id: "soft-pink", color: "#FCE7F3", label: "زهري فاتح", textColor: "#831843", category: "وردي ودافئ" },
  { id: "peach", color: "#FFF0DB", label: "خوخي فاتح", textColor: "#78350F", category: "وردي ودافئ" },
  { id: "coral-blush", color: "#FEE2E2", label: "مرجاني", textColor: "#7F1D1D", category: "وردي ودافئ" },

  // ── كريمي ودافئ ──
  { id: "cream", color: "#FEF9C3", label: "كريمي", textColor: "#713F12", category: "كريمي ودافئ" },
  { id: "sand", color: "#FEF3C7", label: "رملي", textColor: "#78350F", category: "كريمي ودافئ" },
  { id: "champagne", color: "#FDF6E3", label: "شامبانيا", textColor: "#451A03", category: "كريمي ودافئ" },
  { id: "ivory", color: "#FFFFF0", label: "عاجي", textColor: "#3D3D00", category: "كريمي ودافئ" },

  // ── بنفسجي ──
  { id: "lavender", color: "#EDE9FE", label: "لافندر", textColor: "#4C1D95", category: "بنفسجي" },
  { id: "soft-purple", color: "#F3E8FF", label: "بنفسجي فاتح", textColor: "#581C87", category: "بنفسجي" },
  { id: "soft-indigo", color: "#E0E7FF", label: "نيلي فاتح", textColor: "#312E81", category: "بنفسجي" },
  { id: "wisteria", color: "#F0EBFF", label: "وستارية", textColor: "#3B0764", category: "بنفسجي" },
];

// ═══════════════════════════════════════════════════════════
// FORM SETTINGS DIALOG
// ═══════════════════════════════════════════════════════════
export function FormSettingsDialog({
  open,
  onClose,
  settings,
  onApply,
}: FormSettingsDialogProps) {
  const [activeTab, setActiveTab] = useState<"table" | "appearance" | "document">("table");
  const [localSettings, setLocalSettings] = useState<FormSettings>({ ...settings, columnVisibility: settings.columnVisibility.map(c => ({ ...c })) });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Detect theme
  const isDark = typeof document !== "undefined" && !document.documentElement.classList.contains("light-turquoise");
  const bgColors = isDark ? BG_COLORS_DARK : BG_COLORS_LIGHT;

  // Group colors by category
  const categories = [...new Set(bgColors.map(c => c.category))];

  const handleApply = () => {
    onApply(localSettings);
    onClose();
  };

  const handleReset = () => {
    setLocalSettings({
      ...settings,
      columnVisibility: settings.columnVisibility.map(c => ({ ...c, visible: true, active: true })),
      bgMode: "solid",
      bgColor: "transparent",
      bgTextColor: "",
      bgImage: null,
      bgOpacity: 100,
    });
  };

  const toggleColumnVisible = (key: string) => {
    setLocalSettings(prev => ({
      ...prev,
      columnVisibility: prev.columnVisibility.map(c =>
        c.key === key ? { ...c, visible: !c.visible } : c
      ),
    }));
  };

  const toggleColumnActive = (key: string) => {
    setLocalSettings(prev => ({
      ...prev,
      columnVisibility: prev.columnVisibility.map(c =>
        c.key === key ? { ...c, active: !c.active } : c
      ),
    }));
  };

  const moveColumn = (index: number, direction: "up" | "down") => {
    setLocalSettings(prev => {
      const cols = [...prev.columnVisibility];
      const targetIndex = direction === "up" ? index - 1 : index + 1;
      if (targetIndex < 0 || targetIndex >= cols.length) return prev;
      [cols[index], cols[targetIndex]] = [cols[targetIndex], cols[index]];
      return { ...prev, columnVisibility: cols };
    });
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setLocalSettings(prev => ({
        ...prev,
        bgMode: "image",
        bgImage: ev.target?.result as string,
      }));
    };
    reader.readAsDataURL(file);
  };

  const selectBgColor = (bg: BgColorOption) => {
    setLocalSettings(prev => ({
      ...prev,
      bgMode: "solid",
      bgColor: bg.color,
      bgTextColor: bg.textColor,
      bgImage: null,
    }));
  };

  const TABS = [
    { id: "table" as const, label: "تنسيق الجدول", icon: Table2 },
    { id: "appearance" as const, label: "المظهر والخلفية", icon: Palette },
    { id: "document" as const, label: "إعدادات المستند", icon: FileText },
  ];

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent
        className="!max-w-2xl !p-0 !gap-0 !h-[75vh] flex flex-col overflow-hidden border-border/50 !rounded-lg"
        dir="rtl"
      >
        <DialogTitle className="sr-only">إعدادات النموذج</DialogTitle>
        <DialogDescription className="sr-only">تخصيص أعمدة ومظهر نموذج الفاتورة</DialogDescription>

        {/* ─── Title Bar ─── */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-l from-cyan-600 via-cyan-500 to-cyan-600 dark:from-[#2a261b] dark:via-[#1c1915] dark:to-[#2a261b] border-b border-cyan-700 dark:border-[#3d3520] shrink-0">
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-white dark:text-primary" />
            <span className="text-[13px] text-white dark:text-primary/90">
              إعدادات النموذج
            </span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-white/80 hover:text-white hover:bg-white/10 dark:text-primary/60 dark:hover:text-primary"
            onClick={onClose}
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>

        {/* ─── Body ─── */}
        <div className="flex flex-1 min-h-0">
          {/* Sidebar Tabs */}
          <div className="w-44 border-e border-border/30 bg-muted/10 py-2 shrink-0">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-[12px] transition-all ${
                    activeTab === tab.id
                      ? "bg-primary/10 text-primary border-e-2 border-primary"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/20"
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className="flex-1 min-h-0 flex flex-col">
            <ScrollArea className="flex-1 min-h-0" dir="rtl">
              <div className="p-4">
                {/* ════ Table Format Tab ════ */}
                {activeTab === "table" && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-[13px] text-foreground flex items-center gap-2">
                        <Table2 className="w-4 h-4 text-primary" />
                        تنسيق الأعمدة
                      </h4>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 text-[10px] gap-1 text-primary hover:bg-primary/5"
                          onClick={() =>
                            setLocalSettings(prev => ({
                              ...prev,
                              columnVisibility: prev.columnVisibility.map(c => ({ ...c, visible: true })),
                            }))
                          }
                        >
                          <Eye className="w-3 h-3" /> إظهار الكل
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 text-[10px] gap-1 text-muted-foreground hover:bg-muted/20"
                          onClick={() =>
                            setLocalSettings(prev => ({
                              ...prev,
                              columnVisibility: prev.columnVisibility.map(c =>
                                c.key === "rowNum" ? c : { ...c, visible: false }
                              ),
                            }))
                          }
                        >
                          <EyeOff className="w-3 h-3" /> إخفاء الكل
                        </Button>
                      </div>
                    </div>

                    {/* Column Table Header */}
                    <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-0 items-center px-3 py-1.5 bg-gradient-to-b from-slate-100 to-slate-50 dark:from-[#1a1d24] dark:to-[#15171c] border border-border/30 rounded-t-md text-[10px] text-muted-foreground">
                      <span>اسم العمود</span>
                      <span className="w-14 text-center">مرئي</span>
                      <span className="w-14 text-center">نشط</span>
                      <span className="w-16 text-center">الترتيب</span>
                      <span className="w-6" />
                    </div>

                    {/* Column Rows */}
                    <div className="border border-t-0 border-border/30 rounded-b-md divide-y divide-border/20 overflow-hidden">
                      {localSettings.columnVisibility.map((col, idx) => (
                        <div
                          key={col.key}
                          className={`grid grid-cols-[1fr_auto_auto_auto_auto] gap-0 items-center px-3 py-2 transition-colors ${
                            !col.visible ? "opacity-50 bg-muted/10" : "hover:bg-primary/[0.03]"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <GripVertical className="w-3 h-3 text-muted-foreground/40" />
                            <span className="text-[11px] text-foreground">{col.label}</span>
                            {col.key === "rowNum" && (
                              <span className="text-[9px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">ثابت</span>
                            )}
                          </div>
                          <div className="w-14 flex justify-center">
                            <Checkbox
                              checked={col.visible}
                              onCheckedChange={() => toggleColumnVisible(col.key)}
                              className="h-3.5 w-3.5"
                              disabled={col.key === "rowNum"}
                            />
                          </div>
                          <div className="w-14 flex justify-center">
                            <Checkbox
                              checked={col.active}
                              onCheckedChange={() => toggleColumnActive(col.key)}
                              className="h-3.5 w-3.5"
                              disabled={col.key === "rowNum" || !col.visible}
                            />
                          </div>
                          <div className="w-16 flex justify-center gap-0.5">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-5 w-5 text-muted-foreground hover:text-foreground"
                              onClick={() => moveColumn(idx, "up")}
                              disabled={idx === 0}
                            >
                              <ChevronUp className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-5 w-5 text-muted-foreground hover:text-foreground"
                              onClick={() => moveColumn(idx, "down")}
                              disabled={idx === localSettings.columnVisibility.length - 1}
                            >
                              <ChevronDown className="w-3 h-3" />
                            </Button>
                          </div>
                          <div className="w-6 text-center text-[10px] text-muted-foreground/60">
                            {idx + 1}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Summary */}
                    <div className="flex items-center gap-4 pt-2 text-[10px] text-muted-foreground">
                      <span>
                        أعمدة مرئية:{" "}
                        <span className="text-primary">
                          {localSettings.columnVisibility.filter(c => c.visible).length}
                        </span>
                        /{localSettings.columnVisibility.length}
                      </span>
                      <span>
                        أعمدة نشطة:{" "}
                        <span className="text-primary">
                          {localSettings.columnVisibility.filter(c => c.active && c.visible).length}
                        </span>
                      </span>
                    </div>
                  </div>
                )}

                {/* ════ Appearance Tab ════ */}
                {activeTab === "appearance" && (
                  <div className="space-y-5">
                    {/* Background Color */}
                    <div className="space-y-4">
                      <h4 className="text-[13px] text-foreground flex items-center gap-2">
                        <Palette className="w-4 h-4 text-primary" />
                        لون الخلفية
                      </h4>

                      {/* Color groups by category */}
                      {categories.map((category) => {
                        const categoryColors = bgColors.filter(c => c.category === category);
                        return (
                          <div key={category} className="space-y-2">
                            <span className="text-[10px] text-muted-foreground/70 block">{category}</span>
                            <div className="grid grid-cols-4 gap-1.5">
                              {categoryColors.map((bg) => {
                                const isSelected = localSettings.bgMode === "solid" && localSettings.bgColor === bg.color;
                                const isTransparent = bg.color === "transparent";
                                return (
                                  <button
                                    key={bg.id}
                                    onClick={() => selectBgColor(bg)}
                                    className={`relative flex flex-col items-center gap-1.5 px-2 py-2 rounded-lg border-2 transition-all ${
                                      isSelected
                                        ? "border-primary shadow-md shadow-primary/15 scale-[1.02]"
                                        : "border-border/20 hover:border-border/50 hover:shadow-sm"
                                    }`}
                                    title={bg.label}
                                  >
                                    {/* Color swatch - large and clear */}
                                    <div
                                      className="w-full h-10 rounded-md border border-border/30 relative overflow-hidden"
                                      style={{
                                        backgroundColor: isTransparent ? undefined : bg.color,
                                        backgroundImage: isTransparent
                                          ? "repeating-conic-gradient(#d4d4d4 0% 25%, transparent 0% 50%) 0 0 / 12px 12px"
                                          : undefined,
                                      }}
                                    >
                                      {/* Preview text color on the swatch */}
                                      {!isTransparent && (
                                        <span
                                          className="absolute inset-0 flex items-center justify-center text-[9px] opacity-80"
                                          style={{ color: bg.textColor }}
                                        >
                                          نص
                                        </span>
                                      )}
                                      {/* Selected check */}
                                      {isSelected && (
                                        <div className="absolute top-0.5 end-0.5 w-4 h-4 rounded-full bg-primary flex items-center justify-center">
                                          <Check className="w-2.5 h-2.5 text-primary-foreground" />
                                        </div>
                                      )}
                                    </div>
                                    <span className="text-[10px] text-foreground/80 truncate w-full text-center">{bg.label}</span>
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}

                      {/* Current selection preview */}
                      {localSettings.bgColor !== "transparent" && localSettings.bgMode === "solid" && (
                        <div className="mt-3 p-3 rounded-lg border border-border/30 bg-muted/5">
                          <span className="text-[10px] text-muted-foreground block mb-2">معاينة الخلفية والنص</span>
                          <div
                            className="rounded-md p-3 border border-border/20"
                            style={{ backgroundColor: localSettings.bgColor }}
                          >
                            <p className="text-[12px] mb-1" style={{ color: localSettings.bgTextColor }}>
                              نور النبراس للعطور الفاخرة
                            </p>
                            <p className="text-[10px] opacity-80" style={{ color: localSettings.bgTextColor }}>
                              عود ملكي — إصدار محدود — 600 ر.س
                            </p>
                            <div className="flex items-center gap-4 mt-2">
                              <span className="text-[9px] opacity-60" style={{ color: localSettings.bgTextColor }}>الكمية: 3</span>
                              <span className="text-[9px] opacity-60" style={{ color: localSettings.bgTextColor }}>الإجمالي: 1,800 ر.س</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Divider */}
                    <div className="border-t border-border/20" />

                    {/* Background Image */}
                    <div className="space-y-3">
                      <h4 className="text-[13px] text-foreground flex items-center gap-2">
                        <ImageIcon className="w-4 h-4 text-primary" />
                        صورة الخلفية
                      </h4>

                      {localSettings.bgImage ? (
                        <div className="space-y-2">
                          <div className="relative rounded-lg overflow-hidden border border-border/30 h-32">
                            <img
                              src={localSettings.bgImage}
                              alt="خلفية"
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-white bg-black/50 hover:bg-black/70 text-[10px] gap-1"
                                onClick={() =>
                                  setLocalSettings(prev => ({ ...prev, bgImage: null, bgMode: "solid" }))
                                }
                              >
                                <X className="w-3 h-3" /> إزالة
                              </Button>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-[11px] text-muted-foreground">شفافية الصورة</span>
                            <input
                              type="range"
                              min={10}
                              max={100}
                              value={localSettings.bgOpacity}
                              onChange={(e) =>
                                setLocalSettings(prev => ({ ...prev, bgOpacity: parseInt(e.target.value) }))
                              }
                              className="flex-1 h-1 accent-[color:var(--primary)]"
                            />
                            <span className="text-[10px] text-muted-foreground w-8 text-center" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                              {localSettings.bgOpacity}%
                            </span>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="w-full flex flex-col items-center justify-center gap-2 py-8 rounded-lg border-2 border-dashed border-border/40 hover:border-primary/40 bg-muted/5 hover:bg-primary/[0.02] transition-all group cursor-pointer"
                        >
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/15 transition-colors">
                            <Upload className="w-5 h-5 text-primary" />
                          </div>
                          <span className="text-[11px] text-muted-foreground group-hover:text-foreground">
                            اسحب صورة هنا أو اضغط للتحميل
                          </span>
                          <span className="text-[9px] text-muted-foreground/60">
                            PNG, JPG — حد أقصى 5MB
                          </span>
                        </button>
                      )}
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        className="hidden"
                        onChange={handleImageUpload}
                      />
                    </div>
                  </div>
                )}

                {/* ════ Document Tab ════ */}
                {activeTab === "document" && (
                  <div className="space-y-4">
                    <h4 className="text-[13px] text-foreground flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary" />
                      إعدادات المستند
                    </h4>

                    <div className="space-y-3">
                      <div className="flex items-center gap-3 p-3 rounded-md bg-muted/10 border border-border/20">
                        <Checkbox checked={true} className="h-3.5 w-3.5" />
                        <div>
                          <span className="text-[11px] text-foreground block">إظهار شريط الأدوات</span>
                          <span className="text-[9px] text-muted-foreground">عرض أزرار الإضافة والحذف فوق الجدول</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-3 rounded-md bg-muted/10 border border-border/20">
                        <Checkbox checked={true} className="h-3.5 w-3.5" />
                        <div>
                          <span className="text-[11px] text-foreground block">��ظهار الصفوف الفارغة</span>
                          <span className="text-[9px] text-muted-foreground">عرض صفوف فارغة بأسلوب Excel لمظهر ERP</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-3 rounded-md bg-muted/10 border border-border/20">
                        <Checkbox checked={true} className="h-3.5 w-3.5" />
                        <div>
                          <span className="text-[11px] text-foreground block">التظليل الذكي للخلايا</span>
                          <span className="text-[9px] text-muted-foreground">تظليل الصف والعمود عند تحديد خلية</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-3 rounded-md bg-muted/10 border border-border/20">
                        <Checkbox checked={true} className="h-3.5 w-3.5" />
                        <div>
                          <span className="text-[11px] text-foreground block">أعمدة قابلة لتغيير الحجم</span>
                          <span className="text-[9px] text-muted-foreground">السماح بسحب حافة العمود لتغيير عرضه</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-3 rounded-md bg-muted/10 border border-border/20">
                        <Checkbox checked={true} className="h-3.5 w-3.5" />
                        <div>
                          <span className="text-[11px] text-foreground block">إظهار ملخص الإجماليات</span>
                          <span className="text-[9px] text-muted-foreground">عرض قسم الإجماليات والضرائب في التذييل</span>
                        </div>
                      </div>
                    </div>

                    {/* Row format section */}
                    <div className="border-t border-border/20 pt-4 mt-4">
                      <h4 className="text-[13px] text-foreground flex items-center gap-2 mb-3">
                        <Rows3 className="w-4 h-4 text-primary" />
                        تنسيق الصف
                      </h4>
                      <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 rounded-md bg-muted/10 border border-border/20">
                          <Checkbox checked={true} className="h-3.5 w-3.5" />
                          <div>
                            <span className="text-[11px] text-foreground block">تلوين متبادل للصفوف</span>
                            <span className="text-[9px] text-muted-foreground">تطبيق لون خلفية متبادل بين الصفوف</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 p-3 rounded-md bg-muted/10 border border-border/20">
                          <Checkbox checked={true} className="h-3.5 w-3.5" />
                          <div>
                            <span className="text-[11px] text-foreground block">إبراز الصف المحدد</span>
                            <span className="text-[9px] text-muted-foreground">تمييز الصف النشط بلون مختلف</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Footer */}
            <div className="px-4 py-2.5 border-t border-border/30 flex items-center justify-between bg-muted/10 shrink-0">
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-[10px] gap-1 text-muted-foreground hover:text-foreground"
                onClick={handleReset}
              >
                <RotateCcw className="w-3 h-3" /> استعادة الافتراضي
              </Button>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-[10px] rounded-sm"
                  onClick={onClose}
                >
                  إلغاء
                </Button>
                <Button
                  size="sm"
                  className="h-7 text-[10px] gap-1 rounded-sm bg-cyan-500 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] text-white hover:bg-cyan-600 dark:hover:from-[#AA771C] dark:hover:to-[#BF953F] border-none shadow-sm"
                  onClick={handleApply}
                >
                  تطبيق
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}