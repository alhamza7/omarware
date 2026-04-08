// ═══════════════════════════════════════════════════════════
//  Price List — Data Model & Mock Data
//  No hardcoded rules: "new item" threshold comes from Rule Engine
// ═══════════════════════════════════════════════════════════

// ── Section (Product Category) ───────────────────────────

export interface PLSection {
  id: string;
  name: string;
  order: number;
}

export const plSections: PLSection[] = [
  { id: "perfumes", name: "العطور", order: 0 },
  { id: "oils", name: "زجاج", order: 1 },
  { id: "diffusers", name: "المعطرات", order: 2 },
  { id: "machines", name: "الأجهزة", order: 3 },
  { id: "accessories", name: "الإكسسوارات", order: 4 },
  { id: "incense", name: "البخور", order: 5 },
];

// ── Brand ────────────────────────────────────────────────

export interface PLBrand {
  id: string;
  name: string;
  nameEn: string;
  tagline?: string;
  logoText?: string;       // display text when no logo image
  sectionId: string;       // which section this brand belongs to
  color: string;           // brand accent color (hex)
}

export const plBrands: PLBrand[] = [
  // ── Perfumes ──
  { id: "givaudan", name: "جيفودان", nameEn: "Givaudan", tagline: "Human by nature", sectionId: "perfumes", color: "#1a1a2e" },
  { id: "amour-de-fleurs", name: "أمور دو فلور", nameEn: "Amour De Fleurs", tagline: "HAUTE PARFUMERIE", sectionId: "perfumes", color: "#8b5cf6" },
  { id: "robertet", name: "روبرتيه", nameEn: "Robertet", tagline: "GRASSE · FRANCE", sectionId: "perfumes", color: "#b91c1c" },
  { id: "florchem", name: "فلوركيم", nameEn: "Florchem", tagline: "FLAVOR & FRAGRANCE", sectionId: "perfumes", color: "#059669" },
  { id: "european", name: "يوروبيان", nameEn: "EUROPEAN", tagline: "PERFUMERY", sectionId: "perfumes", color: "#0369a1" },
  { id: "firmenich", name: "فيرمنيتش", nameEn: "Firmenich", tagline: "SINCE 1895", sectionId: "perfumes", color: "#7c3aed" },

  // ── Oils ──
  { id: "al-haramain-oils", name: "الحرمين للزيوت", nameEn: "Al Haramain Oils", sectionId: "oils", color: "#92400e" },
  { id: "swiss-arabian-oils", name: "سويس أرابيان", nameEn: "Swiss Arabian", sectionId: "oils", color: "#1e3a5f" },
  { id: "ajmal-oils", name: "أجمل للزيوت", nameEn: "Ajmal Oils", tagline: "PURE ESSENCE", sectionId: "oils", color: "#6d28d9" },

  // ── Diffusers ──
  { id: "rituals", name: "ريتوالز", nameEn: "Rituals", sectionId: "diffusers", color: "#1f2937" },
  { id: "diptyque", name: "ديبتيك", nameEn: "Diptyque", tagline: "PARIS", sectionId: "diffusers", color: "#374151" },

  // ── Machines ──
  { id: "aroma-tech", name: "أروما تك", nameEn: "AromaTech", sectionId: "machines", color: "#0ea5e9" },
  { id: "scentair", name: "سنت إير", nameEn: "ScentAir", sectionId: "machines", color: "#14532d" },

  // ── Accessories ──
  { id: "perfume-bottles", name: "قوارير فاخرة", nameEn: "Luxury Bottles", sectionId: "accessories", color: "#78350f" },
  { id: "gift-boxes", name: "علب الهدايا", nameEn: "Gift Boxes", sectionId: "accessories", color: "#831843" },

  // ── Incense ──
  { id: "dukhoon-house", name: "دار الدخون", nameEn: "Dukhoon House", sectionId: "incense", color: "#451a03" },
  { id: "oud-elite", name: "عود النخبة", nameEn: "Oud Elite", tagline: "PREMIUM OUD", sectionId: "incense", color: "#1c1917" },
];

