import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Palette, LayoutDashboard, Bell, Globe, Route, Crown,
  Timer, BarChart3, Brain, UserCog, Search, Plus, Trash2,
  ChevronDown, Copy, Pencil,
  Settings2, Eye, EyeOff, GripVertical,
  Zap, Clock, Calendar, ArrowUpDown, Filter, Info,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Switch } from "../ui/switch";
import { TooltipProvider } from "../ui/tooltip";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "../ui/dialog";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import {
  settingsSections,
  themeSettings,
  dashboardWidgets,
  notificationSettings,
  languageSettings,
  getRulesByCategory,
  ruleCategoryDescriptions,
  type Rule,
  type RuleCategory,
  type ThemeSetting,
  type DashboardWidget,
  type NotificationSetting,
  type LanguageSetting,
} from "./settings-data";

// ── Icon Map ─────────────────────────────────────────────

const iconMap: Record<string, typeof Palette> = {
  Palette, LayoutDashboard, Bell, Globe, Route, Crown,
  Timer, BarChart3, Brain, UserCog,
};

// ── Helpers ──────────────────────────────────────────────

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ar-SA", {
    year: "numeric", month: "short", day: "numeric",
  });
}

function priorityBadge(p: number): { label: string; color: string } {
  if (p === 1) return { label: "حرج", color: "bg-red-500/15 text-red-400 border-red-500/20" };
  if (p === 2) return { label: "عالي", color: "bg-primary/15 text-primary border-primary/20" };
  if (p === 3) return { label: "متوسط", color: "bg-blue-500/15 text-blue-400 border-blue-500/20" };
  if (p <= 5) return { label: "عادي", color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" };
  return { label: "منخفض", color: "bg-muted/30 text-muted-foreground border-border/30" };
}

// ── Main Component ──────────────────────────────────────

interface SettingsProps {
  isDark: boolean;
}

export function SettingsPage({ isDark }: SettingsProps) {
  const [activeSection, setActiveSection] = useState("ui-theme");
  const [expandedRule, setExpandedRule] = useState<string | null>(null);
  const [ruleSearch, setRuleSearch] = useState("");
  const [ruleFilterEnabled, setRuleFilterEnabled] = useState<"all" | "enabled" | "disabled">("all");
  const [sortBy, setSortBy] = useState<"priority" | "name" | "date">("priority");
  const [showAddRule, setShowAddRule] = useState(false);

  // Local UI state copies
  const [localTheme, setLocalTheme] = useState(themeSettings);
  const [localWidgets, setLocalWidgets] = useState(dashboardWidgets);
  const [localNotifications, setLocalNotifications] = useState(notificationSettings);
  const [localLanguage, setLocalLanguage] = useState(languageSettings);
  const [localRules, setLocalRules] = useState<Record<string, Rule[]>>({
    routing: getRulesByCategory("routing"),
    vip: getRulesByCategory("vip"),
    sla: getRulesByCategory("sla"),
    kpi: getRulesByCategory("kpi"),
    ai: getRulesByCategory("ai"),
    assignment: getRulesByCategory("assignment"),
  });

  const currentSection = settingsSections.find((s) => s.id === activeSection);
  const isRulesSection = currentSection?.group === "rules";
  const ruleCategory = isRulesSection ? activeSection.replace("rules-", "") as RuleCategory : null;

  const filteredRules = useMemo(() => {
    if (!ruleCategory || !localRules[ruleCategory]) return [];
    let rules = [...localRules[ruleCategory]];
    if (ruleSearch) {
      const q = ruleSearch.toLowerCase();
      rules = rules.filter(
        (r) =>
          r.name.includes(ruleSearch) ||
          r.condition.includes(ruleSearch) ||
          r.action.includes(ruleSearch) ||
          r.id.toLowerCase().includes(q),
      );
    }
    if (ruleFilterEnabled === "enabled") rules = rules.filter((r) => r.enabled);
    if (ruleFilterEnabled === "disabled") rules = rules.filter((r) => !r.enabled);

    if (sortBy === "priority") rules.sort((a, b) => a.priority - b.priority);
    else if (sortBy === "name") rules.sort((a, b) => a.name.localeCompare(b.name, "ar"));
    else rules.sort((a, b) => new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime());

    return rules;
  }, [ruleCategory, localRules, ruleSearch, ruleFilterEnabled, sortBy]);

  const toggleRuleEnabled = (ruleId: string) => {
    if (!ruleCategory) return;
    setLocalRules((prev) => ({
      ...prev,
      [ruleCategory]: prev[ruleCategory].map((r) =>
        r.id === ruleId ? { ...r, enabled: !r.enabled } : r,
      ),
    }));
  };

  const addNewRule = (rule: Omit<Rule, "id" | "lastModified" | "modifiedBy">) => {
    if (!ruleCategory) return;
    const prefix = ruleCategory === "routing" ? "RT" : ruleCategory === "vip" ? "VIP" : ruleCategory === "sla" ? "SLA" : ruleCategory === "kpi" ? "KPI" : ruleCategory === "ai" ? "AI" : "ASN";
    const count = localRules[ruleCategory].length + 1;
    const newRule: Rule = {
      ...rule,
      id: `${prefix}-${String(count).padStart(3, "0")}`,
      lastModified: new Date().toISOString().split("T")[0],
      modifiedBy: "أحمد العلي",
    };
    setLocalRules((prev) => ({
      ...prev,
      [ruleCategory]: [...prev[ruleCategory], newRule],
    }));
    setShowAddRule(false);
  };

  const deleteRule = (ruleId: string) => {
    if (!ruleCategory) return;
    setLocalRules((prev) => ({
      ...prev,
      [ruleCategory]: prev[ruleCategory].filter((r) => r.id !== ruleId),
    }));
    if (expandedRule === ruleId) setExpandedRule(null);
  };

  const surface = isDark ? "#1a1a2e" : "#e3edf2";
  const outerShadow = isDark
    ? "4px 4px 10px rgba(0,0,0,0.55), -3px -3px 8px rgba(50,50,80,0.25), inset 0 1px 0 rgba(255,255,255,0.03)"
    : "4px 4px 10px rgba(165,180,195,0.4), -3px -3px 8px rgba(255,255,255,0.75), inset 0 1px 0 rgba(255,255,255,0.5)";
  const innerShadow = isDark
    ? "inset 3px 3px 6px rgba(0,0,0,0.4), inset -2px -2px 5px rgba(50,50,80,0.15)"
    : "inset 3px 3px 6px rgba(165,180,195,0.35), inset -2px -2px 5px rgba(255,255,255,0.7)";
  const cardShadow = isDark
    ? "2px 2px 6px rgba(0,0,0,0.35), -1px -1px 4px rgba(50,50,80,0.15)"
    : "2px 2px 6px rgba(165,180,195,0.3), -1px -1px 4px rgba(255,255,255,0.6)";

  const uiSections = settingsSections.filter((s) => s.group === "ui");
  const rulesSections = settingsSections.filter((s) => s.group === "rules");

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex gap-6 h-[calc(100vh-12rem)]" dir="rtl">

        {/* ═══ Left Sidebar Navigation ═══ */}
        <div
          className="w-64 shrink-0 rounded-2xl p-4 flex flex-col gap-1 overflow-y-auto"
          style={{ background: surface, boxShadow: outerShadow }}
        >
          {/* UI Group */}
          <p className="text-[9px] text-muted-foreground px-3 pt-2 pb-1.5 flex items-center gap-1.5">
            <Settings2 className="w-3 h-3" />
            واجهة المستخدم
          </p>
          {uiSections.map((section) => {
            const Icon = iconMap[section.icon] ?? Settings2;
            const isActive = activeSection === section.id;
            return (
              <motion.button
                key={section.id}
                onClick={() => { setActiveSection(section.id); setRuleSearch(""); setExpandedRule(null); }}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs text-start transition-all duration-200 cursor-pointer outline-none ${
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                style={{
                  background: isActive
                    ? isDark ? "linear-gradient(135deg, rgba(212,175,55,0.12), rgba(212,175,55,0.04))" : "linear-gradient(135deg, rgba(6,182,212,0.12), rgba(6,182,212,0.04))"
                    : "transparent",
                  boxShadow: isActive ? cardShadow : "none",
                }}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{section.label}</span>
              </motion.button>
            );
          })}

          {/* Divider */}
          <div className="my-2 border-t border-border/20" />

          {/* Rules Group */}
          <p className="text-[9px] text-muted-foreground px-3 pt-1 pb-1.5 flex items-center gap-1.5">
            <Zap className="w-3 h-3" />
            محرك القواعد
          </p>
          {rulesSections.map((section) => {
            const Icon = iconMap[section.icon] ?? Settings2;
            const isActive = activeSection === section.id;
            const cat = section.id.replace("rules-", "") as RuleCategory;
            const rules = localRules[cat] ?? [];
            const enabledCount = rules.filter((r) => r.enabled).length;
            return (
              <motion.button
                key={section.id}
                onClick={() => { setActiveSection(section.id); setRuleSearch(""); setExpandedRule(null); }}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs text-start transition-all duration-200 cursor-pointer outline-none ${
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                style={{
                  background: isActive
                    ? isDark ? "linear-gradient(135deg, rgba(212,175,55,0.12), rgba(212,175,55,0.04))" : "linear-gradient(135deg, rgba(6,182,212,0.12), rgba(6,182,212,0.04))"
                    : "transparent",
                  boxShadow: isActive ? cardShadow : "none",
                }}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="flex-1">{section.label}</span>
                <Badge className="text-[8px] h-4 px-1.5 bg-muted/20 text-muted-foreground border-border/20">
                  {enabledCount}/{rules.length}
                </Badge>
              </motion.button>
            );
          })}
        </div>

        {/* ═══ Main Content Area ═══ */}
        <div className="flex-1 min-w-0">
          <ScrollArea className="h-full">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeSection}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="space-y-5 pe-4"
              >
                {/* Section Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg text-foreground flex items-center gap-2">
                      {currentSection && (() => {
                        const Icon = iconMap[currentSection.icon] ?? Settings2;
                        return <Icon className="w-5 h-5 text-primary" />;
                      })()}
                      {currentSection?.label}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {currentSection?.description}
                    </p>
                  </div>
                  {isRulesSection && (
                    <Button
                      size="sm"
                      className="h-8 text-xs gap-1.5"
                      onClick={() => setShowAddRule(true)}
                    >
                      <Plus className="w-3.5 h-3.5" />
                      إضافة قاعدة
                    </Button>
                  )}
                </div>

                {/* ═══ UI SECTIONS ═══ */}

                {activeSection === "ui-theme" && (
                  <ThemeSection settings={localTheme} onChange={setLocalTheme} isDark={isDark} surface={surface} cardShadow={cardShadow} innerShadow={innerShadow} />
                )}

                {activeSection === "ui-dashboard" && (
                  <DashboardSection widgets={localWidgets} onChange={setLocalWidgets} isDark={isDark} surface={surface} cardShadow={cardShadow} />
                )}

                {activeSection === "ui-notifications" && (
                  <NotificationsSection settings={localNotifications} onChange={setLocalNotifications} isDark={isDark} surface={surface} cardShadow={cardShadow} />
                )}

                {activeSection === "ui-language" && (
                  <LanguageSection settings={localLanguage} onChange={setLocalLanguage} isDark={isDark} surface={surface} cardShadow={cardShadow} />
                )}

                {/* ═══ RULES SECTIONS ═══ */}

                {isRulesSection && ruleCategory && (
                  <RulesTableSection
                    category={ruleCategory}
                    rules={filteredRules}
                    totalCount={localRules[ruleCategory]?.length ?? 0}
                    search={ruleSearch}
                    onSearchChange={setRuleSearch}
                    filterEnabled={ruleFilterEnabled}
                    onFilterChange={setRuleFilterEnabled}
                    sortBy={sortBy}
                    onSortChange={setSortBy}
                    expandedRule={expandedRule}
                    onExpandRule={setExpandedRule}
                    onToggleRule={toggleRuleEnabled}
                    onDeleteRule={deleteRule}
                    isDark={isDark}
                    surface={surface}
                    cardShadow={cardShadow}
                    innerShadow={innerShadow}
                  />
                )}

              </motion.div>
            </AnimatePresence>
          </ScrollArea>
        </div>
      </div>

      {/* ── Add Rule Dialog ── */}
      {isRulesSection && ruleCategory && (
        <AddRuleDialog
          open={showAddRule}
          onClose={() => setShowAddRule(false)}
          onAdd={addNewRule}
          category={ruleCategory}
        />
      )}
    </TooltipProvider>
  );
}

// ═══════════════════════════════════════════════════════════
// UI SECTION COMPONENTS
// ═══════════════════════════════════════════════════════════

// ── Theme Section ────────────────────────────────────────

function ThemeSection({ settings, onChange, isDark, surface, cardShadow, innerShadow }: {
  settings: ThemeSetting[];
  onChange: (s: ThemeSetting[]) => void;
  isDark: boolean;
  surface: string;
  cardShadow: string;
  innerShadow: string;
}) {
  const toggleSetting = (id: string) => {
    onChange(settings.map((s) => s.id === id ? { ...s, value: !s.value } : s));
  };

  const updateValue = (id: string, value: string | number) => {
    onChange(settings.map((s) => s.id === id ? { ...s, value } : s));
  };

  return (
    <div className="space-y-3">
      {/* Color Preview */}
      <div
        className="rounded-xl p-4"
        style={{ background: surface, boxShadow: cardShadow }}
      >
        <p className="text-xs text-muted-foreground mb-3 flex items-center gap-1.5">
          <Palette className="w-3.5 h-3.5" />
          معاينة الألوان الحالية
        </p>
        <div className="flex gap-3">
          {[
            { label: "أساسي", color: isDark ? "#D4AF37" : "#06B6D4" },
            { label: "سطح", color: isDark ? "#1a1a2e" : "#e3edf2" },
            { label: "خلفية", color: isDark ? "#0A0A0A" : "#FFFFFF" },
            { label: "نص", color: isDark ? "#F5F5F5" : "#0F172A" },
            { label: "صامت", color: isDark ? "#A0A0A0" : "#64748B" },
            { label: "حدود", color: isDark ? "rgba(212,175,55,0.3)" : "rgba(6,182,212,0.3)" },
          ].map((c) => (
            <div key={c.label} className="flex flex-col items-center gap-1.5">
              <div
                className="w-10 h-10 rounded-lg border border-border/30"
                style={{ background: c.color, boxShadow: innerShadow }}
              />
              <span className="text-[8px] text-muted-foreground">{c.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Settings Cards */}
      {settings.map((setting) => (
        <div
          key={setting.id}
          className="rounded-xl p-4 flex items-center justify-between gap-4"
          style={{ background: surface, boxShadow: cardShadow }}
        >
          <div className="flex-1 min-w-0">
            <p className="text-sm text-foreground">{setting.label}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">{setting.description}</p>
          </div>
          {setting.type === "toggle" && (
            <Switch
              checked={setting.value as boolean}
              onCheckedChange={() => toggleSetting(setting.id)}
            />
          )}
          {setting.type === "select" && (
            <select
              value={setting.value as string}
              onChange={(e) => updateValue(setting.id, e.target.value)}
              className="h-8 text-xs bg-card border border-border/30 rounded-lg px-3 text-foreground min-w-[140px]"
            >
              {setting.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          )}
          {setting.type === "slider" && (
            <div className="flex items-center gap-2 min-w-[140px]">
              <input
                type="range"
                min={0}
                max={24}
                value={setting.value as number}
                onChange={(e) => updateValue(setting.id, parseInt(e.target.value))}
                className="flex-1 accent-[var(--primary)]"
              />
              <span className="text-xs text-muted-foreground w-8 text-center">{setting.value}px</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Dashboard Section ────────────────────────────────────

function DashboardSection({ widgets, onChange, isDark, surface, cardShadow }: {
  widgets: DashboardWidget[];
  onChange: (w: DashboardWidget[]) => void;
  isDark: boolean;
  surface: string;
  cardShadow: string;
}) {
  const toggleWidget = (id: string) => {
    onChange(widgets.map((w) => w.id === id ? { ...w, visible: !w.visible } : w));
  };

  const visibleCount = widgets.filter((w) => w.visible).length;

  return (
    <div className="space-y-3">
      {/* Summary bar */}
      <div
        className="rounded-xl p-3 flex items-center justify-between"
        style={{ background: surface, boxShadow: cardShadow }}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Eye className="w-3.5 h-3.5" />
            <span>ظاهر: <span className="text-primary">{visibleCount}</span></span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <EyeOff className="w-3.5 h-3.5" />
            <span>مخفي: <span className="text-foreground">{widgets.length - visibleCount}</span></span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1" onClick={() => onChange(widgets.map((w) => ({ ...w, visible: true })))}>
            <Eye className="w-3 h-3" />
            إظهار الكل
          </Button>
          <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1" onClick={() => onChange(widgets.map((w) => ({ ...w, visible: false })))}>
            <EyeOff className="w-3 h-3" />
            إخفاء الكل
          </Button>
        </div>
      </div>

      {/* Widgets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {widgets.map((widget) => (
          <motion.div
            key={widget.id}
            layout
            className={`rounded-xl p-4 flex items-center justify-between gap-3 transition-opacity ${
              !widget.visible ? "opacity-50" : ""
            }`}
            style={{ background: surface, boxShadow: cardShadow }}
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <GripVertical className="w-4 h-4 text-muted-foreground/30 shrink-0 cursor-grab" />
              <div className="min-w-0">
                <p className="text-sm text-foreground truncate">{widget.label}</p>
                <p className="text-[10px] text-muted-foreground truncate">{widget.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge className={`text-[8px] h-4 ${
                widget.size === "lg" ? "bg-primary/10 text-primary border-primary/20" :
                widget.size === "md" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                "bg-muted/20 text-muted-foreground border-border/20"
              }`}>
                {widget.size === "lg" ? "كبير" : widget.size === "md" ? "متوسط" : "صغير"}
              </Badge>
              <Switch
                checked={widget.visible}
                onCheckedChange={() => toggleWidget(widget.id)}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// ── Notifications Section ────────────────────────────────

function NotificationsSection({ settings, onChange, isDark, surface, cardShadow }: {
  settings: NotificationSetting[];
  onChange: (s: NotificationSetting[]) => void;
  isDark: boolean;
  surface: string;
  cardShadow: string;
}) {
  const toggleField = (id: string, field: "sound" | "popup" | "badge") => {
    onChange(settings.map((s) => s.id === id ? { ...s, [field]: !s[field] } : s));
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div
        className="rounded-xl p-3"
        style={{ background: surface, boxShadow: cardShadow }}
      >
        <div className="grid grid-cols-[1fr_60px_60px_60px] gap-2 text-[10px] text-muted-foreground">
          <span>نوع الإشعار</span>
          <span className="text-center">صوت</span>
          <span className="text-center">نافذة</span>
          <span className="text-center">شارة</span>
        </div>
      </div>

      {settings.map((setting) => (
        <div
          key={setting.id}
          className="rounded-xl p-3"
          style={{ background: surface, boxShadow: cardShadow }}
        >
          <div className="grid grid-cols-[1fr_60px_60px_60px] gap-2 items-center">
            <div className="min-w-0">
              <p className="text-sm text-foreground">{setting.label}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5 truncate">{setting.description}</p>
            </div>
            <div className="flex justify-center">
              <Switch checked={setting.sound} onCheckedChange={() => toggleField(setting.id, "sound")} />
            </div>
            <div className="flex justify-center">
              <Switch checked={setting.popup} onCheckedChange={() => toggleField(setting.id, "popup")} />
            </div>
            <div className="flex justify-center">
              <Switch checked={setting.badge} onCheckedChange={() => toggleField(setting.id, "badge")} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Language Section ─────────────────────────────────────

function LanguageSection({ settings, onChange, isDark, surface, cardShadow }: {
  settings: LanguageSetting[];
  onChange: (s: LanguageSetting[]) => void;
  isDark: boolean;
  surface: string;
  cardShadow: string;
}) {
  const updateSetting = (id: string, value: string | boolean) => {
    onChange(settings.map((s) => s.id === id ? { ...s, value } : s));
  };

  return (
    <div className="space-y-3">
      {settings.map((setting) => (
        <div
          key={setting.id}
          className="rounded-xl p-4 flex items-center justify-between gap-4"
          style={{ background: surface, boxShadow: cardShadow }}
        >
          <div className="flex-1">
            <p className="text-sm text-foreground">{setting.label}</p>
          </div>
          {setting.type === "select" && (
            <select
              value={setting.value as string}
              onChange={(e) => updateSetting(setting.id, e.target.value)}
              className="h-8 text-xs bg-card border border-border/30 rounded-lg px-3 text-foreground min-w-[160px]"
            >
              {setting.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          )}
          {setting.type === "toggle" && (
            <Switch
              checked={setting.value as boolean}
              onCheckedChange={(v) => updateSetting(setting.id, v)}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// RULES TABLE SECTION
// ═══════════════════════════════════════════════════════════

function RulesTableSection({
  category, rules, totalCount, search, onSearchChange,
  filterEnabled, onFilterChange, sortBy, onSortChange,
  expandedRule, onExpandRule, onToggleRule, onDeleteRule,
  isDark, surface, cardShadow, innerShadow,
}: {
  category: RuleCategory;
  rules: Rule[];
  totalCount: number;
  search: string;
  onSearchChange: (s: string) => void;
  filterEnabled: "all" | "enabled" | "disabled";
  onFilterChange: (f: "all" | "enabled" | "disabled") => void;
  sortBy: "priority" | "name" | "date";
  onSortChange: (s: "priority" | "name" | "date") => void;
  expandedRule: string | null;
  onExpandRule: (id: string | null) => void;
  onToggleRule: (id: string) => void;
  onDeleteRule: (id: string) => void;
  isDark: boolean;
  surface: string;
  cardShadow: string;
  innerShadow: string;
}) {
  const description = ruleCategoryDescriptions[category];
  const enabledCount = rules.filter((r) => r.enabled).length;

  return (
    <div className="space-y-4">
      {/* Description banner */}
      <div
        className="rounded-xl p-3.5 flex items-start gap-3"
        style={{
          background: isDark
            ? "linear-gradient(135deg, rgba(212,175,55,0.06), rgba(212,175,55,0.02))"
            : "linear-gradient(135deg, rgba(6,182,212,0.06), rgba(6,182,212,0.02))",
          boxShadow: cardShadow,
        }}
      >
        <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <div>
          <p className="text-xs text-foreground">{description}</p>
          <p className="text-[10px] text-muted-foreground mt-1">
            {totalCount} قاعدة — {enabledCount} مفعّلة — {totalCount - enabledCount} معطّلة
          </p>
        </div>
      </div>

      {/* Filters bar */}
      <div
        className="rounded-xl p-3 flex items-center gap-3 flex-wrap"
        style={{ background: surface, boxShadow: cardShadow }}
      >
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input
            placeholder="بحث في القواعد..."
            className="h-8 text-xs ps-8"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        <div className="flex gap-1.5">
          {(["all", "enabled", "disabled"] as const).map((f) => (
            <button
              key={f}
              onClick={() => onFilterChange(f)}
              className={`px-2.5 py-1.5 rounded-lg text-[10px] border transition-all cursor-pointer ${
                filterEnabled === f
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border/30 text-muted-foreground hover:border-primary/30"
              }`}
            >
              {f === "all" ? "الكل" : f === "enabled" ? "مفعّلة" : "معطّلة"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
          <ArrowUpDown className="w-3 h-3" />
          <select
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value as typeof sortBy)}
            className="h-7 text-[10px] bg-card border border-border/30 rounded-lg px-2 text-foreground"
          >
            <option value="priority">الأولوية</option>
            <option value="name">الاسم</option>
            <option value="date">آخر تعديل</option>
          </select>
        </div>
      </div>

      {/* Rules List */}
      <div className="space-y-2.5">
        {rules.map((rule) => {
          const isExpanded = expandedRule === rule.id;
          const pb = priorityBadge(rule.priority);
          return (
            <motion.div
              key={rule.id}
              layout
              className="rounded-xl overflow-hidden"
              style={{ background: surface, boxShadow: cardShadow }}
            >
              {/* Rule header row */}
              <div
                className="p-3.5 flex items-center gap-3 cursor-pointer hover:bg-primary/[0.02] transition-colors"
                onClick={() => onExpandRule(isExpanded ? null : rule.id)}
              >
                {/* Priority indicator */}
                <div className={`w-1 h-10 rounded-full shrink-0 ${
                  rule.priority === 1 ? "bg-red-500" :
                  rule.priority === 2 ? "bg-primary" :
                  rule.priority === 3 ? "bg-blue-500" :
                  "bg-emerald-500"
                }`} />

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono text-muted-foreground/60">{rule.id}</span>
                    <span className="text-sm text-foreground truncate">{rule.name}</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-0.5 truncate">{rule.condition}</p>
                </div>

                {/* Meta */}
                <div className="flex items-center gap-2 shrink-0">
                  <Badge className={`text-[8px] h-4 border ${pb.color}`}>
                    {pb.label}
                  </Badge>
                  {!rule.enabled && (
                    <Badge className="text-[8px] h-4 bg-muted/30 text-muted-foreground border-border/20">
                      معطّلة
                    </Badge>
                  )}
                  <div onClick={(e) => e.stopPropagation()}>
                    <Switch
                      checked={rule.enabled}
                      onCheckedChange={() => onToggleRule(rule.id)}
                    />
                  </div>
                  <motion.div
                    animate={{ rotate: isExpanded ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  </motion.div>
                </div>
              </div>

              {/* Expanded detail */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: "easeInOut" }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 pt-1 border-t border-border/10 space-y-3">
                      {/* Detail grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {/* Condition */}
                        <div
                          className="rounded-lg p-3 space-y-1.5"
                          style={{ boxShadow: innerShadow, background: isDark ? "rgba(0,0,0,0.15)" : "rgba(0,0,0,0.03)" }}
                        >
                          <p className="text-[9px] text-muted-foreground flex items-center gap-1">
                            <Filter className="w-3 h-3" />
                            الشرط
                          </p>
                          <p className="text-xs text-foreground">{rule.condition}</p>
                        </div>

                        {/* Action */}
                        <div
                          className="rounded-lg p-3 space-y-1.5"
                          style={{ boxShadow: innerShadow, background: isDark ? "rgba(0,0,0,0.15)" : "rgba(0,0,0,0.03)" }}
                        >
                          <p className="text-[9px] text-muted-foreground flex items-center gap-1">
                            <Zap className="w-3 h-3" />
                            الإجراء
                          </p>
                          <p className="text-xs text-foreground">{rule.action}</p>
                        </div>
                      </div>

                      {/* Metadata row */}
                      <div className="flex items-center gap-4 flex-wrap text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          سارية: {formatDate(rule.effectiveFrom)} — {formatDate(rule.effectiveTo)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          آخر تعديل: {formatDate(rule.lastModified)}
                        </span>
                        <span className="flex items-center gap-1">
                          <UserCog className="w-3 h-3" />
                          بواسطة: {rule.modifiedBy}
                        </span>
                      </div>

                      {/* Description */}
                      {rule.description && (
                        <p className="text-[10px] text-muted-foreground/80 border-s-2 border-primary/20 ps-2">
                          {rule.description}
                        </p>
                      )}

                      {/* Actions */}
                      <div className="flex items-center gap-2 pt-1">
                        <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1">
                          <Pencil className="w-3 h-3" />
                          تعديل
                        </Button>
                        <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1">
                          <Copy className="w-3 h-3" />
                          نسخ
                        </Button>
                        <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1 text-red-400 hover:text-red-300 border-red-500/20 hover:border-red-500/40" onClick={() => onDeleteRule(rule.id)}>
                          <Trash2 className="w-3 h-3" />
                          حذف
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}

        {rules.length === 0 && (
          <div className="text-center py-12">
            <Search className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
            <p className="text-xs text-muted-foreground">لا توجد قواعد مطابقة</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Add Rule Dialog ──────────────────────────────────────

function AddRuleDialog({
  open, onClose, onAdd, category,
}: {
  open: boolean;
  onClose: () => void;
  onAdd: (rule: Omit<Rule, "id" | "lastModified" | "modifiedBy">) => void;
  category: RuleCategory;
}) {
  const [name, setName] = useState("");
  const [condition, setCondition] = useState("");
  const [action, setAction] = useState("");
  const [priority, setPriority] = useState(3);
  const [effectiveFrom, setEffectiveFrom] = useState(new Date().toISOString().split("T")[0]);
  const [effectiveTo, setEffectiveTo] = useState(new Date().toISOString().split("T")[0]);
  const [description, setDescription] = useState("");

  const handleSubmit = () => {
    onAdd({
      name,
      condition,
      action,
      priority,
      effectiveFrom,
      effectiveTo,
      description,
      enabled: true,
      category,
    });
    setName("");
    setCondition("");
    setAction("");
    setPriority(3);
    setDescription("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>إضافة قاعدة جديدة</DialogTitle>
          <DialogDescription>
            قم بتعبئة المعلومات أدناه لإضافة قاعدة جديدة لفئة {category}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">اسم القاعدة</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-8 text-xs"
                placeholder="مثال: توجيه تلقائي"
              />
            </div>
            <div>
              <Label htmlFor="priority">الأولوية</Label>
              <select
                id="priority"
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value))}
                className="h-8 text-xs bg-card border border-border/30 rounded-lg px-3 text-foreground"
              >
                <option value={1}>حرج</option>
                <option value={2}>عالي</option>
                <option value={3}>متوسط</option>
                <option value={4}>عادي</option>
                <option value={5}>منخفض</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="effectiveFrom">فعالة من</Label>
              <Input
                id="effectiveFrom"
                type="date"
                value={effectiveFrom}
                onChange={(e) => setEffectiveFrom(e.target.value)}
                className="h-8 text-xs"
              />
            </div>
            <div>
              <Label htmlFor="effectiveTo">فعالة حتى</Label>
              <Input
                id="effectiveTo"
                type="date"
                value={effectiveTo}
                onChange={(e) => setEffectiveTo(e.target.value)}
                className="h-8 text-xs"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="condition">الشرط</Label>
            <Textarea
              id="condition"
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              className="h-20 text-xs"
              placeholder="مثال: إذا كانت حالة الطلب 'جديدة'"
            />
          </div>

          <div>
            <Label htmlFor="action">الإجراء</Label>
            <Textarea
              id="action"
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="h-20 text-xs"
              placeholder="مثال: تعيين حالة الطلب إلى 'قيد المعالجة'"
            />
          </div>

          <div>
            <Label htmlFor="description">الوصف (اختياري)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="h-20 text-xs"
              placeholder="تفاصيل إضافية حول القاعدة"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1" onClick={onClose}>
            إلغاء
          </Button>
          <Button size="sm" className="h-7 text-[10px] gap-1" onClick={handleSubmit}>
            إضافة
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}