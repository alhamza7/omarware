import { useState, useCallback, useMemo, useRef, forwardRef } from "react";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Input } from "./ui/input";
import {
  Sparkles, Package, AlertTriangle, XCircle, Tag,
  MoreHorizontal, Plus, Search, ChevronLeft, ChevronRight,
  Printer, Filter, ChevronDown, X, GlassWater, CircleDot,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import {
  plItems, plBrands, plSections, isItemNew, currencyLabels,
  brandCardSizeRanges,
  type PLItem, type SizeRange,
} from "./price-list/pl-data";

// ─── Product Status (Kanban Stages) ─────────────────────
export type ProductStage = "all" | "new" | "inStock" | "lowStock" | "outOfStock" | "onDiscount";

const stageConfig: Record<Exclude<ProductStage, "all">, {
  label: string;
  color: string;
  bg: string;
  border: string;
  dot: string;
  icon: React.ReactNode;
}> = {
  new: {
    label: "جديد",
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    dot: "bg-emerald-500",
    icon: <Sparkles className="w-3.5 h-3.5" />,
  },
  inStock: {
    label: "متوفر",
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    dot: "bg-blue-500",
    icon: <Package className="w-3.5 h-3.5" />,
  },
  lowStock: {
    label: "مخزون منخفض",
    color: "text-[#B8860B] dark:text-primary",
    bg: "bg-primary/10",
    border: "border-primary/30",
    dot: "bg-[#D4AF37] dark:bg-primary",
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
  },
  outOfStock: {
    label: "نفد المخزون",
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    dot: "bg-red-500",
    icon: <XCircle className="w-3.5 h-3.5" />,
  },
  onDiscount: {
    label: "تخفيض",
    color: "text-purple-600 dark:text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    dot: "bg-purple-500",
    icon: <Tag className="w-3.5 h-3.5" />,
  },
};

const stageOrder: ProductStage[] = ["all", "new", "inStock", "lowStock", "outOfStock", "onDiscount"];

const LOW_STOCK_THRESHOLD = 10;
const NEW_THRESHOLD_DAYS = 60;

function classifyProduct(item: PLItem): Exclude<ProductStage, "all"> {
  if (item.isOnDiscount) return "onDiscount";
  if (!item.inStock || (item.stock !== undefined && item.stock <= 0)) return "outOfStock";
  if (isItemNew(item, NEW_THRESHOLD_DAYS)) return "new";
  if (item.stock !== undefined && item.stock <= LOW_STOCK_THRESHOLD) return "lowStock";
  return "inStock";
}

// ─── Brand lookup ────────────────────────────────────────
const brandMap = new Map(plBrands.map((b) => [b.id, b]));
const sectionMap = new Map(plSections.map((s) => [s.id, s]));

// ─── Kanban Product Card ─────────────────────────────────
const ProductKanbanCard = forwardRef<HTMLDivElement, {
  item: PLItem;
  index: number;
  showSection?: boolean;
}>(function ProductKanbanCard({ item, index, showSection }, ref) {
  const brand = brandMap.get(item.brandId);
  const section = sectionMap.get(item.sectionId);
  const isNew = isItemNew(item, NEW_THRESHOLD_DAYS);
  const stage = classifyProduct(item);
  const stageCfg = stageConfig[stage];

  return (
    <motion.div
      ref={ref}
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2, delay: Math.min(index * 0.02, 0.3) }}
    >
      <Card className="bg-white dark:bg-[#1a1d24] border-slate-150 dark:border-white/[0.06] shadow-sm hover:shadow-md hover:border-primary/30 dark:hover:border-primary/20 transition-all duration-200 cursor-pointer group overflow-hidden h-full">
        <CardContent className="p-3.5">
          {/* Status dot + Section badge */}
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full shrink-0 ${stageCfg.dot}`} />
              <span className={`text-[9px] ${stageCfg.color}`}>{stageCfg.label}</span>
            </div>
            {showSection && section && (
              <Badge variant="outline" className="text-[8px] px-1.5 py-0 text-muted-foreground border-border/40">
                {section.name}
              </Badge>
            )}
          </div>

          {/* Name + Code */}
          <div className="flex items-start justify-between gap-2 mb-2.5">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5 mb-0.5">
                <p className="text-xs font-bold text-foreground truncate group-hover:text-primary transition-colors">
                  {item.name}
                </p>
                {isNew && (
                  <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-[8px] px-1 py-0 shrink-0">
                    جديد
                  </Badge>
                )}
              </div>
              <p className="text-[10px] text-muted-foreground font-mono" dir="ltr">
                {item.itemCode}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-muted-foreground hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              onClick={(e) => { e.stopPropagation(); }}
            >
              <MoreHorizontal className="w-3.5 h-3.5" />
            </Button>
          </div>

          {/* Brand */}
          {brand && (
            <div className="flex items-center gap-1.5 mb-2.5">
              <span
                className="w-5 h-5 rounded flex items-center justify-center shrink-0 text-[6px] tracking-wider"
                style={{
                  backgroundColor: `${brand.color}20`,
                  color: brand.color,
                }}
              >
                {brand.nameEn.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)}
              </span>
              <span className="text-[10px] text-muted-foreground" dir="ltr">
                {brand.nameEn}
              </span>
            </div>
          )}

          {/* Divider */}
          <div className="h-px bg-gradient-to-l from-transparent via-border to-transparent mb-2.5" />

          {/* Price + Stock */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-bold text-primary font-mono">
                {item.price.toLocaleString()}
              </span>
              <span className="text-[9px] text-muted-foreground">
                {currencyLabels[item.currency]}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {item.isOnDiscount && item.discountPct && (
                <Badge className="bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/20 text-[9px] px-1.5 py-0">
                  {item.discountPct}%-
                </Badge>
              )}
              {item.stock !== undefined && (
                <span className={`text-[10px] font-mono ${
                  item.stock <= 0
                    ? "text-red-500"
                    : item.stock <= LOW_STOCK_THRESHOLD
                      ? "text-primary"
                      : "text-muted-foreground"
                }`}>
                  {item.stock <= 0 ? "نفد" : `${item.stock} وحدة`}
                </span>
              )}
            </div>
          </div>

          {/* Size info for glass */}
          {item.sizeML !== undefined && (
            <div className="mt-2 flex items-center gap-2 text-[9px] text-muted-foreground">
              {item.sizeML === "display" ? (
                <span className="bg-muted/50 px-1.5 py-0.5 rounded">زجاج عرض</span>
              ) : (
                <span className="bg-muted/50 px-1.5 py-0.5 rounded font-mono">{item.sizeML}ML</span>
              )}
              {item.glassColor && (
                <span className="bg-muted/50 px-1.5 py-0.5 rounded">
                  {item.glassColor === "transparent" ? "شفاف" : "ملوّن"}
                </span>
              )}
              {item.capType && (
                <span className="bg-muted/50 px-1.5 py-0.5 rounded">
                  {item.capType === "screw" ? "لولبي" : "كبس"}
                </span>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
});
ProductKanbanCard.displayName = "ProductKanbanCard";

// ─── Main Product Kanban Component ───────────────────────
export function ProductKanban() {
  const [activeSection, setActiveSection] = useState("perfumes");
  const [activeBrand, setActiveBrand] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<ProductStage>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const brandScrollRef = useRef<HTMLDivElement>(null);
  const rangeScrollRef = useRef<HTMLDivElement>(null);

  // Glass-specific filters
  const [activeSizeRange, setActiveSizeRange] = useState<string | null>(null);
  const [glassColorFilter, setGlassColorFilter] = useState<"all" | "transparent" | "colored">("all");
  const [capTypeFilter, setCapTypeFilter] = useState<"all" | "screw" | "press">("all");
  const [showGlassFilters, setShowGlassFilters] = useState(false);
  const [showSizeRangeCarousel, setShowSizeRangeCarousel] = useState(true);

  const isGlassSection = activeSection === "oils";

  // Brands for the active section
  const sectionBrands = useMemo(
    () => plBrands.filter((b) => b.sectionId === activeSection),
    [activeSection],
  );

  // All items for current section (before stage filter, for counting)
  const sectionItems = useMemo(
    () => plItems.filter((i) => i.sectionId === activeSection),
    [activeSection],
  );

  // Counts per stage for the current section + brand
  const stageCounts = useMemo(() => {
    let base = sectionItems;
    if (activeBrand) base = base.filter((i) => i.brandId === activeBrand);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      base = base.filter(
        (i) =>
          i.name.includes(searchQuery) ||
          i.nameEn.toLowerCase().includes(q) ||
          i.itemCode.toLowerCase().includes(q),
      );
    }

    const counts: Record<ProductStage, number> = {
      all: base.length,
      new: 0,
      inStock: 0,
      lowStock: 0,
      outOfStock: 0,
      onDiscount: 0,
    };
    base.forEach((item) => {
      counts[classifyProduct(item)]++;
    });
    return counts;
  }, [sectionItems, activeBrand, searchQuery]);

  // Filtered items
  const filteredItems = useMemo(() => {
    let items = sectionItems;
    if (activeBrand) items = items.filter((i) => i.brandId === activeBrand);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (i) =>
          i.name.includes(searchQuery) ||
          i.nameEn.toLowerCase().includes(q) ||
          i.itemCode.toLowerCase().includes(q),
      );
    }
    if (activeStage !== "all") {
      items = items.filter((i) => classifyProduct(i) === activeStage);
    }
    if (isGlassSection) {
      if (activeSizeRange) {
        if (activeSizeRange === "r-display") {
          items = items.filter((i) => i.sizeML === "display");
        } else {
          const range = brandCardSizeRanges.find((r) => r.id === activeSizeRange);
          if (range) {
            items = items.filter((i) => {
              if (typeof i.sizeML !== "number") return false;
              return i.sizeML >= range.min && (range.max === null || i.sizeML <= range.max);
            });
          }
        }
      }
      if (glassColorFilter !== "all") {
        items = items.filter((i) => i.glassColor === glassColorFilter);
      }
      if (capTypeFilter !== "all") {
        items = items.filter((i) => i.capType === capTypeFilter);
      }
    }
    return items;
  }, [sectionItems, activeBrand, searchQuery, activeStage, isGlassSection, activeSizeRange, glassColorFilter, capTypeFilter]);

  // Total value
  const totalValue = filteredItems.reduce((sum, i) => sum + i.price, 0);

  // Scroll brand carousel
  const scrollBrands = (dir: "start" | "end") => {
    if (!brandScrollRef.current) return;
    const amount = dir === "start" ? -240 : 240;
    brandScrollRef.current.scrollBy({ left: -amount, behavior: "smooth" });
  };

  // Scroll size range carousel
  const scrollRanges = (dir: "start" | "end") => {
    if (!rangeScrollRef.current) return;
    const amount = dir === "start" ? -240 : 240;
    rangeScrollRef.current.scrollBy({ left: -amount, behavior: "smooth" });
  };

  return (
    <div className="flex gap-0 min-h-[calc(100vh-220px)]">
      {/* ═══ Sections Sidebar ═══ */}
      <div className="w-44 shrink-0 border-e border-border/40 bg-card/30 dark:bg-[#0d0f12]/60">
        <div className="px-3 py-3 border-b border-border/30">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
            الأقسام
          </span>
        </div>
        <nav className="flex flex-col gap-0.5 p-2">
          {plSections.map((section) => {
            const isActive = activeSection === section.id;
            const sectionItemCount = plItems.filter(
              (i) => i.sectionId === section.id,
            ).length;

            return (
              <button
                key={section.id}
                onClick={() => {
                  setActiveSection(section.id);
                  setActiveBrand(null);
                  setSearchQuery("");
                  setActiveStage("all");
                  setActiveSizeRange(null);
                  setGlassColorFilter("all");
                  setCapTypeFilter("all");
                  setShowGlassFilters(false);
                }}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-start transition-all ${
                  isActive
                    ? "bg-primary/10 dark:bg-primary/15 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
                }`}
              >
                <span className={`text-xs ${isActive ? "text-primary" : ""}`}>
                  {section.name}
                </span>
                <span className="text-[9px] text-muted-foreground">
                  {sectionItemCount}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* ═══ Main Content ═══ */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* ── Header Bar ── */}
        <div className="shrink-0 px-5 py-4 border-b border-border/30 bg-card/20">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg text-foreground flex items-center gap-2">
                <Package className="w-5 h-5 text-primary" />
                كانبان المنتجات
              </h3>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                {plSections.find((s) => s.id === activeSection)?.name}  {filteredItems.length} منتج
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* Search */}
              <div className="relative">
                <Search className="absolute end-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <Input
                  placeholder="بحث..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-8 text-xs pe-8 ps-3 w-48 bg-secondary/30 border-border/40"
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs gap-1.5"
              >
                <Printer className="w-3.5 h-3.5" />
                طباعة
              </Button>
            </div>
          </div>
        </div>

        {/* ── Brand Selector Carousel ── */}
        <div className="shrink-0 px-5 py-3 border-b border-border/20">
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-muted-foreground shrink-0">
              العلامات:
            </span>

            <button
              onClick={() => setActiveBrand(null)}
              className={`shrink-0 px-4 py-2 rounded-lg border text-xs transition-all ${
                activeBrand === null
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border/40 text-muted-foreground hover:border-primary/30 hover:text-foreground"
              }`}
            >
              الكل
            </button>

            {sectionBrands.length > 4 && (
              <button
                onClick={() => scrollBrands("start")}
                className="shrink-0 w-7 h-7 rounded-full bg-muted/30 hover:bg-muted/50 flex items-center justify-center text-muted-foreground transition-colors"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}

            <div
              ref={brandScrollRef}
              className="flex gap-2 overflow-x-auto scrollbar-none scroll-smooth flex-1"
              style={{ scrollbarWidth: "none" }}
            >
              {sectionBrands.map((brand) => {
                const isActive = activeBrand === brand.id;
                const brandItemCount = plItems.filter(
                  (i) => i.brandId === brand.id && i.sectionId === activeSection,
                ).length;

                return (
                  <button
                    key={brand.id}
                    onClick={() => setActiveBrand(isActive ? null : brand.id)}
                    className={`shrink-0 flex items-center gap-2 px-3 py-2 rounded-lg border text-xs transition-all ${
                      isActive
                        ? "border-primary bg-primary/10 text-primary shadow-sm"
                        : "border-border/40 text-muted-foreground hover:border-primary/30 hover:text-foreground"
                    }`}
                  >
                    <span
                      className="w-5 h-5 rounded flex items-center justify-center shrink-0 text-[7px] tracking-wider"
                      style={{
                        backgroundColor: `${brand.color}20`,
                        color: brand.color,
                      }}
                    >
                      {brand.nameEn.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)}
                    </span>
                    <span>{brand.name}</span>
                    <span className="text-[9px] text-muted-foreground/60">{brandItemCount}</span>
                  </button>
                );
              })}
            </div>

            {sectionBrands.length > 4 && (
              <button
                onClick={() => scrollBrands("end")}
                className="shrink-0 w-7 h-7 rounded-full bg-muted/30 hover:bg-muted/50 flex items-center justify-center text-muted-foreground transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* ── Glass-specific Filters (Size Range + Color + Cap) ── */}
        <AnimatePresence>
          {isGlassSection && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className="shrink-0 overflow-hidden border-b border-border/20"
            >
              {/* Size Range Carousel */}
              <div className="px-5 py-3 border-b border-border/10">
                {/* Toggle header */}
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => setShowSizeRangeCarousel((prev) => !prev)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setShowSizeRangeCarousel((prev) => !prev);
                    }
                  }}
                  className="flex items-center gap-2 cursor-pointer select-none rounded-md py-1.5 px-1 hover:bg-muted/20 transition-colors"
                >
                  <CircleDot className="w-3.5 h-3.5 text-primary shrink-0" />
                  <span className="text-[10px] text-muted-foreground">
                    نطاق الحجم
                  </span>
                  {activeSizeRange != null && !showSizeRangeCarousel && (
                    <Badge className="bg-primary/15 text-primary text-[8px] border-primary/20 h-4 px-1.5">
                      فلتر نشط
                    </Badge>
                  )}
                  <ChevronDown
                    className={`w-3.5 h-3.5 text-muted-foreground transition-transform duration-300 ${
                      showSizeRangeCarousel ? "rotate-180" : ""
                    }`}
                  />
                </div>

                {/* Collapsible content */}
                <div
                  className="grid transition-[grid-template-rows,opacity] duration-300 ease-in-out"
                  style={{
                    gridTemplateRows: showSizeRangeCarousel ? "1fr" : "0fr",
                    opacity: showSizeRangeCarousel ? 1 : 0,
                  }}
                >
                  <div className="overflow-hidden">
                    <div className="flex items-center gap-3 pt-2 pb-1">
                      <span className="text-[10px] text-muted-foreground shrink-0">
                        نطاق الحجم:
                      </span>
                      <button
                        onClick={(e) => { e.stopPropagation(); scrollRanges("start"); }}
                        className="shrink-0 w-7 h-7 rounded-full bg-muted/30 hover:bg-muted/50 flex items-center justify-center text-muted-foreground transition-colors"
                      >
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => setActiveSizeRange(null)}
                        className={`shrink-0 px-4 py-2 rounded-lg border text-xs transition-all ${
                          activeSizeRange === null
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border/40 text-muted-foreground hover:border-primary/30 hover:text-foreground"
                        }`}
                      >
                        الكل
                      </button>

                      <div
                        ref={rangeScrollRef}
                        className="flex gap-2 overflow-x-auto scrollbar-none scroll-smooth flex-1"
                        style={{ scrollbarWidth: "none" }}
                      >
                        {brandCardSizeRanges.map((range) => {
                          const isActive = activeSizeRange === range.id;
                          const matchCount = plItems.filter((i) => {
                            if (i.sectionId !== "oils") return false;
                            if (typeof i.sizeML !== "number") return false;
                            return i.sizeML >= range.min && (range.max === null || i.sizeML <= range.max);
                          }).length;

                          return (
                            <motion.button
                              key={range.id}
                              onClick={() => setActiveSizeRange(isActive ? null : range.id)}
                              disabled={matchCount === 0}
                              className={`shrink-0 flex items-center gap-2.5 px-3.5 py-2 rounded-xl border transition-all ${
                                isActive
                                  ? "border-primary bg-primary/5 dark:bg-primary/10 shadow-sm shadow-primary/10"
                                  : matchCount > 0
                                    ? "border-border/40 bg-card/40 hover:border-primary/30 hover:bg-card/60"
                                    : "border-border/20 bg-card/10 opacity-35 cursor-default"
                              }`}
                              whileHover={matchCount > 0 ? { y: -1 } : undefined}
                              whileTap={matchCount > 0 ? { scale: 0.98 } : undefined}
                            >
                              <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                                isActive ? "bg-primary/15 text-primary" : "bg-muted/30 text-muted-foreground"
                              }`}>
                                <CircleDot className="w-3.5 h-3.5" />
                              </div>
                              <div className="flex flex-col items-start gap-0.5 min-w-0">
                                <span
                                  className={`text-[11px] whitespace-nowrap ${isActive ? "text-primary" : "text-foreground"}`}
                                  style={{ direction: "ltr", unicodeBidi: "embed" }}
                                >
                                  {range.label} ML
                                </span>
                                <span className={`text-[8px] ${isActive ? "text-primary/70" : "text-muted-foreground"}`}>
                                  {matchCount} منتج
                                </span>
                              </div>
                            </motion.button>
                          );
                        })}

                        {/* Display glass card */}
                        {(() => {
                          const isActive = activeSizeRange === "r-display";
                          const matchCount = plItems.filter(
                            (i) => i.sectionId === "oils" && i.sizeML === "display",
                          ).length;
                          return matchCount > 0 ? (
                            <motion.button
                              key="r-display"
                              onClick={() => setActiveSizeRange(isActive ? null : "r-display")}
                              className={`shrink-0 flex items-center gap-2.5 px-3.5 py-2 rounded-xl border transition-all ${
                                isActive
                                  ? "border-violet-500 bg-violet-500/10 dark:bg-violet-500/15 shadow-sm shadow-violet-500/10"
                                  : "border-border/40 bg-card/40 hover:border-primary/30 hover:bg-card/60"
                              }`}
                              whileHover={{ y: -1 }}
                              whileTap={{ scale: 0.98 }}
                            >
                              <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                                isActive ? "bg-violet-500/20 text-violet-500" : "bg-muted/30 text-muted-foreground"
                              }`}>
                                <GlassWater className="w-3.5 h-3.5" />
                              </div>
                              <div className="flex flex-col items-start gap-0.5 min-w-0">
                                <span className={`text-[11px] whitespace-nowrap ${isActive ? "text-violet-500" : "text-foreground"}`}>
                                  زجاج عرض
                                </span>
                                <span className={`text-[8px] ${isActive ? "text-violet-500/70" : "text-muted-foreground"}`}>
                                  {matchCount} منتج
                                </span>
                              </div>
                            </motion.button>
                          ) : null;
                        })()}
                      </div>

                      <button
                        onClick={() => scrollRanges("end")}
                        className="shrink-0 w-7 h-7 rounded-full bg-muted/30 hover:bg-muted/50 flex items-center justify-center text-muted-foreground transition-colors"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Glass Color + Cap Type Filters */}
              <div className="px-5 py-3">
                <div className="flex items-center gap-2 mb-0">
                  <button
                    onClick={() => setShowGlassFilters((p) => !p)}
                    className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
                  >
                    <GlassWater className="w-3.5 h-3.5 text-primary" />
                    <span className="text-[10px] text-muted-foreground">
                      نوع الزجاج والغطاء
                    </span>
                    <ChevronDown
                      className={`w-3 h-3 text-muted-foreground transition-transform duration-200 ${showGlassFilters ? "rotate-180" : ""}`}
                    />
                  </button>
                  {(glassColorFilter !== "all" || capTypeFilter !== "all") && (
                    <button
                      onClick={() => { setGlassColorFilter("all"); setCapTypeFilter("all"); }}
                      className="text-[9px] text-primary hover:text-primary/80 transition-colors flex items-center gap-0.5 ms-1"
                    >
                      <X className="w-2.5 h-2.5" />
                      مسح الكل
                    </button>
                  )}
                </div>
                <AnimatePresence>
                  {showGlassFilters && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ type: "spring", stiffness: 400, damping: 30 }}
                      className="overflow-hidden"
                    >
                      <div className="pt-2">
                        <div className="flex items-center gap-4 flex-wrap">
                          {/* Glass Color */}
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-muted-foreground shrink-0">نوع الزجاج:</span>
                            <button
                              onClick={() => setGlassColorFilter("all")}
                              className={`px-3 py-2 rounded-xl border text-[10px] transition-all ${
                                glassColorFilter === "all"
                                  ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                                  : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                              }`}
                            >
                              الكل
                              <span className="text-[8px] ms-1 opacity-60">
                                ({plItems.filter((i) => i.sectionId === "oils").length})
                              </span>
                            </button>
                            <button
                              onClick={() => setGlassColorFilter(glassColorFilter === "transparent" ? "all" : "transparent")}
                              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] transition-all ${
                                glassColorFilter === "transparent"
                                  ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                                  : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                              }`}
                            >
                              <span
                                className="w-4 h-4 rounded-full shrink-0 border"
                                style={{
                                  background: "linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.03))",
                                  borderColor: glassColorFilter === "transparent" ? "var(--color-primary)" : "var(--border)",
                                }}
                              />
                              شفاف
                              <span className="text-[8px] opacity-60">
                                ({plItems.filter((i) => i.sectionId === "oils" && i.glassColor === "transparent").length})
                              </span>
                            </button>
                            <button
                              onClick={() => setGlassColorFilter(glassColorFilter === "colored" ? "all" : "colored")}
                              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] transition-all ${
                                glassColorFilter === "colored"
                                  ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                                  : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                              }`}
                            >
                              <span
                                className="w-4 h-4 rounded-full shrink-0"
                                style={{ background: "linear-gradient(135deg, var(--primary), var(--gold-dark))" }}
                              />
                              ملوّن
                              <span className="text-[8px] opacity-60">
                                ({plItems.filter((i) => i.sectionId === "oils" && i.glassColor === "colored").length})
                              </span>
                            </button>
                          </div>

                          {/* Separator */}
                          <div className="w-px h-6 bg-border/30 shrink-0" />

                          {/* Cap Type */}
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-muted-foreground shrink-0">نوع الغطاء:</span>
                            <button
                              onClick={() => setCapTypeFilter("all")}
                              className={`px-3 py-2 rounded-xl border text-[10px] transition-all ${
                                capTypeFilter === "all"
                                  ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                                  : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                              }`}
                            >
                              الكل
                              <span className="text-[8px] ms-1 opacity-60">
                                ({plItems.filter((i) => i.sectionId === "oils").length})
                              </span>
                            </button>
                            <button
                              onClick={() => setCapTypeFilter(capTypeFilter === "screw" ? "all" : "screw")}
                              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] transition-all ${
                                capTypeFilter === "screw"
                                  ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                                  : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                              }`}
                            >
                              <svg width="16" height="16" viewBox="0 0 20 20" fill="none" className="shrink-0">
                                <circle cx="10" cy="7" r="4" stroke="currentColor" strokeWidth="1.2" strokeDasharray="2.5 1.5" />
                                <rect x="7.5" y="3" width="5" height="3.5" rx="1" fill="currentColor" fillOpacity="0.25" stroke="currentColor" strokeWidth="0.8" />
                                <path d="M8.5 11v5M11.5 11v5M10 11v5.5" stroke="currentColor" strokeWidth="0.6" strokeLinecap="round" opacity="0.4" />
                              </svg>
                              لولبي
                              <span className="text-[8px] opacity-60">
                                ({plItems.filter((i) => i.sectionId === "oils" && i.capType === "screw").length})
                              </span>
                            </button>
                            <button
                              onClick={() => setCapTypeFilter(capTypeFilter === "press" ? "all" : "press")}
                              className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] transition-all ${
                                capTypeFilter === "press"
                                  ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                                  : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                              }`}
                            >
                              <svg width="16" height="16" viewBox="0 0 20 20" fill="none" className="shrink-0">
                                <rect x="6.5" y="3" width="7" height="4.5" rx="1.2" fill="currentColor" fillOpacity="0.25" stroke="currentColor" strokeWidth="0.8" />
                                <path d="M10 1v2.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
                                <path d="M8 1.5l2 2 2-2" stroke="currentColor" strokeWidth="0.7" fill="none" />
                                <rect x="7.5" y="7.5" width="5" height="9" rx="0.8" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.4" />
                              </svg>
                              كبس
                              <span className="text-[8px] opacity-60">
                                ({plItems.filter((i) => i.sectionId === "oils" && i.capType === "press").length})
                              </span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Status Tabs (Kanban Stages) ── */}
        <div className="shrink-0 px-5 py-3 border-b border-border/20">
          <div className="flex items-center gap-2 overflow-x-auto" style={{ scrollbarWidth: "none" }}>
            {/* "الكل" tab */}
            <button
              onClick={() => setActiveStage("all")}
              className={`shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl border text-xs transition-all ${
                activeStage === "all"
                  ? "border-primary bg-primary/10 text-primary shadow-sm"
                  : "border-border/40 text-muted-foreground hover:border-primary/30 hover:text-foreground bg-card/30"
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              الكل
              <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full min-w-[20px] text-center ${
                activeStage === "all" ? "bg-primary/20 text-primary" : "bg-white/60 dark:bg-white/10 text-muted-foreground"
              }`}>
                {stageCounts.all}
              </span>
            </button>

            {/* Stage tabs */}
            {(["new", "inStock", "lowStock", "outOfStock", "onDiscount"] as const).map((stage) => {
              const cfg = stageConfig[stage];
              const count = stageCounts[stage];
              const isActive = activeStage === stage;

              return (
                <button
                  key={stage}
                  onClick={() => setActiveStage(isActive ? "all" : stage)}
                  className={`shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl border text-xs transition-all ${
                    isActive
                      ? `${cfg.border} ${cfg.bg} ${cfg.color} shadow-sm`
                      : "border-border/40 text-muted-foreground hover:border-primary/30 hover:text-foreground bg-card/30"
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                  <span className={isActive ? cfg.color : ""}>{cfg.icon}</span>
                  <span>{cfg.label}</span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full min-w-[20px] text-center ${
                    isActive ? `${cfg.bg} ${cfg.color}` : "bg-white/60 dark:bg-white/10 text-muted-foreground"
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Summary Bar ── */}
        <div className="shrink-0 px-5 py-2 border-b border-border/10 bg-muted/10 flex items-center justify-between">
          <p className="text-[10px] text-muted-foreground">
            عرض <span className="font-mono font-bold text-foreground">{filteredItems.length}</span> منتج
            {activeStage !== "all" && (
              <span> · الحالة: <span className={stageConfig[activeStage as Exclude<ProductStage, "all">]?.color}>{stageConfig[activeStage as Exclude<ProductStage, "all">]?.label}</span></span>
            )}
          </p>
          <p className="text-[10px] text-muted-foreground">
            الإجمالي: <span className="font-mono font-bold text-primary">{totalValue.toLocaleString()}</span>
          </p>
        </div>

        {/* ── Cards Grid ── */}
        <ScrollArea className="flex-1 min-h-0" dir="rtl">
          <div className="p-5">
            {filteredItems.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3">
                <AnimatePresence mode="popLayout">
                  {filteredItems.map((item, i) => (
                    <ProductKanbanCard
                      key={item.id}
                      item={item}
                      index={i}
                      showSection={false}
                    />
                  ))}
                </AnimatePresence>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-muted/30 flex items-center justify-center mb-4">
                  <Package className="w-8 h-8 text-muted-foreground/40" />
                </div>
                <p className="text-sm text-muted-foreground">لا توجد منتجات</p>
                <p className="text-[11px] text-muted-foreground/60 mt-1">
                  جرّب تغيير الفلاتر أو البحث
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}