// ── Product Item ────────────────────────────────────────

export type PLCurrency = "USD" | "SAR" | "EUR" | "AED";
export type PLUnit = "Bottle" | "ML" | "KG" | "Piece" | "Box" | "Set" | "Unit";

export interface PLItem {
  id: string;
  itemCode: string;
  name: string;
  nameEn: string;
  brandId: string;
  sectionId: string;
  unit: PLUnit;
  price: number;
  currency: PLCurrency;
  releaseDate: string;     // ISO date string
  inStock: boolean;
  sizeML?: number | "display"; // glass bottle size (ML) or "display" for زجاج عرض
  glassColor?: "transparent" | "colored"; // transparent = شفاف, colored = ملوّن
  capType?: "screw" | "press";            // screw = لولبي, press = كبس
  moq?: number;            // minimum order quantity
  notes?: string;
  isOnDiscount?: boolean;  // flagged as currently on discount
  discountPct?: number;    // discount percentage
  stock?: number;          // current stock count (for restocking requests)
}

// ── Helper: calculate "new" based on days threshold ──────

export function isItemNew(item: PLItem, thresholdDays: number): boolean {
  const releaseDate = new Date(item.releaseDate);
  const today = new Date("2026-02-23"); // current date
  const diffMs = today.getTime() - releaseDate.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays <= thresholdDays && diffDays >= 0;
}

// ── Sort items: NEW first, then alphabetically ───────────

export function sortItemsWithNewFirst(items: PLItem[], thresholdDays: number): PLItem[] {
  return [...items].sort((a, b) => {
    const aNew = isItemNew(a, thresholdDays);
    const bNew = isItemNew(b, thresholdDays);
    if (aNew && !bNew) return -1;
    if (!aNew && bNew) return 1;
    // within same group, sort by name
    return a.name.localeCompare(b.name, "ar");
  });
}

// ── Mock Product Items ───────────────────────────────────

