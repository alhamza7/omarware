import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Timer, Route, ArrowUpCircle, ShieldCheck, CalendarCheck,
  Bell, Crown, Zap, ChevronDown, ChevronUp, GripVertical,
  Plus, Copy, Trash2, Settings2, Power, PowerOff,
  ChevronLeft, Search, Filter, AlertTriangle, Info,
  Pencil, Check, X, ArrowRight, Package,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";
import { ScrollArea } from "../ui/scroll-area";
import { Separator } from "../ui/separator";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../ui/select";
import {
  Dialog, DialogContent, DialogTitle, DialogDescription,
} from "../ui/dialog";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";
import {
  ruleCategories, allRules, operatorLabels, actionLabels, fieldCatalog,
  type Rule, type RuleCategory, type RuleCategoryMeta, type RuleCondition,
  type RuleAction, type ConditionOperator, type ActionType,
} from "./ad-rules-data";

// ── Icon Resolver ──────────────────────────────────────
const iconMap: Record<string, typeof Timer> = {
  Timer, Route, ArrowUpCircle, ShieldCheck, CalendarCheck, Bell, Crown, Zap, Package,
};

// ── Main Component ─────────────────────────────────────

export function ADRuleEngine() {
  const [rules, setRules] = useState<Rule[]>(allRules);
  const [activeCategory, setActiveCategory] = useState<RuleCategory>("sla");
  const [expandedRule, setExpandedRule] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);

  const categoryRules = useMemo(() => {
    let filtered = rules.filter((r) => r.category === activeCategory);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (r) => r.name.includes(searchQuery) || r.description.includes(searchQuery)
      );
    }
    return filtered.sort((a, b) => a.priority - b.priority);
  }, [rules, activeCategory, searchQuery]);

  const activeCat = ruleCategories.find((c) => c.id === activeCategory)!;

  const totalRules = rules.length;
  const enabledRules = rules.filter((r) => r.enabled).length;
  const disabledRules = totalRules - enabledRules;
  const catCounts = useMemo(() => {
    const counts: Record<string, { total: number; enabled: number }> = {};
    for (const cat of ruleCategories) {
      const catRules = rules.filter((r) => r.category === cat.id);
      counts[cat.id] = { total: catRules.length, enabled: catRules.filter((r) => r.enabled).length };
    }
    return counts;
  }, [rules]);

  const toggleRule = (ruleId: string) => {
    setRules((prev) =>
      prev.map((r) =>
        r.id === ruleId ? { ...r, enabled: !r.enabled, updatedAt: "2026-02-23" } : r
      )
    );
  };

  const deleteRule = (ruleId: string) => {
    setRules((prev) => prev.filter((r) => r.id !== ruleId));
    if (expandedRule === ruleId) setExpandedRule(null);
  };

  const duplicateRule = (rule: Rule) => {
    const newRule: Rule = {
      ...rule,
      id: `r-${Date.now()}`,
      name: `${rule.name} (نسخة)`,
      enabled: false,
      priority: rule.priority + 1,
      createdAt: "2026-02-23",
      updatedAt: "2026-02-23",
    };
    setRules((prev) => [...prev, newRule]);
  };

  const moveRule = (ruleId: string, direction: "up" | "down") => {
    setRules((prev) => {
      const catRules = prev.filter((r) => r.category === activeCategory).sort((a, b) => a.priority - b.priority);
      const idx = catRules.findIndex((r) => r.id === ruleId);
      if (idx < 0) return prev;
      if (direction === "up" && idx === 0) return prev;
      if (direction === "down" && idx === catRules.length - 1) return prev;

      const swapIdx = direction === "up" ? idx - 1 : idx + 1;
      const tempPriority = catRules[idx].priority;
      
      return prev.map((r) => {
        if (r.id === catRules[idx].id) return { ...r, priority: catRules[swapIdx].priority };
        if (r.id === catRules[swapIdx].id) return { ...r, priority: tempPriority };
        return r;
      });
    });
  };

  const addNewRule = () => {
    const catRules = rules.filter((r) => r.category === activeCategory);
    const maxPriority = catRules.length > 0 ? Math.max(...catRules.map((r) => r.priority)) : -1;
    const newRule: Rule = {
      id: `r-new-${Date.now()}`,
      name: "قاعدة جديدة",
      description: "وصف القاعدة الجديدة",
      category: activeCategory,
      enabled: false,
      priority: maxPriority + 1,
      conditionLogic: "AND",
      conditions: [],
      actions: [],
      createdAt: "2026-02-23",
      updatedAt: "2026-02-23",
      createdBy: "أحمد العلي",
      appliesTo: "all",
    };
    setRules((prev) => [...prev, newRule]);
    setExpandedRule(newRule.id);
    setEditingRule(newRule);
  };

  const saveEditingRule = (updated: Rule) => {
    setRules((prev) => prev.map((r) => (r.id === updated.id ? { ...updated, updatedAt: "2026-02-23" } : r)));
    setEditingRule(null);
  };

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">
        {/* Summary Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-primary" />
              <span className="text-xs text-muted-foreground">
                <span className="text-foreground">{totalRules}</span> قاعدة •{" "}
                <span className="text-emerald-500">{enabledRules} مفعّلة</span> •{" "}
                <span className="text-zinc-500">{disabledRules} معطّلة</span>
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                placeholder="بحث في القواعد..."
                className="h-8 text-xs ps-8 w-48"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button
              size="sm"
              className="h-8 text-xs gap-1.5"
              onClick={addNewRule}
            >
              <Plus className="w-3.5 h-3.5" />
              قاعدة جديدة
            </Button>
          </div>
        </div>

        <div className="flex gap-4 min-h-[calc(100vh-380px)]">
          {/* ═══ Category Sidebar ═══ */}
          <div className="w-56 shrink-0 space-y-1">
            {ruleCategories.map((cat) => {
              const CatIcon = iconMap[cat.icon] || Settings2;
              const isActive = activeCategory === cat.id;
              const count = catCounts[cat.id];

              return (
                <button
                  key={cat.id}
                  onClick={() => { setActiveCategory(cat.id); setExpandedRule(null); }}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-start transition-all ${
                    isActive
                      ? "bg-primary/10 dark:bg-primary/15 text-primary border border-primary/20"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/30 border border-transparent"
                  }`}
                >
                  <CatIcon className={`w-4 h-4 shrink-0 ${isActive ? "text-primary" : cat.color}`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs truncate ${isActive ? "text-primary" : ""}`}>{cat.label}</p>
                    <p className="text-[9px] text-muted-foreground">
                      {count.enabled}/{count.total} مفعّلة
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* ═══ Rules Table ═══ */}
          <div className="flex-1 min-w-0">
            {/* Category Header */}
            <Card className="border-border/40 mb-3">
              <CardContent className="p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {(() => {
                    const CatIcon = iconMap[activeCat.icon] || Settings2;
                    return <CatIcon className={`w-5 h-5 ${activeCat.color}`} />;
                  })()}
                  <div>
                    <h4 className="text-sm text-foreground">{activeCat.label}</h4>
                    <p className="text-[10px] text-muted-foreground">{activeCat.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className="bg-emerald-500/10 text-emerald-500 text-[9px] border-transparent">
                    {catCounts[activeCategory].enabled} مفعّلة
                  </Badge>
                  <Badge className="bg-zinc-500/10 text-zinc-500 text-[9px] border-transparent">
                    {catCounts[activeCategory].total - catCounts[activeCategory].enabled} معطّلة
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Rules List */}
            <ScrollArea className="max-h-[calc(100vh-460px)]" dir="rtl">
              <div className="space-y-2">
                <AnimatePresence>
                  {categoryRules.map((rule, index) => (
                    <RuleRow
                      key={rule.id}
                      rule={rule}
                      index={index}
                      isExpanded={expandedRule === rule.id}
                      onToggle={() => setExpandedRule(expandedRule === rule.id ? null : rule.id)}
                      onEnable={() => toggleRule(rule.id)}
                      onDelete={() => deleteRule(rule.id)}
                      onDuplicate={() => duplicateRule(rule)}
                      onEdit={() => setEditingRule(rule)}
                      onMoveUp={() => moveRule(rule.id, "up")}
                      onMoveDown={() => moveRule(rule.id, "down")}
                      isFirst={index === 0}
                      isLast={index === categoryRules.length - 1}
                    />
                  ))}
                </AnimatePresence>

                {categoryRules.length === 0 && (
                  <div className="p-12 text-center">
                    <Settings2 className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
                    <p className="text-xs text-muted-foreground">
                      {searchQuery ? "لا توجد قواعد تطابق البحث" : "لا توجد قواعد في هذه الفئة"}
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-3 text-xs gap-1"
                      onClick={addNewRule}
                    >
                      <Plus className="w-3 h-3" />
                      إضافة قاعدة
                    </Button>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* ═══ Edit Dialog ═══ */}
        {editingRule && (
          <RuleEditDialog
            rule={editingRule}
            onSave={saveEditingRule}
            onClose={() => setEditingRule(null)}
          />
        )}
      </div>
    </TooltipProvider>
  );
}

