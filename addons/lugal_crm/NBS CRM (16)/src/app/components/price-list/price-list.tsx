import { useState, useMemo, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Search, Printer, Plus, ChevronLeft, ChevronRight,
  Sparkles, Package, Filter, X, Check, List, LayoutGrid, Tag, AlertTriangle,
  GlassWater, CircleDot, ChevronDown,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import {
  Table, TableBody, TableCell, TableHead,
  TableHeader, TableRow,
} from "../ui/table";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";
import {
  plSections, plBrands, plItems,
  isItemNew, sortItemsWithNewFirst,
  currencyLabels, unitLabels,
  defaultGlassSizeFilters,
  loadCustomGlassFilters, saveCustomGlassFilters,
  getBrandSizeRanges,
  brandCardSizeRanges,
  type PLBrand, type PLSizeFilter, type SizeRange,
} from "./pl-data";

// ── "New item threshold" — driven by Rule Engine config ──

function getNewItemThreshold(): number {
  try {
    const stored = localStorage.getItem("pl_new_item_days");
    if (stored) return Number(stored);
  } catch { /* ignore */ }
  return 60;
}

// ── Size label helper (module-level for use in table + BrandCard) ──

function getSizeLabel(sizeML: number | "display" | undefined): string {
  if (sizeML === undefined) return "—";
  if (sizeML === "display") return "زجاج عرض";
  return `${sizeML}ML`;
}

// ── Main Component ─────────────────────────────────────

export function PriceList() {
  const [activeSection, setActiveSection] = useState("perfumes");
  const [activeBrand, setActiveBrand] = useState<string | null>(null);
  const [activeSizeRange, setActiveSizeRange] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [newThreshold] = useState(getNewItemThreshold);
  const brandScrollRef = useRef<HTMLDivElement>(null);
  const rangeScrollRef = useRef<HTMLDivElement>(null);

  // ── Glass size filters state ──
  const [activeSizeFilters, setActiveSizeFilters] = useState<Set<string>>(new Set());
  const [customFilters, setCustomFilters] = useState<PLSizeFilter[]>(loadCustomGlassFilters);
  const [showAddFilter, setShowAddFilter] = useState(false);
  const [newFilterInput, setNewFilterInput] = useState("");
  const addFilterRef = useRef<HTMLInputElement>(null);

  // ── Glass color + cap type filters ──
  const [glassColorFilter, setGlassColorFilter] = useState<"all" | "transparent" | "colored">("all");
  const [capTypeFilter, setCapTypeFilter] = useState<"all" | "screw" | "press">("all");

  // ── Collapsible filter toggles ──
  const [showSizeFilter, setShowSizeFilter] = useState(false);
  const [showGlassColorCapFilter, setShowGlassColorCapFilter] = useState(false);
  const [showSizeRangeCarousel, setShowSizeRangeCarousel] = useState(true);

  const isGlassSection = activeSection === "oils";

  // All available glass filters (built-in + custom)
  const allGlassFilters = useMemo(
    () => [...defaultGlassSizeFilters, ...customFilters],
    [customFilters],
  );

  // Toggle a size filter
  const toggleSizeFilter = useCallback((filterId: string) => {
    setActiveSizeFilters((prev) => {
      const next = new Set(prev);
      if (next.has(filterId)) next.delete(filterId);
      else next.add(filterId);
      return next;
    });
  }, []);

  // Clear all size filters
  const clearSizeFilters = useCallback(() => {
    setActiveSizeFilters(new Set());
  }, []);

  // Add a new custom filter
  const handleAddCustomFilter = useCallback(() => {
    const raw = newFilterInput.trim();
    if (!raw) return;

    // Check if it's "عرض" or "display"
    const isDisplay = raw === "عرض" || raw.toLowerCase() === "display";
    const numVal = isDisplay ? NaN : Number(raw.replace(/[^\d.]/g, ""));

    if (!isDisplay && (isNaN(numVal) || numVal <= 0)) return;

    const id = `sz-custom-${Date.now()}`;
    const value: number | "display" = isDisplay ? "display" : numVal;

    // Check for duplicates
    const exists = allGlassFilters.some((f) => f.value === value);
    if (exists) { setNewFilterInput(""); setShowAddFilter(false); return; }

    const label = isDisplay ? "زجاج عرض (مخصص)" : `${numVal}ML`;
    const newFilter: PLSizeFilter = { id, label, value, isCustom: true };

    const updated = [...customFilters, newFilter];
    setCustomFilters(updated);
    saveCustomGlassFilters(updated);
    setNewFilterInput("");
    setShowAddFilter(false);
  }, [newFilterInput, customFilters, allGlassFilters]);

  // Remove a custom filter
  const removeCustomFilter = useCallback((filterId: string) => {
    const updated = customFilters.filter((f) => f.id !== filterId);
    setCustomFilters(updated);
    saveCustomGlassFilters(updated);
    setActiveSizeFilters((prev) => {
      const next = new Set(prev);
      next.delete(filterId);
      return next;
    });
  }, [customFilters]);

  // Brands for the active section
  const sectionBrands = useMemo(
    () => plBrands.filter((b) => b.sectionId === activeSection),
    [activeSection],
  );

  // Items filtered by section + brand + search + size
  const filteredItems = useMemo(() => {
    let items = plItems.filter((i) => i.sectionId === activeSection);
    if (activeBrand) {
      items = items.filter((i) => i.brandId === activeBrand);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (i) =>
          i.name.includes(searchQuery) ||
          i.nameEn.toLowerCase().includes(q) ||
          i.itemCode.toLowerCase().includes(q),
      );
    }
    // Glass size range filtering (from carousel cards)
    if (isGlassSection && activeSizeRange) {
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
    // Glass size filtering (from collapsible filter chips)
    if (isGlassSection && activeSizeFilters.size > 0) {
      const selectedValues = new Set(
        allGlassFilters
          .filter((f) => activeSizeFilters.has(f.id))
          .map((f) => f.value),
      );
      items = items.filter((i) => i.sizeML !== undefined && selectedValues.has(i.sizeML));
    }
    // Glass color filtering
    if (isGlassSection && glassColorFilter !== "all") {
      items = items.filter((i) => i.glassColor === glassColorFilter);
    }
    // Cap type filtering
    if (isGlassSection && capTypeFilter !== "all") {
      items = items.filter((i) => i.capType === capTypeFilter);
    }
    return sortItemsWithNewFirst(items, newThreshold);
  }, [activeSection, activeBrand, activeSizeRange, searchQuery, newThreshold, isGlassSection, activeSizeFilters, allGlassFilters, glassColorFilter, capTypeFilter]);

  const activeSectionData = plSections.find((s) => s.id === activeSection)!;
  const activeBrandData = activeBrand
    ? plBrands.find((b) => b.id === activeBrand)
    : null;

  const totalItems = filteredItems.length;
  const newItems = filteredItems.filter((i) => isItemNew(i, newThreshold)).length;

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

  const tableColSpan = isGlassSection ? 9 : 6;

  return (
    <TooltipProvider delayDuration={200}>
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
                    setActiveSizeRange(null);
                    setSearchQuery("");
                    setActiveSizeFilters(new Set());
                    setGlassColorFilter("all");
                    setCapTypeFilter("all");
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
                  قائمة الأسعار
                </h3>
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  {activeSectionData.name}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 text-xs gap-1.5"
                >
                  <Printer className="w-3.5 h-3.5" />
                  طباعة
                </Button>
                <Button size="sm" className="h-8 text-xs gap-1.5">
                  <Plus className="w-3.5 h-3.5" />
                  إضافة قسم
                </Button>
              </div>
            </div>
          </div>

          {/* ── Brand Selector Carousel (non-glass) / Size Range Cards (glass) ── */}
          <div className="shrink-0 px-5 py-3 border-b border-border/20">
            {isGlassSection ? (
              /* ━━━ Glass: Size Range Cards (collapsible) ━━━ */
              <div className="flex flex-col">
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

                {/* Collapsible content via CSS grid trick */}
                <div
                  className="grid transition-[grid-template-rows,opacity] duration-300 ease-in-out"
                  style={{
                    gridTemplateRows: showSizeRangeCarousel ? "1fr" : "0fr",
                    opacity: showSizeRangeCarousel ? 1 : 0,
                  }}
                >
                  <div className="overflow-hidden">
                    <div className="flex items-center gap-3 pt-2 pb-1">
                      <button
                        onClick={() => scrollRanges("start")}
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
                          const newCount = plItems.filter((i) => {
                            if (i.sectionId !== "oils") return false;
                            if (typeof i.sizeML !== "number") return false;
                            if (!(i.sizeML >= range.min && (range.max === null || i.sizeML <= range.max))) return false;
                            return isItemNew(i, newThreshold);
                          }).length;

                          return (
                            <SizeRangeCard
                              key={range.id}
                              range={range}
                              isActive={isActive}
                              itemCount={matchCount}
                              newCount={newCount}
                              onClick={() =>
                                setActiveSizeRange(isActive ? null : range.id)
                              }
                            />
                          );
                        })}

                        {/* Display glass card */}
                        {(() => {
                          const isActive = activeSizeRange === "r-display";
                          const matchCount = plItems.filter(
                            (i) => i.sectionId === "oils" && i.sizeML === "display",
                          ).length;
                          return matchCount > 0 ? (
                            <SizeRangeCard
                              key="r-display"
                              range={{ id: "r-display", label: "عرض", min: 0, max: null }}
                              isActive={isActive}
                              itemCount={matchCount}
                              newCount={0}
                              isDisplay
                              onClick={() =>
                                setActiveSizeRange(isActive ? null : "r-display")
                              }
                            />
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
            ) : (
              /* ━━━ Non-glass: Brand Cards ━━━ */
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
                  className="flex gap-2 overflow-x-auto scrollbar-none scroll-smooth"
                  style={{ scrollbarWidth: "none" }}
                >
                  {sectionBrands.map((brand) => {
                    const isActive = activeBrand === brand.id;
                    const brandItems = plItems.filter(
                      (i) =>
                        i.brandId === brand.id && i.sectionId === activeSection,
                    );
                    const brandItemCount = brandItems.length;
                    const brandNewCount = brandItems.filter(
                      (i) => isItemNew(i, newThreshold),
                    ).length;

                    return (
                      <BrandCard
                        key={brand.id}
                        brand={brand}
                        isActive={isActive}
                        itemCount={brandItemCount}
                        newCount={brandNewCount}
                        isGlass={false}
                        availableSizes={[]}
                        onClick={() =>
                          setActiveBrand(isActive ? null : brand.id)
                        }
                      />
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
            )}
          </div>

          {/* ── Glass Size Filters (only for زجاج section) ── */}
          <AnimatePresence>
            {isGlassSection && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
                className="shrink-0 overflow-hidden border-b border-border/20"
              >
                <div className="px-5 py-3">
                  <div className="flex items-center gap-2 mb-0">
                    <button
                      onClick={() => setShowSizeFilter((p) => !p)}
                      className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
                    >
                      <Filter className="w-3.5 h-3.5 text-primary" />
                      <span className="text-[10px] text-muted-foreground">
                        فلتر الحجم
                      </span>
                      <ChevronDown
                        className={`w-3 h-3 text-muted-foreground transition-transform duration-200 ${showSizeFilter ? "rotate-180" : ""}`}
                      />
                    </button>
                    {activeSizeFilters.size > 0 && (
                      <button
                        onClick={clearSizeFilters}
                        className="text-[9px] text-primary hover:text-primary/80 transition-colors flex items-center gap-0.5 ms-1"
                      >
                        <X className="w-2.5 h-2.5" />
                        مسح الكل
                      </button>
                    )}
                    {activeSizeFilters.size > 0 && (
                      <Badge className="bg-primary/15 text-primary text-[8px] border-primary/20 h-4 px-1.5 ms-auto">
                        {activeSizeFilters.size} محدد
                      </Badge>
                    )}
                  </div>
                  <AnimatePresence>
                    {showSizeFilter && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ type: "spring", stiffness: 400, damping: 30 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-2">
                  <ScrollArea dir="rtl" className="w-full">
                    <div className="flex items-center gap-1.5 pb-1">
                      {allGlassFilters.map((filter) => {
                        const isActive = activeSizeFilters.has(filter.id);
                        const matchCount = plItems.filter(
                          (i) =>
                            i.sectionId === "oils" &&
                            i.sizeML === filter.value &&
                            (activeBrand ? i.brandId === activeBrand : true),
                        ).length;

                        return (
                          <button
                            key={filter.id}
                            onClick={() => toggleSizeFilter(filter.id)}
                            className={`group shrink-0 relative flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-[10px] transition-all ${
                              isActive
                                ? "border-primary bg-primary/10 dark:bg-primary/15 text-primary shadow-sm shadow-primary/5"
                                : matchCount > 0
                                  ? "border-border/40 text-muted-foreground hover:border-primary/30 hover:text-foreground bg-card/30"
                                  : "border-border/20 text-muted-foreground/40 bg-card/10 cursor-default"
                            }`}
                            disabled={matchCount === 0}
                          >
                            {isActive && (
                              <Check className="w-2.5 h-2.5 text-primary" />
                            )}
                            <span
                              style={
                                typeof filter.value === "number"
                                  ? { direction: "ltr" as const, unicodeBidi: "embed" as const }
                                  : undefined
                              }
                            >
                              {filter.label}
                            </span>
                            {matchCount > 0 && (
                              <span className={`text-[8px] ${isActive ? "text-primary/70" : "text-muted-foreground/50"}`}>
                                ({matchCount})
                              </span>
                            )}
                            {/* Remove button for custom filters */}
                            {filter.isCustom && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  removeCustomFilter(filter.id);
                                }}
                                className="opacity-0 group-hover:opacity-100 absolute -top-1.5 -start-1.5 w-4 h-4 rounded-full bg-red-500/90 text-white flex items-center justify-center transition-opacity"
                              >
                                <X className="w-2.5 h-2.5" />
                              </button>
                            )}
                          </button>
                        );
                      })}

                      {/* Add Filter Button / Input */}
                      {showAddFilter ? (
                        <div className="shrink-0 flex items-center gap-1">
                          <Input
                            ref={addFilterRef}
                            placeholder="الحجم (مل)..."
                            className="h-7 text-[10px] w-24 px-2"
                            value={newFilterInput}
                            onChange={(e) => setNewFilterInput(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleAddCustomFilter();
                              if (e.key === "Escape") {
                                setShowAddFilter(false);
                                setNewFilterInput("");
                              }
                            }}
                            autoFocus
                          />
                          <button
                            onClick={handleAddCustomFilter}
                            className="shrink-0 w-6 h-6 rounded-md bg-primary/10 text-primary hover:bg-primary/20 flex items-center justify-center transition-colors"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => {
                              setShowAddFilter(false);
                              setNewFilterInput("");
                            }}
                            className="shrink-0 w-6 h-6 rounded-md bg-muted/30 text-muted-foreground hover:bg-muted/50 flex items-center justify-center transition-colors"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ) : (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={() => setShowAddFilter(true)}
                              className="shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-dashed border-border/40 text-[10px] text-muted-foreground hover:border-primary/40 hover:text-primary transition-all"
                            >
                              <Plus className="w-3 h-3" />
                              إضافة فلتر
                            </button>
                          </TooltipTrigger>
                          <TooltipContent className="text-xs">
                            أضف حجم جديد للفلترة — جاهز للربط بالباك إند
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                  </ScrollArea>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Glass Color + Cap Type Filter Cards (only for زجاج section) ── */}
          <AnimatePresence>
            {isGlassSection && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
                className="shrink-0 overflow-hidden border-b border-border/20"
              >
                <div className="px-5 py-3">
                  <div className="flex items-center gap-2 mb-0">
                    <button
                      onClick={() => setShowGlassColorCapFilter((p) => !p)}
                      className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
                    >
                      <GlassWater className="w-3.5 h-3.5 text-primary" />
                      <span className="text-[10px] text-muted-foreground">
                        نوع الزجاج والغطاء
                      </span>
                      <ChevronDown
                        className={`w-3 h-3 text-muted-foreground transition-transform duration-200 ${showGlassColorCapFilter ? "rotate-180" : ""}`}
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
                    {showGlassColorCapFilter && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ type: "spring", stiffness: 400, damping: 30 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-2">
                  <div className="flex items-center gap-4 flex-wrap">
                    {/* ━━━ Glass Color Cards ━━━ */}
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground shrink-0">نوع الزجاج:</span>

                      {/* All option */}
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

                      {/* Transparent card */}
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

                      {/* Colored card */}
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
                          style={{
                            background: "linear-gradient(135deg, var(--primary), var(--gold-dark))",
                          }}
                        />
                        ملوّن
                        <span className="text-[8px] opacity-60">
                          ({plItems.filter((i) => i.sectionId === "oils" && i.glassColor === "colored").length})
                        </span>
                      </button>
                    </div>

                    {/* Separator */}
                    <div className="w-px h-6 bg-border/30 shrink-0" />

                    {/* ━━━ Cap Type Cards ━━━ */}
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground shrink-0">نوع الغطاء:</span>

                      {/* All option */}
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

                      {/* Screw card */}
                      <button
                        onClick={() => setCapTypeFilter(capTypeFilter === "screw" ? "all" : "screw")}
                        className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] transition-all ${
                          capTypeFilter === "screw"
                            ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                            : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                        }`}
                      >
                        {/* Screw icon SVG */}
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

                      {/* Press/Crimp card */}
                      <button
                        onClick={() => setCapTypeFilter(capTypeFilter === "press" ? "all" : "press")}
                        className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px] transition-all ${
                          capTypeFilter === "press"
                            ? "border-primary bg-primary/10 text-primary shadow-sm shadow-primary/5"
                            : "border-border/40 text-muted-foreground hover:border-primary/30 bg-card/30"
                        }`}
                      >
                        {/* Press icon SVG */}
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

                    {/* Clear all glass filters */}
                    {(glassColorFilter !== "all" || capTypeFilter !== "all") && (
                      <button
                        onClick={() => { setGlassColorFilter("all"); setCapTypeFilter("all"); }}
                        className="text-[9px] text-primary hover:text-primary/80 transition-colors flex items-center gap-0.5 ms-auto"
                      >
                        <X className="w-2.5 h-2.5" />
                        مسح فلاتر الزجاج
                      </button>
                    )}
                  </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Brand Header + Search ── */}
          <div className="shrink-0 px-5 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {activeBrandData && (
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white shrink-0"
                  style={{ backgroundColor: activeBrandData.color }}
                >
                  <span className="text-[8px] tracking-wider">
                    {activeBrandData.nameEn.slice(0, 3).toUpperCase()}
                  </span>
                </div>
              )}
              <div>
                <h4 className="text-sm text-foreground">
                  {activeBrandData
                    ? `${activeBrandData.nameEn} — قائمة الأسعار`
                    : `${activeSectionData.name} — جميع العلامات`}
                </h4>
                <p className="text-[10px] text-muted-foreground">
                  {totalItems} منتج
                  {newItems > 0 && (
                    <span className="text-primary ms-2">
                      • {newItems} جديد
                    </span>
                  )}
                  {isGlassSection && activeSizeRange && (
                    <span className="text-primary/70 ms-2">
                      • نطاق: {activeSizeRange === "r-display" ? "زجاج عرض" : `${brandCardSizeRanges.find((r) => r.id === activeSizeRange)?.label ?? ""} ML`}
                    </span>
                  )}
                  {isGlassSection && activeSizeFilters.size > 0 && (
                    <span className="text-muted-foreground/60 ms-2">
                      • فلتر نشط
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <Input
                  placeholder="بحث بالاسم أو الكود..."
                  className="h-8 text-xs ps-8 w-48"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-1 text-[9px] text-muted-foreground bg-muted/20 px-2 py-1 rounded-md">
                    <Sparkles className="w-3 h-3 text-primary" />
                    جديد = آخر {newThreshold} يوم
                  </div>
                </TooltipTrigger>
                <TooltipContent className="text-xs max-w-[200px]">
                  يمكن تغيير عتبة «المنتج الجديد» من محرك القواعد في لوحة المشرف
                </TooltipContent>
              </Tooltip>
            </div>
          </div>

          {/* ── Items Table ── */}
          <div className="flex-1 min-h-0 px-5 pb-4">
            <ScrollArea className="h-full" dir="rtl">
              <div className="rounded-xl border border-border/40 overflow-hidden bg-card/30">
                <Table>
                  <TableHeader className="bg-muted/20">
                    <TableRow className="hover:bg-transparent border-border/30">
                      <TableHead className="text-start w-[120px] text-[11px]">
                        كود المنتج
                      </TableHead>
                      <TableHead className="text-start text-[11px]">
                        الاسم
                      </TableHead>
                      {isGlassSection && (
                        <TableHead className="text-start w-[80px] text-[11px]">
                          الحجم
                        </TableHead>
                      )}
                      {isGlassSection && (
                        <TableHead className="text-start w-[70px] text-[11px]">
                          الزجاج
                        </TableHead>
                      )}
                      {isGlassSection && (
                        <TableHead className="text-start w-[70px] text-[11px]">
                          الغطاء
                        </TableHead>
                      )}
                      <TableHead className="text-start w-[100px] text-[11px]">
                        الوحدة
                      </TableHead>
                      <TableHead className="text-start w-[100px] text-[11px]">
                        السعر
                      </TableHead>
                      <TableHead className="text-start w-[80px] text-[11px]">
                        العملة
                      </TableHead>
                      <TableHead className="text-start w-[120px] text-[11px]">
                        تاريخ الإصدار
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredItems.map((item) => {
                      const itemIsNew = isItemNew(item, newThreshold);

                      return (
                        <TableRow
                          key={item.id}
                          className={`border-border/20 transition-colors ${
                            itemIsNew
                              ? "bg-primary/[0.06] dark:bg-primary/[0.08] hover:bg-primary/[0.1]"
                              : "hover:bg-muted/10"
                          }`}
                        >
                          <TableCell
                            className={`font-mono text-xs ${
                              itemIsNew
                                ? "text-primary"
                                : "text-muted-foreground"
                            }`}
                          >
                            {item.itemCode}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <span
                                className={`text-xs ${
                                  itemIsNew ? "text-foreground" : ""
                                }`}
                              >
                                {item.name}
                              </span>
                              {itemIsNew && (
                                <Badge className="bg-primary/15 text-primary text-[8px] border-primary/20 h-4 px-1.5">
                                  NEW
                                </Badge>
                              )}
                              {!item.inStock && (
                                <Badge className="bg-red-500/10 text-red-500 text-[8px] border-transparent h-4 px-1.5">
                                  نفذ
                                </Badge>
                              )}
                              {item.isOnDiscount && (
                                <Badge className="bg-red-500/10 text-red-400 text-[8px] border-red-500/20 h-4 px-1.5">
                                  -{item.discountPct}%
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          {isGlassSection && (
                            <TableCell className="text-xs text-muted-foreground">
                              <span
                                className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] ${
                                  item.sizeML === "display"
                                    ? "bg-violet-500/10 text-violet-500"
                                    : "bg-muted/30 text-muted-foreground"
                                }`}
                                style={
                                  typeof item.sizeML === "number"
                                    ? { direction: "ltr" as const, unicodeBidi: "embed" as const }
                                    : undefined
                                }
                              >
                                {getSizeLabel(item.sizeML)}
                              </span>
                            </TableCell>
                          )}
                          {isGlassSection && (
                            <TableCell className="text-xs text-muted-foreground">
                              <span
                                className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] ${
                                  item.glassColor === "transparent"
                                    ? "bg-violet-500/10 text-violet-500"
                                    : "bg-muted/30 text-muted-foreground"
                                }`}
                              >
                                {item.glassColor === "transparent" ? "شفاف" : "ملون"}
                              </span>
                            </TableCell>
                          )}
                          {isGlassSection && (
                            <TableCell className="text-xs text-muted-foreground">
                              <span
                                className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] ${
                                  item.capType === "screw"
                                    ? "bg-violet-500/10 text-violet-500"
                                    : "bg-muted/30 text-muted-foreground"
                                }`}
                              >
                                {item.capType === "screw" ? "لولبي" : "كبس"}
                              </span>
                            </TableCell>
                          )}
                          <TableCell className="text-xs text-muted-foreground">
                            {unitLabels[item.unit]}
                          </TableCell>
                          <TableCell
                            className={`text-xs font-mono ${
                              itemIsNew ? "text-primary" : "text-foreground"
                            }`}
                          >
                            {item.currency === "USD" && "$"}
                            {item.price.toLocaleString("en-US", {
                              minimumFractionDigits: 2,
                            })}
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {currencyLabels[item.currency]}
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground" dir="ltr">
                            <span style={{ direction: "ltr", unicodeBidi: "embed" }}>
                              {formatDate(item.releaseDate)}
                            </span>
                          </TableCell>
                        </TableRow>
                      );
                    })}

                    {filteredItems.length === 0 && (
                      <TableRow>
                        <TableCell
                          colSpan={tableColSpan}
                          className="text-center py-12"
                        >
                          <Package className="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
                          <p className="text-xs text-muted-foreground">
                            {searchQuery
                              ? "لا توجد منتجات تطابق البحث"
                              : activeSizeRange || activeSizeFilters.size > 0
                                ? "لا توجد منتجات تطابق الفلتر المحدد"
                                : "لا توجد منتجات في هذا القسم"}
                          </p>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

// ── Size Range Card Component ──────────────────────────

function SizeRangeCard({
  range,
  isActive,
  itemCount,
  newCount,
  isDisplay,
  onClick,
}: {
  range: SizeRange;
  isActive: boolean;
  itemCount: number;
  newCount: number;
  isDisplay?: boolean;
  onClick: () => void;
}) {
  return (
    <motion.button
      onClick={onClick}
      disabled={itemCount === 0}
      className={`shrink-0 flex items-center gap-2.5 px-3.5 py-2 rounded-xl border transition-all ${
        isActive
          ? isDisplay
            ? "border-violet-500 bg-violet-500/10 dark:bg-violet-500/15 shadow-sm shadow-violet-500/10"
            : "border-primary bg-primary/5 dark:bg-primary/10 shadow-sm shadow-primary/10"
          : itemCount > 0
            ? "border-border/40 bg-card/40 hover:border-primary/30 hover:bg-card/60"
            : "border-border/20 bg-card/10 opacity-35 cursor-default"
      }`}
      whileHover={itemCount > 0 ? { y: -1 } : undefined}
      whileTap={itemCount > 0 ? { scale: 0.98 } : undefined}
    >
      {/* Compact icon */}
      <div
        className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
          isActive
            ? isDisplay
              ? "bg-violet-500/20 text-violet-500"
              : "bg-primary/15 text-primary"
            : "bg-muted/30 text-muted-foreground"
        }`}
      >
        {isDisplay ? (
          <GlassWater className="w-3.5 h-3.5" />
        ) : (
          <CircleDot className="w-3.5 h-3.5" />
        )}
      </div>

      {/* Label + count */}
      <div className="flex flex-col items-start gap-0.5 min-w-0">
        <span
          className={`text-[11px] whitespace-nowrap ${
            isActive
              ? isDisplay ? "text-violet-500" : "text-primary"
              : "text-foreground"
          }`}
          style={{ direction: "ltr", unicodeBidi: "embed" }}
        >
          {isDisplay ? "زجاج عرض" : `${range.label} ML`}
        </span>
        <div className="flex items-center gap-1.5">
          <span
            className={`text-[8px] ${
              isActive
                ? isDisplay ? "text-violet-500/70" : "text-primary/70"
                : "text-muted-foreground"
            }`}
          >
            {itemCount} منتج
          </span>
          {newCount > 0 && (
            <span className="text-[7px] px-1 py-px rounded-full bg-primary/15 text-primary">
              {newCount} جديد
            </span>
          )}
        </div>
      </div>
    </motion.button>
  );
}

// ── Brand Card Component ───────────────────────────────

function BrandCard({
  brand,
  isActive,
  itemCount,
  newCount,
  isGlass,
  availableSizes,
  onClick,
}: {
  brand: PLBrand;
  isActive: boolean;
  itemCount: number;
  newCount: number;
  isGlass: boolean;
  availableSizes: (number | "display")[];
  onClick: () => void;
}) {
  return (
    <motion.button
      onClick={onClick}
      className={`shrink-0 flex flex-col gap-2 px-4 py-2.5 rounded-xl border transition-all ${
        isGlass ? "min-w-[180px]" : "min-w-[140px]"
      } ${
        isActive
          ? "border-primary bg-primary/5 dark:bg-primary/10 shadow-sm shadow-primary/10"
          : "border-border/40 bg-card/40 hover:border-primary/30 hover:bg-card/60"
      }`}
      whileHover={{ y: -1 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Top row: Logo + Brand Info + Badges */}
      <div className="flex items-center gap-3 w-full">
        {/* Brand Logo Area */}
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 relative"
          style={{
            backgroundColor: isActive ? brand.color : `${brand.color}20`,
            color: isActive ? "#fff" : brand.color,
          }}
        >
          <span
            className="text-[8px] tracking-wider"
            style={{ direction: "ltr", unicodeBidi: "embed" }}
          >
            {brand.nameEn
              .split(" ")
              .map((w) => w[0])
              .join("")
              .toUpperCase()
              .slice(0, 3)}
          </span>
          {/* New badge dot on logo */}
          {newCount > 0 && (
            <span className="absolute -top-1 -end-1 w-3.5 h-3.5 rounded-full bg-primary text-[7px] text-white flex items-center justify-center shadow-sm shadow-primary/30">
              {newCount}
            </span>
          )}
        </div>

        {/* Brand Info */}
        <div className="text-start min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <p
              className={`text-[11px] truncate ${
                isActive ? "text-primary" : "text-foreground"
              }`}
              style={{ direction: "ltr", unicodeBidi: "embed" }}
            >
              {brand.nameEn}
            </p>
            {newCount > 0 && (
              <span className="shrink-0 text-[7px] px-1.5 py-0.5 rounded-full bg-primary/15 text-primary">
                {newCount} جديد
              </span>
            )}
          </div>
          {/* Tagline or item count */}
          {brand.tagline && !isGlass ? (
            <p
              className="text-[8px] text-muted-foreground truncate"
              style={{ direction: "ltr", unicodeBidi: "embed" }}
            >
              {brand.tagline}
            </p>
          ) : (
            <p className="text-[8px] text-muted-foreground">
              {itemCount} منتج
            </p>
          )}
        </div>
      </div>

      {/* Bottom row: Glass size chips (only for glass section) */}
      {isGlass && availableSizes.length > 0 && (() => {
        const { ranges, hasDisplay } = getBrandSizeRanges(availableSizes);
        return (
        <div className="flex items-center gap-1 flex-wrap w-full">
          {ranges.map((range) => (
            <span
              key={range.id}
              className={`px-1.5 py-0.5 rounded text-[7px] ${
                isActive
                  ? "bg-primary/10 text-primary"
                  : "bg-muted/30 text-muted-foreground"
              }`}
              style={{ direction: "ltr" as const, unicodeBidi: "embed" as const }}
            >
              {range.label} ML
            </span>
          ))}
          {hasDisplay && (
            <span
              className="px-1.5 py-0.5 rounded text-[7px] bg-violet-500/10 text-violet-400 dark:text-violet-300"
            >
              زجاج عرض
            </span>
          )}
        </div>
        );
      })()}
    </motion.button>
  );
}

// ── Helpers ─────────────────────────────────────────────

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}