export const plItems: PLItem[] = [
  // ═══ Givaudan (Perfumes) ═══
  { id: "p-001", itemCode: "PERF-001", name: "عطر فاخر 100مل", nameEn: "Luxury Eau de Parfum 100ml", brandId: "givaudan", sectionId: "perfumes", unit: "Bottle", price: 125, currency: "USD", releaseDate: "2025-12-18", inStock: true, stock: 24 },
  { id: "p-002", itemCode: "PERF-006", name: "عطر ديلوكس 150مل", nameEn: "Deluxe Fragrance 150ml", brandId: "givaudan", sectionId: "perfumes", unit: "Bottle", price: 175, currency: "USD", releaseDate: "2026-01-22", inStock: true, isOnDiscount: true, discountPct: 15, stock: 12 },
  { id: "p-003", itemCode: "PERF-011", name: "بريميوم جفودن 100مل", nameEn: "Givaudan Premium 100ml", brandId: "givaudan", sectionId: "perfumes", unit: "Bottle", price: 135, currency: "USD", releaseDate: "2025-12-25", inStock: true, stock: 18 },

  // ═══ Amour De Fleurs (Perfumes) ═══
  { id: "p-004", itemCode: "PERF-002", name: "روز أمور 50مل", nameEn: "Rose Amour 50ml", brandId: "amour-de-fleurs", sectionId: "perfumes", unit: "Bottle", price: 95, currency: "USD", releaseDate: "2025-11-10", inStock: true, isOnDiscount: true, discountPct: 20, stock: 30 },
  { id: "p-005", itemCode: "PERF-007", name: "فلور نوار 100مل", nameEn: "Fleur Noire 100ml", brandId: "amour-de-fleurs", sectionId: "perfumes", unit: "Bottle", price: 180, currency: "USD", releaseDate: "2026-02-05", inStock: true, stock: 8 },
  { id: "p-006", itemCode: "PERF-012", name: "جاردان دو باريس 75مل", nameEn: "Jardin de Paris 75ml", brandId: "amour-de-fleurs", sectionId: "perfumes", unit: "Bottle", price: 145, currency: "USD", releaseDate: "2025-09-15", inStock: true, stock: 15 },
  { id: "p-007", itemCode: "PERF-015", name: "ليلة أمور 100مل", nameEn: "Nuit d'Amour 100ml", brandId: "amour-de-fleurs", sectionId: "perfumes", unit: "Bottle", price: 210, currency: "USD", releaseDate: "2026-02-10", inStock: true, stock: 5 },

  // ═══ Robertet (Perfumes) ═══
  { id: "p-008", itemCode: "PERF-003", name: "إسنس غراس 100مل", nameEn: "Essence de Grasse 100ml", brandId: "robertet", sectionId: "perfumes", unit: "Bottle", price: 220, currency: "USD", releaseDate: "2025-10-01", inStock: true, stock: 10 },
  { id: "p-009", itemCode: "PERF-008", name: "ناتورال أبسوليوت 50مل", nameEn: "Natural Absolute 50ml", brandId: "robertet", sectionId: "perfumes", unit: "Bottle", price: 310, currency: "USD", releaseDate: "2026-01-28", inStock: true, stock: 3 },
  { id: "p-010", itemCode: "PERF-013", name: "مسك بروفنس 75مل", nameEn: "Musc de Provence 75ml", brandId: "robertet", sectionId: "perfumes", unit: "Bottle", price: 185, currency: "USD", releaseDate: "2025-08-20", inStock: false, isOnDiscount: true, discountPct: 30, stock: 0 },

  // ═══ Florchem (Perfumes) ═══
  { id: "p-011", itemCode: "PERF-004", name: "فلورال سيمفوني 100مل", nameEn: "Floral Symphony 100ml", brandId: "florchem", sectionId: "perfumes", unit: "Bottle", price: 110, currency: "USD", releaseDate: "2025-11-25", inStock: true, stock: 20 },
  { id: "p-012", itemCode: "PERF-009", name: "سيدار وود 75مل", nameEn: "Cedar Wood 75ml", brandId: "florchem", sectionId: "perfumes", unit: "Bottle", price: 90, currency: "USD", releaseDate: "2026-02-15", inStock: true, stock: 10 },

  // ═══ European (Perfumes) ═══
  { id: "p-013", itemCode: "PERF-005", name: "كلاسيك يورو 100مل", nameEn: "Classic Euro 100ml", brandId: "european", sectionId: "perfumes", unit: "Bottle", price: 155, currency: "USD", releaseDate: "2025-10-12", inStock: true, stock: 15 },
  { id: "p-014", itemCode: "PERF-010", name: "أورينتال بلند 150مل", nameEn: "Oriental Blend 150ml", brandId: "european", sectionId: "perfumes", unit: "Bottle", price: 195, currency: "USD", releaseDate: "2026-01-05", inStock: true, stock: 5 },
  { id: "p-015", itemCode: "PERF-014", name: "ميديتيرانيان فريش 100مل", nameEn: "Mediterranean Fresh 100ml", brandId: "european", sectionId: "perfumes", unit: "Bottle", price: 140, currency: "USD", releaseDate: "2025-07-01", inStock: true, stock: 25 },

  // ═══ Firmenich (Perfumes) ═══
  { id: "p-016", itemCode: "PERF-016", name: "فيرمنيتش إليت 100مل", nameEn: "Firmenich Elite 100ml", brandId: "firmenich", sectionId: "perfumes", unit: "Bottle", price: 250, currency: "USD", releaseDate: "2026-02-18", inStock: true, stock: 8 },
  { id: "p-017", itemCode: "PERF-017", name: "أروماتيك سويس 75مل", nameEn: "Aromatic Swiss 75ml", brandId: "firmenich", sectionId: "perfumes", unit: "Bottle", price: 190, currency: "USD", releaseDate: "2025-09-30", inStock: true, stock: 12 },

  // ═══ Oils (زجاج) ═══
  { id: "p-020", itemCode: "GLS-001", name: "زجاج عود كمبودي 10مل", nameEn: "Cambodian Oud Glass 10ml", brandId: "al-haramain-oils", sectionId: "oils", unit: "Piece", price: 850, currency: "SAR", releaseDate: "2025-11-01", inStock: true, sizeML: 10, glassColor: "colored", capType: "screw" },
  { id: "p-021", itemCode: "GLS-002", name: "زجاج ورد طائفي 5مل", nameEn: "Taif Rose Glass 5ml", brandId: "al-haramain-oils", sectionId: "oils", unit: "Piece", price: 420, currency: "SAR", releaseDate: "2026-01-15", inStock: true, sizeML: 5, glassColor: "transparent", capType: "screw" },
  { id: "p-022", itemCode: "GLS-003", name: "زجاج مسك أبيض 15مل", nameEn: "White Musk Glass 15ml", brandId: "al-haramain-oils", sectionId: "oils", unit: "Piece", price: 280, currency: "SAR", releaseDate: "2025-08-10", inStock: true, sizeML: 15, glassColor: "transparent", capType: "press" },
  { id: "p-023", itemCode: "GLS-004", name: "زجاج عنبر ذهبي 3مل", nameEn: "Golden Amber Glass 3ml", brandId: "swiss-arabian-oils", sectionId: "oils", unit: "Piece", price: 350, currency: "SAR", releaseDate: "2026-02-01", inStock: true, sizeML: 3, glassColor: "colored", capType: "screw" },
  { id: "p-024", itemCode: "GLS-005", name: "زجاج صندل هندي 25مل", nameEn: "Indian Sandalwood Glass 25ml", brandId: "swiss-arabian-oils", sectionId: "oils", unit: "Piece", price: 520, currency: "SAR", releaseDate: "2025-10-20", inStock: true, sizeML: 25, glassColor: "transparent", capType: "press" },
  { id: "p-025", itemCode: "GLS-006", name: "زجاج عود أسام 50مل", nameEn: "Assam Oud Glass 50ml", brandId: "ajmal-oils", sectionId: "oils", unit: "Piece", price: 1200, currency: "SAR", releaseDate: "2026-02-12", inStock: true, sizeML: 50, glassColor: "colored", capType: "press" },
  { id: "p-026", itemCode: "GLS-007", name: "زجاج ياسمين سامباك 30مل", nameEn: "Sambac Jasmine Glass 30ml", brandId: "ajmal-oils", sectionId: "oils", unit: "Piece", price: 380, currency: "SAR", releaseDate: "2025-06-15", inStock: true, sizeML: 30, glassColor: "transparent", capType: "screw" },
  { id: "p-027", itemCode: "GLS-008", name: "زجاج عرض كريستال كبير", nameEn: "Crystal Display Glass Large", brandId: "al-haramain-oils", sectionId: "oils", unit: "Piece", price: 95, currency: "SAR", releaseDate: "2025-12-01", inStock: true, sizeML: "display", glassColor: "transparent", capType: "screw" },
  { id: "p-028", itemCode: "GLS-009", name: "زجاج ورد بلغاري 100مل", nameEn: "Bulgarian Rose Glass 100ml", brandId: "swiss-arabian-oils", sectionId: "oils", unit: "Piece", price: 1850, currency: "SAR", releaseDate: "2026-02-18", inStock: true, sizeML: 100, glassColor: "transparent", capType: "press" },
  { id: "p-029", itemCode: "GLS-010", name: "زجاج عود هندي 75مل", nameEn: "Indian Oud Glass 75ml", brandId: "ajmal-oils", sectionId: "oils", unit: "Piece", price: 980, currency: "SAR", releaseDate: "2026-01-20", inStock: true, sizeML: 75, glassColor: "colored", capType: "screw" },
  { id: "p-029b", itemCode: "GLS-011", name: "زجاج مسك طهارة 20مل", nameEn: "Tahara Musk Glass 20ml", brandId: "al-haramain-oils", sectionId: "oils", unit: "Piece", price: 310, currency: "SAR", releaseDate: "2025-09-05", inStock: true, sizeML: 20, glassColor: "transparent", capType: "screw" },
  { id: "p-029c", itemCode: "GLS-012", name: "زجاج عنبر رمادي 40مل", nameEn: "Grey Ambergris Glass 40ml", brandId: "swiss-arabian-oils", sectionId: "oils", unit: "Piece", price: 720, currency: "SAR", releaseDate: "2026-02-05", inStock: true, sizeML: 40, glassColor: "colored", capType: "press" },
  { id: "p-029d", itemCode: "GLS-013", name: "زجاج عرض ذهبي صغير", nameEn: "Small Gold Display Glass", brandId: "ajmal-oils", sectionId: "oils", unit: "Piece", price: 65, currency: "SAR", releaseDate: "2025-11-20", inStock: true, sizeML: "display", glassColor: "colored", capType: "screw" },
  { id: "p-029e", itemCode: "GLS-014", name: "زجاج دهن عود 60مل", nameEn: "Dehn Al Oud Glass 60ml", brandId: "al-haramain-oils", sectionId: "oils", unit: "Piece", price: 1450, currency: "SAR", releaseDate: "2026-01-28", inStock: true, sizeML: 60, glassColor: "transparent", capType: "press" },
  { id: "p-029f", itemCode: "GLS-015", name: "زجاج زعفران 35مل", nameEn: "Saffron Glass 35ml", brandId: "swiss-arabian-oils", sectionId: "oils", unit: "Piece", price: 580, currency: "SAR", releaseDate: "2025-07-10", inStock: false, sizeML: 35, glassColor: "transparent", capType: "screw" },
  { id: "p-029g", itemCode: "GLS-016", name: "زجاج عود ملكي 90مل", nameEn: "Royal Oud Glass 90ml", brandId: "ajmal-oils", sectionId: "oils", unit: "Piece", price: 2100, currency: "SAR", releaseDate: "2026-02-20", inStock: true, sizeML: 90, glassColor: "colored", capType: "press" },

  // ═══ Diffusers ═══
  { id: "p-030", itemCode: "DIF-001", name: "معطر الصالون 200مل", nameEn: "Salon Diffuser 200ml", brandId: "rituals", sectionId: "diffusers", unit: "Bottle", price: 65, currency: "USD", releaseDate: "2025-12-01", inStock: true, stock: 30 },
  { id: "p-031", itemCode: "DIF-002", name: "أعواد معطرة فاخرة", nameEn: "Luxury Reed Diffuser", brandId: "rituals", sectionId: "diffusers", unit: "Set", price: 85, currency: "USD", releaseDate: "2026-02-08", inStock: true, stock: 20 },
  { id: "p-032", itemCode: "DIF-003", name: "شمعة عطرية بايس 300غ", nameEn: "Baies Scented Candle 300g", brandId: "diptyque", sectionId: "diffusers", unit: "Piece", price: 72, currency: "USD", releaseDate: "2025-09-10", inStock: true, stock: 15 },
  { id: "p-033", itemCode: "DIF-004", name: "معطر كار فريش", nameEn: "Car Fresh Diffuser", brandId: "diptyque", sectionId: "diffusers", unit: "Piece", price: 48, currency: "USD", releaseDate: "2026-01-18", inStock: true, stock: 25 },

  // ═══ Machines ═══
  { id: "p-040", itemCode: "MCH-001", name: "جهاز أروما 300 برو", nameEn: "AromaTech 300 Pro", brandId: "aroma-tech", sectionId: "machines", unit: "Unit", price: 1500, currency: "SAR", releaseDate: "2025-10-15", inStock: true, stock: 5 },
  { id: "p-041", itemCode: "MCH-002", name: "جهاز أروما 100 ميني", nameEn: "AromaTech 100 Mini", brandId: "aroma-tech", sectionId: "machines", unit: "Unit", price: 750, currency: "SAR", releaseDate: "2026-02-20", inStock: true, stock: 10 },
  { id: "p-042", itemCode: "MCH-003", name: "جهاز سنت إير سمارت", nameEn: "ScentAir Smart Device", brandId: "scentair", sectionId: "machines", unit: "Unit", price: 2200, currency: "SAR", releaseDate: "2025-11-20", inStock: true, stock: 3 },
  { id: "p-043", itemCode: "MCH-004", name: "جهاز سنت إير بورتابل", nameEn: "ScentAir Portable", brandId: "scentair", sectionId: "machines", unit: "Unit", price: 890, currency: "SAR", releaseDate: "2026-01-30", inStock: true, stock: 7 },

  // ═══ Accessories ═══
  { id: "p-050", itemCode: "ACC-001", name: "قارورة كريستال 100مل", nameEn: "Crystal Bottle 100ml", brandId: "perfume-bottles", sectionId: "accessories", unit: "Piece", price: 45, currency: "SAR", releaseDate: "2025-08-01", inStock: true, stock: 20 },
  { id: "p-051", itemCode: "ACC-002", name: "قارورة ذهبية 50مل", nameEn: "Gold Bottle 50ml", brandId: "perfume-bottles", sectionId: "accessories", unit: "Piece", price: 65, currency: "SAR", releaseDate: "2026-02-14", inStock: true, stock: 15 },
  { id: "p-052", itemCode: "ACC-003", name: "علبة هدية فاخرة كبيرة", nameEn: "Luxury Gift Box Large", brandId: "gift-boxes", sectionId: "accessories", unit: "Box", price: 35, currency: "SAR", releaseDate: "2025-12-10", inStock: true, stock: 10 },
  { id: "p-053", itemCode: "ACC-004", name: "علبة هدية VIP", nameEn: "VIP Gift Box", brandId: "gift-boxes", sectionId: "accessories", unit: "Box", price: 85, currency: "SAR", releaseDate: "2026-02-01", inStock: true, stock: 5 },

  // ═══ Incense ═══
  { id: "p-060", itemCode: "INC-001", name: "بخور عود سوبر كيوسي", nameEn: "Super Kinam Oud Incense", brandId: "dukhoon-house", sectionId: "incense", unit: "Box", price: 950, currency: "SAR", releaseDate: "2025-10-01", inStock: true, stock: 12 },
  { id: "p-061", itemCode: "INC-002", name: "بخور معمول فاخر", nameEn: "Luxury Mamoul Incense", brandId: "dukhoon-house", sectionId: "incense", unit: "Box", price: 180, currency: "SAR", releaseDate: "2026-02-19", inStock: true, stock: 20 },
  { id: "p-062", itemCode: "INC-003", name: "عود نخبة كمبودي", nameEn: "Elite Cambodian Oud", brandId: "oud-elite", sectionId: "incense", unit: "Box", price: 2500, currency: "SAR", releaseDate: "2025-06-01", inStock: true, stock: 8 },
  { id: "p-063", itemCode: "INC-004", name: "عود سوبر هندي", nameEn: "Super Indian Oud", brandId: "oud-elite", sectionId: "incense", unit: "Box", price: 1800, currency: "SAR", releaseDate: "2026-01-10", inStock: true, stock: 15 },
];