// ── Rule Row Component ─────────────────────────────────

function RuleRow({
  rule, index, isExpanded, onToggle, onEnable,
  onDelete, onDuplicate, onEdit, onMoveUp, onMoveDown,
  isFirst, isLast,
}: {
  rule: Rule;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
  onEnable: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onEdit: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  isFirst: boolean;
  isLast: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ delay: index * 0.03 }}
    >
      <Card className={`border-border/40 transition-all ${
        !rule.enabled ? "opacity-60" : ""
      } ${isExpanded ? "ring-1 ring-primary/20" : ""}`}>
        {/* ── Row Header ── */}
        <div
          className="flex items-center gap-3 p-3 cursor-pointer hover:bg-muted/10 transition-colors"
          onClick={onToggle}
        >
          {/* Priority/Order Handle */}
          <div className="flex flex-col items-center gap-0.5 shrink-0">
            <button
              onClick={(e) => { e.stopPropagation(); onMoveUp(); }}
              disabled={isFirst}
              className="text-muted-foreground/40 hover:text-foreground disabled:opacity-30 transition-colors"
            >
              <ChevronUp className="w-3 h-3" />
            </button>
            <span className="text-[9px] text-muted-foreground w-5 text-center">{rule.priority}</span>
            <button
              onClick={(e) => { e.stopPropagation(); onMoveDown(); }}
              disabled={isLast}
              className="text-muted-foreground/40 hover:text-foreground disabled:opacity-30 transition-colors"
            >
              <ChevronDown className="w-3 h-3" />
            </button>
          </div>

          {/* Toggle */}
          <div onClick={(e) => e.stopPropagation()} dir="ltr">
            <Switch checked={rule.enabled} onCheckedChange={onEnable} />
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-xs text-foreground truncate">{rule.name}</p>
              {rule.appliesTo && rule.appliesTo !== "all" && (
                <Badge className="text-[8px] bg-muted/30 text-muted-foreground border-transparent h-4 px-1.5">
                  {rule.appliesTo === "agents" ? "وكلاء" : rule.appliesTo === "qa" ? "مدققين" : rule.appliesTo}
                </Badge>
              )}
              {rule.schedule && (
                <Badge className="text-[8px] bg-violet-500/10 text-violet-500 border-transparent h-4 px-1.5">
                  {rule.schedule}
                </Badge>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground truncate mt-0.5">{rule.description}</p>
          </div>

          {/* Meta */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="text-end text-[9px] text-muted-foreground hidden lg:block">
              <p>{rule.conditions.length} شرط</p>
              <p>{rule.actions.length} إجراء</p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary" onClick={onEdit}>
                    <Pencil className="w-3 h-3" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">تعديل</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-blue-500" onClick={onDuplicate}>
                    <Copy className="w-3 h-3" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">نسخ</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-red-500" onClick={onDelete}>
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">حذف</TooltipContent>
              </Tooltip>
            </div>

            {/* Expand Arrow */}
            <motion.div animate={{ rotate: isExpanded ? 90 : 0 }}>
              <ChevronLeft className="w-4 h-4 text-muted-foreground" />
            </motion.div>
          </div>
        </div>

        {/* ── Expanded Detail ── */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <Separator />
              <div className="p-4 space-y-4 bg-muted/5">
                {/* Conditions */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Filter className="w-3.5 h-3.5 text-blue-500" />
                    <span className="text-[10px] text-muted-foreground">الشروط</span>
                    <Badge className="text-[8px] bg-blue-500/10 text-blue-500 border-transparent h-4 px-1.5">
                      {rule.conditionLogic}
                    </Badge>
                  </div>
                  {rule.conditions.length > 0 ? (
                    <div className="space-y-1.5 ps-5">
                      {rule.conditions.map((cond, ci) => (
                        <div key={cond.id} className="flex items-center gap-2 text-xs">
                          <span className="text-foreground">{cond.fieldLabel}</span>
                          <Badge className="text-[8px] bg-muted/40 text-muted-foreground border-transparent h-4 px-1.5">
                            {operatorLabels[cond.operator]}
                          </Badge>
                          <span className="text-primary">
                            {cond.valueLabel || String(cond.value)}
                            {cond.unit && <span className="text-muted-foreground ms-0.5">{cond.unit}</span>}
                          </span>
                          {ci < rule.conditions.length - 1 && (
                            <span className="text-[9px] text-muted-foreground">{rule.conditionLogic === "AND" ? "و" : "أو"}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[10px] text-muted-foreground ps-5">لا توجد شروط (ينطبق دائماً)</p>
                  )}
                </div>

                {/* Actions */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-3.5 h-3.5 text-primary" />
                    <span className="text-[10px] text-muted-foreground">الإجراءات</span>
                  </div>
                  {rule.actions.length > 0 ? (
                    <div className="space-y-1.5 ps-5">
                      {rule.actions.map((action) => (
                        <div key={action.id} className="flex items-center gap-2 text-xs">
                          <ArrowRight className="w-3 h-3 text-muted-foreground shrink-0" />
                          <Badge className="text-[8px] bg-primary/10 text-primary border-transparent h-4 px-1.5">
                            {action.typeLabel}
                          </Badge>
                          <span className="text-foreground">{action.paramsLabel}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[10px] text-muted-foreground ps-5">لا توجد إجراءات</p>
                  )}
                </div>

                {/* Meta */}
                <div className="flex items-center gap-4 text-[9px] text-muted-foreground pt-2 border-t border-border/20">
                  <span>أنشئ: {rule.createdAt}</span>
                  <span>آخر تعديل: {rule.updatedAt}</span>
                  <span>بواسطة: {rule.createdBy}</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}

// ── Rule Edit Dialog ───────────────────────────────────

function RuleEditDialog({
  rule, onSave, onClose,
}: {
  rule: Rule;
  onSave: (rule: Rule) => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState<Rule>({ ...rule });
  const fields = fieldCatalog[form.category] || [];

  const updateField = <K extends keyof Rule>(key: K, value: Rule[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const addCondition = () => {
    const f = fields[0];
    if (!f) return;
    const newCond: RuleCondition = {
      id: `c-${Date.now()}`,
      field: f.value,
      fieldLabel: f.label,
      operator: "equals",
      value: "",
      unit: f.unit,
    };
    updateField("conditions", [...form.conditions, newCond]);
  };

  const removeCondition = (condId: string) => {
    updateField("conditions", form.conditions.filter((c) => c.id !== condId));
  };

  const updateCondition = (condId: string, updates: Partial<RuleCondition>) => {
    updateField(
      "conditions",
      form.conditions.map((c) => (c.id === condId ? { ...c, ...updates } : c))
    );
  };

  const addAction = () => {
    const newAction: RuleAction = {
      id: `a-${Date.now()}`,
      type: "notify",
      typeLabel: actionLabels.notify,
      params: {},
      paramsLabel: "",
    };
    updateField("actions", [...form.actions, newAction]);
  };

  const removeAction = (actionId: string) => {
    updateField("actions", form.actions.filter((a) => a.id !== actionId));
  };

  const updateAction = (actionId: string, updates: Partial<RuleAction>) => {
    updateField(
      "actions",
      form.actions.map((a) => (a.id === actionId ? { ...a, ...updates } : a))
    );
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="!max-w-2xl !p-0 !gap-0 max-h-[85vh] overflow-hidden flex flex-col">
        <DialogTitle className="sr-only">تعديل القاعدة</DialogTitle>
        <DialogDescription className="sr-only">تعديل إعدادات وشروط وإجراءات القاعدة</DialogDescription>

        {/* Header */}
        <div className="px-5 py-4 border-b border-border/30 shrink-0">
          <div className="flex items-center justify-between">
            <h3 className="text-sm text-foreground flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-primary" />
              تعديل القاعدة
            </h3>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" className="h-7 text-xs" onClick={onClose}>
                إلغاء
              </Button>
              <Button size="sm" className="h-7 text-xs gap-1" onClick={() => onSave(form)}>
                <Check className="w-3 h-3" />
                حفظ
              </Button>
            </div>
          </div>
        </div>

        {/* Body */}
        <ScrollArea className="flex-1 min-h-0" dir="rtl">
          <div className="p-5 space-y-5">
            {/* Basic Info */}
            <div className="space-y-3">
              <h4 className="text-xs text-muted-foreground">المعلومات الأساسية</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-muted-foreground mb-1 block">اسم القاعدة</label>
                  <Input
                    className="h-8 text-xs"
                    value={form.name}
                    onChange={(e) => updateField("name", e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-[10px] text-muted-foreground mb-1 block">ينطبق على</label>
                  <Select value={form.appliesTo || "all"} onValueChange={(v) => updateField("appliesTo", v)}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all" className="text-xs">الجميع</SelectItem>
                      <SelectItem value="agents" className="text-xs">وكلاء</SelectItem>
                      <SelectItem value="qa" className="text-xs">مدققين</SelectItem>
                      <SelectItem value="supervisors" className="text-xs">مشرفين</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-[10px] text-muted-foreground mb-1 block">الوصف</label>
                <Input
                  className="h-8 text-xs"
                  value={form.description}
                  onChange={(e) => updateField("description", e.target.value)}
                />
              </div>
            </div>

            <Separator />

            {/* Conditions */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <Filter className="w-3.5 h-3.5 text-blue-500" />
                  الشروط
                </h4>
                <div className="flex items-center gap-2">
                  <Select
                    value={form.conditionLogic}
                    onValueChange={(v: "AND" | "OR") => updateField("conditionLogic", v)}
                  >
                    <SelectTrigger className="h-7 text-[10px] w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="AND" className="text-xs">AND (و)</SelectItem>
                      <SelectItem value="OR" className="text-xs">OR (أو)</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button size="sm" variant="outline" className="h-7 text-[10px] gap-1" onClick={addCondition}>
                    <Plus className="w-3 h-3" />
                    شرط
                  </Button>
                </div>
              </div>

              {form.conditions.length === 0 && (
                <p className="text-[10px] text-muted-foreground p-3 rounded-lg bg-muted/20 text-center">
                  لا توجد شروط — القاعدة ستنطبق دائماً
                </p>
              )}

              {form.conditions.map((cond, ci) => (
                <div key={cond.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted/10 border border-border/30">
                  {/* Field */}
                  <Select
                    value={cond.field}
                    onValueChange={(v) => {
                      const f = fields.find((ff) => ff.value === v);
                      if (f) updateCondition(cond.id, { field: v, fieldLabel: f.label, unit: f.unit });
                    }}
                  >
                    <SelectTrigger className="h-7 text-[10px] w-36">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {fields.map((f) => (
                        <SelectItem key={f.value} value={f.value} className="text-xs">{f.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Operator */}
                  <Select
                    value={cond.operator}
                    onValueChange={(v: ConditionOperator) => updateCondition(cond.id, { operator: v })}
                  >
                    <SelectTrigger className="h-7 text-[10px] w-28">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(operatorLabels).map(([k, v]) => (
                        <SelectItem key={k} value={k} className="text-xs">{v}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Value */}
                  {cond.operator !== "is_true" && cond.operator !== "is_false" && (
                    <Input
                      className="h-7 text-[10px] w-24"
                      value={String(cond.value)}
                      onChange={(e) => updateCondition(cond.id, { value: e.target.value })}
                      placeholder="القيمة"
                    />
                  )}

                  {/* Unit */}
                  {cond.unit && (
                    <span className="text-[9px] text-muted-foreground shrink-0">{cond.unit}</span>
                  )}

                  {/* Remove */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground hover:text-red-500 shrink-0"
                    onClick={() => removeCondition(cond.id)}
                  >
                    <X className="w-3 h-3" />
                  </Button>

                  {/* Logic connector */}
                  {ci < form.conditions.length - 1 && (
                    <span className="text-[9px] text-muted-foreground">{form.conditionLogic === "AND" ? "و" : "أو"}</span>
                  )}
                </div>
              ))}
            </div>

            <Separator />

            {/* Actions */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-primary" />
                  الإجراءات
                </h4>
                <Button size="sm" variant="outline" className="h-7 text-[10px] gap-1" onClick={addAction}>
                  <Plus className="w-3 h-3" />
                  إجراء
                </Button>
              </div>

              {form.actions.length === 0 && (
                <p className="text-[10px] text-muted-foreground p-3 rounded-lg bg-muted/20 text-center">
                  لا توجد إجراءات
                </p>
              )}

              {form.actions.map((action) => (
                <div key={action.id} className="flex items-center gap-2 p-2 rounded-lg bg-muted/10 border border-border/30">
                  {/* Type */}
                  <Select
                    value={action.type}
                    onValueChange={(v: ActionType) => updateAction(action.id, { type: v, typeLabel: actionLabels[v] })}
                  >
                    <SelectTrigger className="h-7 text-[10px] w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(actionLabels).map(([k, v]) => (
                        <SelectItem key={k} value={k} className="text-xs">{v}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Description */}
                  <Input
                    className="h-7 text-[10px] flex-1"
                    value={action.paramsLabel}
                    onChange={(e) => updateAction(action.id, { paramsLabel: e.target.value })}
                    placeholder="وصف الإجراء"
                  />

                  {/* Remove */}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground hover:text-red-500 shrink-0"
                    onClick={() => removeAction(action.id)}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}