// ── Currency labels ──────────────────────────────────────

export const currencyLabels: Record<PLCurrency, string> = {
  USD: "USD",
  SAR: "ر.س",
  EUR: "EUR",
  AED: "د.إ",
};

// ── Unit labels ──────────────────────────────────────────

export const unitLabels: Record<PLUnit, string> = {
  Bottle: "قارورة",
  ML: "مل",
  KG: "كغ",
  Piece: "قطعة",
  Box: "علبة",
  Set: "طقم",
  Unit: "وحدة",
};

// ── Glass (زجاج) Size Filters ───────────────────────────
// Predefined sizes for the glass section.
// Custom filters can be added via the UI and persisted to localStorage
// (ready for backend wiring via Supabase / API).

export interface PLSizeFilter {
  id: string;
  label: string;
  value: number | "display"; // ML size or "display" for زجاج عرض
  isCustom?: boolean;        // true = added by user (not built-in)
}

export const defaultGlassSizeFilters: PLSizeFilter[] = [
  { id: "sz-3",   label: "3ML",  value: 3 },
  { id: "sz-5",   label: "5ML",  value: 5 },
  { id: "sz-10",  label: "10ML", value: 10 },
  { id: "sz-15",  label: "15ML", value: 15 },
  { id: "sz-20",  label: "20ML", value: 20 },
  { id: "sz-25",  label: "25ML", value: 25 },
  { id: "sz-30",  label: "30ML", value: 30 },
  { id: "sz-35",  label: "35ML", value: 35 },
  { id: "sz-40",  label: "40ML", value: 40 },
  { id: "sz-45",  label: "45ML", value: 45 },
  { id: "sz-50",  label: "50ML", value: 50 },
  { id: "sz-55",  label: "55ML", value: 55 },
  { id: "sz-60",  label: "60ML", value: 60 },
  { id: "sz-65",  label: "65ML", value: 65 },
  { id: "sz-70",  label: "70ML", value: 70 },
  { id: "sz-75",  label: "75ML", value: 75 },
  { id: "sz-80",  label: "80ML", value: 80 },
  { id: "sz-90",  label: "90ML", value: 90 },
  { id: "sz-100", label: "100ML", value: 100 },
];

/** Size range definition for BrandCard display */
export interface SizeRange {
  id: string;
  label: string;
  min: number;
  max: number | null; // null = no upper bound (80+)
}

/** Predefined size ranges for BrandCard chips */
export const brandCardSizeRanges: SizeRange[] = [
  { id: "r-2-9",   label: "2 – 9",   min: 2,  max: 9 },
  { id: "r-10-19", label: "10 – 19",  min: 10, max: 19 },
  { id: "r-20-29", label: "20 – 29",  min: 20, max: 29 },
  { id: "r-30-39", label: "30 – 39",  min: 30, max: 39 },
  { id: "r-40-49", label: "40 – 49",  min: 40, max: 49 },
  { id: "r-50-59", label: "50 – 59",  min: 50, max: 59 },
  { id: "r-60-69", label: "60 – 69",  min: 60, max: 69 },
  { id: "r-70-79", label: "70 – 79",  min: 70, max: 79 },
  { id: "r-80+",   label: "80+",      min: 80, max: null },
];

/** Check which ranges a brand's sizes fall into */
export function getBrandSizeRanges(sizes: (number | "display")[]): { ranges: SizeRange[]; hasDisplay: boolean } {
  const hasDisplay = sizes.includes("display");
  const numericSizes = sizes.filter((s): s is number => typeof s === "number");
  const activeRanges = brandCardSizeRanges.filter((range) =>
    numericSizes.some((size) =>
      size >= range.min && (range.max === null || size <= range.max),
    ),
  );
  return { ranges: activeRanges, hasDisplay };
}

/** Check if an item's sizeML matches a given range filter */
export function matchesSizeFilter(sizeML: number | "display" | undefined, filter: PLSizeFilter): boolean {
  if (sizeML === undefined) return false;
  if (filter.value === "display") return sizeML === "display";
  if (sizeML === "display") return false;
  const num = sizeML as number;
  return num === filter.value;
}

const GLASS_CUSTOM_FILTERS_KEY = "pl_custom_glass_filters";

export function loadCustomGlassFilters(): PLSizeFilter[] {
  try {
    const stored = localStorage.getItem(GLASS_CUSTOM_FILTERS_KEY);
    if (stored) return JSON.parse(stored);
  } catch { /* ignore */ }
  return [];
}

export function saveCustomGlassFilters(filters: PLSizeFilter[]): void {
  try {
    localStorage.setItem(GLASS_CUSTOM_FILTERS_KEY, JSON.stringify(filters));
  } catch { /* ignore */ }
}