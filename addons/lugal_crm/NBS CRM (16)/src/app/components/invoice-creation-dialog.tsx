import { useState, useMemo, useCallback, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import {
  Receipt,
  Plus,
  Trash2,
  CheckCircle2,
  Save,
  Printer,
  X,
  Copy,
  Settings2,
  Loader2,
} from "lucide-react";
import { motion } from "motion/react";
import { FormSettingsDialog, type FormSettings } from "./invoice-form-settings";
import type {
  ApiProduct,
  ApiProductDetail,
  ApiWarehouse,
  CreatedOrder,
  CreateOrderPayload,
  CreateOrderLine,
} from "../../features/pos-invoice/types";

// ─── Static fallback catalog (used when external data is not yet loaded) ─────
const FALLBACK_PRODUCTS: ApiProduct[] = [
  { id: -1, name: "عود ملكي - إصدار محدود", default_code: "OUD-001", foreign_name: "", uom_id: { id: 1, name: "قطعة" }, list_price: 600, qty_available: 0 },
  { id: -2, name: "مسك الليل",               default_code: "MSK-001", foreign_name: "", uom_id: { id: 1, name: "قطعة" }, list_price: 600, qty_available: 0 },
  { id: -3, name: "روز باريس الفاخر",        default_code: "ROS-001", foreign_name: "", uom_id: { id: 1, name: "قطعة" }, list_price: 600, qty_available: 0 },
  { id: -4, name: "دهن عود هندي",            default_code: "OUD-002", foreign_name: "", uom_id: { id: 1, name: "تولة"  }, list_price: 950, qty_available: 0 },
];

const FALLBACK_WAREHOUSES: ApiWarehouse[] = [
  { id: -1, name: "المستودع الرئيسي", code: "MK-01" },
  { id: -2, name: "مستودع البخور",     code: "MK-02" },
];

const CONTACTS = [
  "أحمد محمد", "فهد العلي", "سارة الحربي", "خالد المطيري",
];

const CURRENCIES = [
  { value: "SAR", label: "ريال سعودي" },
  { value: "USD", label: "دولار أمريكي" },
  { value: "IQD", label: "دينار عراقي"  },
];

/** Fallback invoice types used when the API hasn't returned context yet */
const FALLBACK_INV_TYPES = [
  { value: "1", label: "زبون محل" },
  { value: "2", label: "شركات توصيل" },
  { value: "3", label: "نقليات" },
  { value: "4", label: "ديلفري" },
  { value: "5", label: "NBS" },
];

const VAT_RATE = 0.15;

// ─── Types ───────────────────────────────────────────────
interface InvoiceLineItem {
  id: string;
  rowNum: number;
  /** Odoo product.product ID (numeric); null for un-selected rows */
  productApiId: number | null;
  itemNo: string;
  itemDescription: string;
  quantity: number;
  uomCode: string;
  /** UoM ID from Odoo (for submitting) */
  uomApiId: number | null;
  warehouse: string;
  /** Warehouse ID from Odoo (for submitting) */
  warehouseApiId: number | null;
  unitPrice: number;
  discountPercent: number;
  taxCode: string;
  totalLC: number;
  cogsBranch: string;
}

interface ColumnDef {
  key: string;
  label: string;
  minWidth: number;
  defaultWidth: number;
}

const COLUMNS: ColumnDef[] = [
  { key: "rowNum", label: "#", minWidth: 32, defaultWidth: 36 },
  { key: "itemNo", label: "رقم الصنف", minWidth: 70, defaultWidth: 100 },
  { key: "itemDescription", label: "وصف الصنف", minWidth: 120, defaultWidth: 200 },
  { key: "quantity", label: "الكمية", minWidth: 55, defaultWidth: 70 },
  { key: "uomCode", label: "الوحدة", minWidth: 55, defaultWidth: 70 },
  { key: "warehouse", label: "المستودع", minWidth: 60, defaultWidth: 80 },
  { key: "unitPrice", label: "سعر الوحدة", minWidth: 70, defaultWidth: 95 },
  { key: "discountPercent", label: "الخصم %", minWidth: 55, defaultWidth: 70 },
  { key: "taxCode", label: "كود الضريبة", minWidth: 65, defaultWidth: 85 },
  { key: "totalLC", label: "الإجمالي (م.م)", minWidth: 80, defaultWidth: 105 },
  { key: "cogsBranch", label: "فرع التكلفة", minWidth: 70, defaultWidth: 95 },
];

interface InvoiceCreationDialogProps {
  open: boolean;
  onClose: () => void;
  customerName: string;
  customerId: string;
  customerAddress?: string;
  customerPhone?: string;

  // ── External data from Container (replaces hardcoded mock data) ──
  externalProducts?: ApiProduct[];
  externalWarehouses?: ApiWarehouse[];
  externalPricelists?: { value: string; label: string }[];
  externalInvoiceTypes?: { value: string; label: string }[];
  selectedPricelistId?: number;
  onPricelistChange?: (id: number) => void;

  // ── Loading / submission state ──
  isContextLoading?: boolean;
  isSearchingProducts?: boolean;
  isSubmitting?: boolean;

  // ── Callbacks ──
  /** Fires when user types in the product search box */
  onProductSearch?: (query: string) => void;
  /** Fetch full details for a selected product (price, uom, warehouses) */
  onProductDetailFetch?: (productId: number) => Promise<ApiProductDetail | null>;
  /** Called with the order payload when user clicks "إضافة الفاتورة" */
  onCreateOrder?: (payload: CreateOrderPayload) => Promise<void>;

  // ── Result ──
  externalCreatedOrder?: CreatedOrder;
  contextError?: string;
}

const fmtDecimal = (n: number) =>
  new Intl.NumberFormat("ar-SA", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);

let lineIdCounter = 1;

// ─── localStorage key for form settings ─────────────────
const FORM_SETTINGS_KEY = "nour-nebras-invoice-form-settings";

function loadFormSettings(columns: ColumnDef[]): FormSettings {
  try {
    const stored = localStorage.getItem(FORM_SETTINGS_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as FormSettings;
      // Preserve saved column order, and append any new columns not yet saved
      const savedKeys = new Set(parsed.columnVisibility?.map((cv) => cv.key) || []);
      const merged = [
        ...(parsed.columnVisibility || []),
        ...columns
          .filter((c) => !savedKeys.has(c.key))
          .map((c) => ({ key: c.key, label: c.label, visible: true, active: true })),
      ];
      return { ...parsed, columnVisibility: merged };
    }
  } catch {}
  return {
    columnVisibility: columns.map((c) => ({ key: c.key, label: c.label, visible: true, active: true })),
    bgMode: "solid",
    bgColor: "transparent",
    bgTextColor: "",
    bgImage: null,
    bgOpacity: 100,
  };
}

function saveFormSettings(settings: FormSettings) {
  try {
    localStorage.setItem(FORM_SETTINGS_KEY, JSON.stringify(settings));
  } catch {}
}

// ─── Helper: compute muted text color from base text color ──
function getMutedTextColor(hex: string): string {
  if (!hex) return "";
  // Add alpha for muted variant (roughly 65% opacity)
  return hex + "A6";
}

// ─── Resizable Column Hook ──────────────────────────────
function useResizableColumns(columns: ColumnDef[]) {
  const [widths, setWidths] = useState<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    columns.forEach((c) => { map[c.key] = c.defaultWidth; });
    return map;
  });
  const [resizingCol, setResizingCol] = useState<string | null>(null);
  const resizingRef = useRef<{ colKey: string; startX: number; startWidth: number } | null>(null);

  // Ensure new columns get default widths
  const colKeys = columns.map((c) => c.key).join(",");
  useState(() => {
    columns.forEach((c) => {
      if (!(c.key in widths)) {
        setWidths((prev) => ({ ...prev, [c.key]: c.defaultWidth }));
      }
    });
  });

  const onMouseDown = useCallback(
    (colKey: string, e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const col = columns.find((c) => c.key === colKey);
      if (!col) return;
      resizingRef.current = { colKey, startX: e.clientX, startWidth: widths[colKey] ?? col.defaultWidth };
      setResizingCol(colKey);

      const onMouseMove = (ev: MouseEvent) => {
        if (!resizingRef.current) return;
        const { colKey: ck, startX, startWidth } = resizingRef.current;
        const colDef = columns.find((c) => c.key === ck);
        if (!colDef) return;
        // RTL: moving mouse left increases width
        const diff = startX - ev.clientX;
        const newWidth = Math.max(colDef.minWidth, startWidth + diff);
        setWidths((prev) => ({ ...prev, [ck]: newWidth }));
      };

      const onMouseUp = () => {
        resizingRef.current = null;
        setResizingCol(null);
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      };

      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    },
    [widths, columns]
  );

  return { widths, onMouseDown, resizingCol };
}

// ─── ERP Field Component ────────────────────────────────
function ErpField({
  label,
  children,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-[11px] text-muted-foreground whitespace-nowrap min-w-[90px] text-start">{label}</span>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function ErpReadonly({ value, ltr }: { value: string; ltr?: boolean }) {
  return (
    <div
      className="h-7 px-2 flex items-center text-[11px] text-foreground bg-muted/30 border border-border/40 rounded-sm"
      style={ltr ? { direction: "ltr", unicodeBidi: "embed" } : undefined}
    >
      {value}
    </div>
  );
}

function ErpInput({
  value,
  onChange,
  placeholder,
  ltr,
  className = "",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  ltr?: boolean;
  className?: string;
}) {
  return (
    <Input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`h-7 text-[11px] rounded-sm border-border/40 px-2 ${className}`}
      style={ltr ? { direction: "ltr" } : undefined}
    />
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════
export function InvoiceCreationDialog({
  open,
  onClose,
  customerName,
  customerId,
  customerAddress,
  customerPhone,
  externalProducts,
  externalWarehouses,
  externalPricelists,
  externalInvoiceTypes,
  selectedPricelistId,
  onPricelistChange,
  isContextLoading = false,
  isSearchingProducts = false,
  isSubmitting = false,
  onProductSearch,
  onProductDetailFetch,
  onCreateOrder,
  externalCreatedOrder,
  contextError,
}: InvoiceCreationDialogProps) {
  // ── State ──
  const [lines, setLines] = useState<InvoiceLineItem[]>([
    createEmptyLine(1),
  ]);
  const [activeTab, setActiveTab] = useState("contents");
  const [currency, setCurrency] = useState("SAR");
  const [contactPerson, setContactPerson] = useState(CONTACTS[0]);
  const [customerRef, setCustomerRef] = useState("");
  const [invType, setInvType] = useState("1");
  const [deliveryDate, setDeliveryDate] = useState("");
  const [salesEmployee, setSalesEmployee] = useState("");
  const [owner, setOwner] = useState("");
  const [discountPercent, setDiscountPercent] = useState(0);
  const [freight, setFreight] = useState(0);
  const [roundingEnabled, setRoundingEnabled] = useState(false);
  const [notes, setNotes] = useState("");
  const [selectedRow, setSelectedRow] = useState<string | null>(null);
  const [created, setCreated] = useState(false);
  const [savedDraft, setSavedDraft] = useState(false);
  const [productSearchQuery, setProductSearchQuery] = useState("");

  // Resolved data: prefer external, fall back to static
  const activeProducts   = (externalProducts && externalProducts.length > 0) ? externalProducts  : FALLBACK_PRODUCTS;
  const activeWarehouses = (externalWarehouses && externalWarehouses.length > 0) ? externalWarehouses : FALLBACK_WAREHOUSES;
  const activeInvTypes   = (externalInvoiceTypes && externalInvoiceTypes.length > 0) ? externalInvoiceTypes : FALLBACK_INV_TYPES;

  // Sync externalCreatedOrder → local created flag
  const prevCreatedOrderRef = useRef<CreatedOrder | undefined>(undefined);
  if (externalCreatedOrder && externalCreatedOrder !== prevCreatedOrderRef.current) {
    prevCreatedOrderRef.current = externalCreatedOrder;
    if (!created) setCreated(true);
  }

  // ── Form Settings State ──
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [formSettings, setFormSettings] = useState<FormSettings>(loadFormSettings(COLUMNS));

  // Compute visible columns based on settings order
  const visibleColumns = useMemo(() => {
    return formSettings.columnVisibility
      .filter((cv) => cv.visible)
      .map((cv) => {
        const colDef = COLUMNS.find((c) => c.key === cv.key)!;
        return colDef;
      });
  }, [formSettings.columnVisibility]);

  const { widths, onMouseDown, resizingCol } = useResizableColumns(visibleColumns);
  const tableRef = useRef<HTMLDivElement>(null);
  const [activeCell, setActiveCell] = useState<{ row: string; col: number } | null>(null);

  // ── Column Drag Reorder State ──
  const [dragColKey, setDragColKey] = useState<string | null>(null);
  const [dropTargetKey, setDropTargetKey] = useState<string | null>(null);
  const [dropSide, setDropSide] = useState<"before" | "after" | null>(null);

  const handleColDragStart = useCallback((colKey: string, e: React.DragEvent) => {
    setDragColKey(colKey);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", colKey);
    // Make the drag ghost semi-transparent
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = "0.5";
    }
  }, []);

  const handleColDragEnd = useCallback((e: React.DragEvent) => {
    setDragColKey(null);
    setDropTargetKey(null);
    setDropSide(null);
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = "1";
    }
  }, []);

  const handleColDragOver = useCallback((colKey: string, e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (colKey === dragColKey) {
      setDropTargetKey(null);
      setDropSide(null);
      return;
    }
    setDropTargetKey(colKey);
    // In RTL, right is start, left is end. Determine which side of the header mouse is on.
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const mouseX = e.clientX;
    const midX = rect.left + rect.width / 2;
    // RTL: if mouse is to the right of center → "before" (inserting before in visual order)
    // if mouse is to the left → "after"
    setDropSide(mouseX > midX ? "before" : "after");
  }, [dragColKey]);

  const handleColDrop = useCallback((targetColKey: string, e: React.DragEvent) => {
    e.preventDefault();
    const sourceKey = e.dataTransfer.getData("text/plain");
    if (!sourceKey || sourceKey === targetColKey) {
      setDragColKey(null);
      setDropTargetKey(null);
      setDropSide(null);
      return;
    }

    setFormSettings((prev) => {
      const colVis = [...prev.columnVisibility];
      const sourceIdx = colVis.findIndex((c) => c.key === sourceKey);
      const targetIdx = colVis.findIndex((c) => c.key === targetColKey);
      if (sourceIdx === -1 || targetIdx === -1) return prev;

      const [removed] = colVis.splice(sourceIdx, 1);
      // Recalculate target position after removal
      const newTargetIdx = colVis.findIndex((c) => c.key === targetColKey);
      const insertIdx = dropSide === "after" ? newTargetIdx + 1 : newTargetIdx;
      colVis.splice(insertIdx, 0, removed);

      const updated = { ...prev, columnVisibility: colVis };
      saveFormSettings(updated);
      return updated;
    });

    setDragColKey(null);
    setDropTargetKey(null);
    setDropSide(null);
  }, [dropSide]);

  const invoiceNumber = useMemo(() => {
    const num = Math.floor(Math.random() * 900000) + 100000;
    return `26${String(num).padStart(6, "0")}`;
  }, [open]);

  const today = "23.02.2026";

  // ── Line helpers ──
  function createEmptyLine(rowNum: number): InvoiceLineItem {
    return {
      id: `line-${lineIdCounter++}`,
      rowNum,
      productApiId: null,
      itemNo: "",
      itemDescription: "",
      quantity: 0,
      uomCode: "",
      uomApiId: null,
      warehouse: "",
      warehouseApiId: null,
      unitPrice: 0,
      discountPercent: 0,
      taxCode: "",
      totalLC: 0,
      cogsBranch: "الرئيسي",
    };
  }

  const addLine = useCallback(() => {
    setLines((prev) => {
      // Don't add if any existing line has no item selected
      const hasEmptyLine = prev.some((l) => !l.itemNo);
      if (hasEmptyLine) return prev;
      return [...prev, createEmptyLine(prev.length + 1)];
    });
  }, []);

  const removeLine = useCallback((id: string) => {
    setLines((prev) => {
      if (prev.length <= 1) return prev;
      return prev.filter((l) => l.id !== id).map((l, i) => ({ ...l, rowNum: i + 1 }));
    });
  }, []);

  /**
   * Called when the user picks a product from the row selector.
   * First applies immediate data from the product list, then enriches
   * with full detail (price per pricelist, stock per warehouse) if
   * the container provides an onProductDetailFetch callback.
   */
  const updateLineProduct = useCallback(async (lineId: string, productId: string) => {
    const numId = parseInt(productId, 10);
    const apiProduct = activeProducts.find((p) => p.id === numId);

    if (apiProduct) {
      // Immediate update with list-level data
      setLines((prev) =>
        prev.map((l) => {
          if (l.id !== lineId) return l;
          const qty = l.quantity || 1;
          const subtotal = qty * apiProduct.list_price;
          return {
            ...l,
            productApiId: apiProduct.id,
            itemNo: apiProduct.default_code || String(apiProduct.id),
            itemDescription: apiProduct.name,
            quantity: qty,
            uomCode: apiProduct.uom_id.name,
            uomApiId: apiProduct.uom_id.id,
            unitPrice: apiProduct.list_price,
            taxCode: "VAT15",
            totalLC: subtotal - subtotal * (l.discountPercent / 100),
          };
        })
      );

      // Enrich with full detail (pricelist price, default warehouse)
      if (onProductDetailFetch && apiProduct.id > 0) {
        const detail = await onProductDetailFetch(apiProduct.id);
        if (detail) {
          const defaultWarehouse = detail.warehouses[0];
          setLines((prev) =>
            prev.map((l) => {
              if (l.id !== lineId) return l;
              const qty = l.quantity || 1;
              const subtotal = qty * detail.price_unit;
              return {
                ...l,
                uomCode:      detail.product_uom_name,
                uomApiId:     detail.product_uom_id,
                unitPrice:    detail.price_unit,
                warehouse:    defaultWarehouse ? defaultWarehouse.code : l.warehouse,
                warehouseApiId: defaultWarehouse ? defaultWarehouse.id : l.warehouseApiId,
                totalLC: subtotal - subtotal * (l.discountPercent / 100),
              };
            })
          );
        }
      }
    }
  }, [activeProducts, onProductDetailFetch]);

  const updateLineField = useCallback((lineId: string, field: keyof InvoiceLineItem, value: number | string) => {
    setLines((prev) =>
      prev.map((l) => {
        if (l.id !== lineId) return l;
        const updated = { ...l, [field]: value };
        // recalc total
        const subtotal = updated.quantity * updated.unitPrice;
        updated.totalLC = subtotal - subtotal * (updated.discountPercent / 100);
        return updated;
      })
    );
  }, []);

  // ── Calculations ──
  const totalBeforeDiscount = useMemo(() => lines.reduce((s, l) => s + l.totalLC, 0), [lines]);
  const discountAmount = totalBeforeDiscount * (discountPercent / 100);
  const afterDiscount = totalBeforeDiscount - discountAmount;
  const taxAmount = afterDiscount * VAT_RATE;
  const rounding = roundingEnabled ? Math.round(afterDiscount + freight + taxAmount) - (afterDiscount + freight + taxAmount) : 0;
  const grandTotal = afterDiscount + freight + taxAmount + rounding;

  const hasValidLines = lines.some((l) => l.itemNo && l.quantity > 0);

  const handleReset = () => {
    lineIdCounter = 1;
    setLines([createEmptyLine(1)]);
    setActiveTab("contents");
    setCurrency("SAR");
    setContactPerson(CONTACTS[0]);
    setCustomerRef("");
    setInvType("1");
    setDeliveryDate("");
    setSalesEmployee("");
    setOwner("");
    setDiscountPercent(0);
    setFreight(0);
    setRoundingEnabled(false);
    setNotes("");
    setSelectedRow(null);
    setCreated(false);
    setSavedDraft(false);
    setProductSearchQuery("");
    prevCreatedOrderRef.current = undefined;
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  // ── Tab definitions ──
  const TABS = [
    { id: "contents", label: "المحتويات" },
    { id: "logistics", label: "اللوجستيات" },
    { id: "accounting", label: "المحاسبة" },
    { id: "attachments", label: "المرفقات" },
  ];

  return (
    <>
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent
        className="!max-w-[92vw] xl:!max-w-6xl !p-0 !gap-0 !h-[88vh] flex flex-col overflow-hidden border-border/50 !rounded-none sm:!rounded-lg"
        dir="rtl"
        style={
          formSettings.bgColor !== "transparent" && formSettings.bgMode === "solid"
            ? { backgroundColor: formSettings.bgColor }
            : formSettings.bgMode === "image" && formSettings.bgImage
              ? {
                  backgroundImage: `url(${formSettings.bgImage})`,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                }
              : undefined
        }
      >
        {/* Background image overlay for opacity */}
        {formSettings.bgMode === "image" && formSettings.bgImage && (
          <div
            className="absolute inset-0 z-0 pointer-events-none"
            style={{ backgroundColor: `rgba(var(--background-rgb, 0,0,0), ${1 - formSettings.bgOpacity / 100})` }}
          />
        )}
        <DialogTitle className="sr-only">أمر بيع - فاتورة جديدة</DialogTitle>
        <DialogDescription className="sr-only">نموذج إنشاء فاتورة للعميل {customerName}</DialogDescription>

        {/* ── Success State ── */}
        {created ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200, damping: 15 }}
              className="w-20 h-20 rounded-full bg-emerald-500/15 flex items-center justify-center"
            >
              <CheckCircle2 className="w-10 h-10 text-emerald-500" />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-center space-y-2"
            >
              <h3 className="text-foreground">تم إنشاء الفاتورة بنجاح</h3>
              <p className="text-sm text-muted-foreground">
                رقم الفاتورة:{" "}
                <span className="text-primary font-mono" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                  {externalCreatedOrder?.order_name ?? `2026-${invoiceNumber}`}
                </span>
              </p>
              {externalCreatedOrder?.sale_order_name && (
                <p className="text-xs text-muted-foreground">
                  أمر البيع:{" "}
                  <span className="text-primary font-mono" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                    {externalCreatedOrder.sale_order_name}
                  </span>
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                المبلغ الإجمالي:{" "}
                <span style={{ direction: "ltr", unicodeBidi: "embed" }}>
                  {fmtDecimal(externalCreatedOrder?.amount_total ?? grandTotal)} ر.س
                </span>
              </p>
            </motion.div>
            <div className="flex items-center gap-2 mt-4">
              <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={() => {}}>
                <Printer className="w-3.5 h-3.5" /> طباعة
              </Button>
              <Button variant="outline" size="sm" className="gap-1.5 text-xs" onClick={() => {}}>
                <Copy className="w-3.5 h-3.5" /> نسخ
              </Button>
              <Button
                size="sm"
                className="gap-1.5 text-xs bg-cyan-500 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] text-white hover:bg-cyan-600 dark:hover:from-[#AA771C] dark:hover:to-[#BF953F] border-none"
                onClick={handleClose}
              >
                إغلاق
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col h-full"
            style={formSettings.bgTextColor ? {
              '--foreground': formSettings.bgTextColor,
              '--muted-foreground': getMutedTextColor(formSettings.bgTextColor),
              '--card-foreground': formSettings.bgTextColor,
              color: formSettings.bgTextColor,
            } as React.CSSProperties : undefined}
          >
            {/* ═══ Title Bar ═══ */}
            <div className="flex items-center justify-between px-3 py-1.5 bg-gradient-to-l from-cyan-600 via-cyan-500 to-cyan-600 dark:from-[#2a261b] dark:via-[#1c1915] dark:to-[#2a261b] border-b border-cyan-700 dark:border-[#3d3520] shrink-0">
              <div className="flex items-center gap-2">
                <Receipt className="w-4 h-4 text-white dark:text-primary" />
                <span className="text-[12px] text-white dark:text-primary/90">
                  أمر بيع - فاتورة جديدة
                </span>
              </div>
              <div className="flex items-center gap-0.5">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-white/80 hover:text-white hover:bg-white/10 dark:text-primary/60 dark:hover:text-primary"
                  onClick={() => setSettingsOpen(true)}
                  title="إعدادات النموذج"
                >
                  <Settings2 className="w-3.5 h-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-white/80 hover:text-white hover:bg-white/10 dark:text-primary/60 dark:hover:text-primary"
                  onClick={handleClose}
                >
                  <X className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>

            {/* ═══ Context loading / error banners ═══ */}
            {isContextLoading && (
              <div className="flex items-center gap-2 px-4 py-1.5 bg-primary/5 border-b border-primary/10 text-[10px] text-primary shrink-0">
                <Loader2 className="w-3 h-3 animate-spin" />
                جاري تحميل بيانات الفاتورة...
              </div>
            )}
            {contextError && !isContextLoading && (
              <div className="flex items-center gap-2 px-4 py-1.5 bg-red-500/10 border-b border-red-500/20 text-[10px] text-red-500 shrink-0">
                ⚠ {contextError}
              </div>
            )}

            {/* ═══ Header Fields ═══ */}
            <div className="px-4 py-3 border-b border-border/30 bg-card/30 shrink-0">
              <div className="flex justify-between gap-8">
                {/* Left side */}
                <div className="w-[340px] space-y-2">
                  <ErpField label="العميل">
                    <div className="flex items-center gap-1">
                      <div className="h-7 flex-1 px-2 flex items-center text-[11px] text-primary bg-primary/5 border border-primary/20 rounded-sm">
                        {customerId}
                      </div>
                    </div>
                  </ErpField>
                  <ErpField label="الاسم">
                    <ErpReadonly value={customerName} />
                  </ErpField>
                  <ErpField label="جهة الاتصال">
                    <Select value={contactPerson} onValueChange={setContactPerson} dir="rtl">
                      <SelectTrigger className="h-7 text-[11px] rounded-sm border-border/40" size="sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CONTACTS.map((c) => (
                          <SelectItem key={c} value={c} className="text-[11px]">{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </ErpField>
                  <ErpField label="مرجع العميل">
                    <ErpInput value={customerRef} onChange={setCustomerRef} placeholder="" />
                  </ErpField>
                  <ErpField label="العملة المحلية">
                    <Select value={currency} onValueChange={setCurrency} dir="rtl">
                      <SelectTrigger className="h-7 text-[11px] rounded-sm border-border/40 w-40" size="sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CURRENCIES.map((c) => (
                          <SelectItem key={c.value} value={c.value} className="text-[11px]">{c.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </ErpField>
                  <ErpField label="نوع الفاتورة">
                    <Select value={invType} onValueChange={setInvType} dir="rtl">
                      <SelectTrigger className="h-7 text-[11px] rounded-sm border-border/40" size="sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {activeInvTypes.map((t) => (
                          <SelectItem key={t.value} value={t.value} className="text-[11px]">{t.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </ErpField>
                </div>

                {/* Right side */}
                <div className="w-[280px] space-y-2">
                  <ErpField label="الرقم">
                    <div className="flex items-center gap-1">
                      <ErpReadonly value="2026" ltr />
                      <div className="h-7 px-2 flex items-center text-[11px] text-foreground bg-muted/30 border border-border/40 rounded-sm flex-1" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {invoiceNumber}
                      </div>
                    </div>
                  </ErpField>
                  <ErpField label="الحالة">
                    <div className="h-7 px-2 flex items-center text-[11px] rounded-sm border border-border/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      مفتوح
                    </div>
                  </ErpField>
                  <ErpField label="تاريخ الترحيل">
                    <ErpReadonly value={today} ltr />
                  </ErpField>
                  <ErpField label="تاريخ التسليم">
                    <ErpInput value={deliveryDate} onChange={setDeliveryDate} placeholder="DD.MM.YYYY" ltr />
                  </ErpField>
                  <ErpField label="تاريخ المستند">
                    <ErpReadonly value={today} ltr />
                  </ErpField>
                </div>
              </div>
            </div>

            {/* ═══ Tab Navigation ═══ */}
            <div className="flex items-center border-b border-border/30 bg-card/20 shrink-0">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-5 py-2 text-[11px] border-b-2 transition-all ${
                    activeTab === tab.id
                      ? "border-primary text-primary bg-primary/5"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/20"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
              {/* Item/Service Type on the right of tabs */}
              <div className="ms-auto pe-3 flex items-center gap-2">
                <span className="text-[10px] text-muted-foreground">نوع الصنف/الخدمة</span>
                <Select defaultValue="item" dir="rtl">
                  <SelectTrigger className="h-6 text-[10px] rounded-sm border-border/40 w-24" size="sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="item" className="text-[10px]">صنف</SelectItem>
                    <SelectItem value="service" className="text-[10px]">خدمة</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* ═══ Table Content ═══ */}
            <div className="flex-1 min-h-0 flex flex-col">
              {activeTab === "contents" && (
                <div className="flex-1 min-h-0 flex flex-col">
                  {/* Action bar */}
                  <div className="flex items-center gap-2 px-2 py-1 border-b border-border/20 bg-muted/10 shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 text-[10px] gap-1 text-primary hover:bg-primary/5 px-2"
                      onClick={addLine}
                      disabled={lines.some((l) => !l.itemNo)}
                    >
                      <Plus className="w-3 h-3" /> إضافة سطر
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 text-[10px] gap-1 text-red-500 hover:bg-red-500/5 px-2"
                      onClick={() => selectedRow && removeLine(selectedRow)}
                      disabled={!selectedRow || lines.length <= 1}
                    >
                      <Trash2 className="w-3 h-3" /> حذف سطر
                    </Button>
                    {/* Product search box */}
                    <div className="ms-auto flex items-center gap-1 relative">
                      <Input
                        value={productSearchQuery}
                        onChange={(e) => {
                          setProductSearchQuery(e.target.value);
                          onProductSearch?.(e.target.value);
                        }}
                        placeholder="بحث عن منتج..."
                        className="h-6 text-[10px] rounded-sm border-border/40 w-40 px-2"
                        dir="rtl"
                      />
                      {isSearchingProducts && (
                        <Loader2 className="w-3 h-3 animate-spin text-muted-foreground absolute start-2" />
                      )}
                    </div>
                  </div>

                  {/* Resizable Table */}
                  <div className="flex-1 min-h-0 overflow-hidden" ref={tableRef}>
                    <ScrollArea className="h-full" dir="rtl">
                      <table className="min-w-max border-collapse" style={{ tableLayout: "fixed" }}>
                        {/* colgroup for widths */}
                        <colgroup>
                          {visibleColumns.map((col, colIdx) => (
                            <col key={col.key} style={{ width: widths[col.key], minWidth: col.minWidth }} />
                          ))}
                        </colgroup>

                        {/* Table Header */}
                        <thead className="sticky top-0 z-10">
                          <tr className="bg-gradient-to-b from-slate-100 to-slate-50 dark:from-[#1a1d24] dark:to-[#15171c]">
                            {visibleColumns.map((col, colIdx) => {
                              const isDragTarget = dropTargetKey === col.key && dragColKey !== col.key;
                              return (
                              <th
                                key={col.key}
                                draggable
                                onDragStart={(e) => handleColDragStart(col.key, e)}
                                onDragEnd={handleColDragEnd}
                                onDragOver={(e) => handleColDragOver(col.key, e)}
                                onDrop={(e) => handleColDrop(col.key, e)}
                                className={`relative px-1 py-2 text-[11px] text-foreground/80 select-none text-center border border-slate-300 dark:border-[#2a2d35] cursor-grab active:cursor-grabbing ${
                                  resizingCol === col.key ? "bg-primary/10" : ""
                                } ${activeCell?.col === colIdx ? "bg-primary/5" : ""} ${
                                  dragColKey === col.key ? "opacity-50" : ""
                                }`}
                                style={{ width: widths[col.key], minWidth: col.minWidth, fontWeight: 600 }}
                              >
                                <span className="truncate block">{col.label}</span>
                                {/* Resize Handle */}
                                <div
                                  className={`absolute start-0 top-0 bottom-0 w-[4px] cursor-col-resize z-20 transition-colors ${
                                    resizingCol === col.key
                                      ? "bg-blue-500 dark:bg-primary"
                                      : "hover:bg-blue-400/60 dark:hover:bg-primary/40"
                                  }`}
                                  onMouseDown={(e) => onMouseDown(col.key, e)}
                                  draggable={false}
                                />
                                {/* Drop indicator line */}
                                {isDragTarget && dropSide === "before" && (
                                  <div className="absolute end-0 top-0 bottom-0 w-[3px] bg-blue-500 dark:bg-primary z-30 rounded-full" />
                                )}
                                {isDragTarget && dropSide === "after" && (
                                  <div className="absolute start-0 top-0 bottom-0 w-[3px] bg-blue-500 dark:bg-primary z-30 rounded-full" />
                                )}
                              </th>
                              );
                            })}
                          </tr>
                        </thead>

                        <tbody>
                          {/* Data Rows */}
                          {lines.map((line) => (
                            <tr
                              key={line.id}
                              className={`transition-colors ${
                                selectedRow === line.id
                                  ? "bg-blue-50/80 dark:bg-primary/8"
                                  : "hover:bg-slate-50 dark:hover:bg-white/[0.02]"
                              }`}
                              onClick={() => setSelectedRow(line.id)}
                            >
                              {visibleColumns.map((col, colIdx) => {
                                const isActive = activeCell?.row === line.id && activeCell?.col === colIdx;
                                const isActiveRow = selectedRow === line.id;
                                const isActiveCol = activeCell?.col === colIdx;
                                return (
                                  <td
                                    key={col.key}
                                    className={`relative border border-slate-200 dark:border-[#232630] px-0.5 ${
                                      isActive
                                        ? "!border-2 !border-blue-500 dark:!border-primary bg-white dark:bg-[#1a1d24]"
                                        : isActiveRow
                                          ? "bg-blue-50/40 dark:bg-primary/5"
                                          : isActiveCol
                                            ? "bg-blue-50/20 dark:bg-primary/[0.02]"
                                            : ""
                                    }`}
                                    style={{ width: widths[col.key], minWidth: col.minWidth }}
                                    onClick={() => { if (line.itemNo) addLine(); }}
                                    onFocus={() => { if (line.itemNo) addLine(); }}
                                  >
                                    {renderCell(line, col.key, colIdx, updateLineProduct, updateLineField, widths, activeCell, setActiveCell, activeProducts, activeWarehouses)}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}

                          {/* Empty rows for ERP/Excel look */}
                          {Array.from({ length: Math.max(0, 6 - lines.length) }).map((_, i) => (
                            <tr
                              key={`empty-${i}`}
                              className="h-8 hover:bg-slate-50/50 dark:hover:bg-white/[0.01] cursor-pointer"
                              onClick={addLine}
                            >
                              {visibleColumns.map((col, colIdx) => (
                                <td
                                  key={col.key}
                                  className="border border-slate-200 dark:border-[#232630]"
                                  style={{ width: widths[col.key], minWidth: col.minWidth }}
                                />
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </ScrollArea>
                  </div>
                </div>
              )}

              {activeTab === "logistics" && (
                <div className="flex-1 min-h-0 p-5">
                  <div className="space-y-4 max-w-md">
                    <ErpField label="عنوان الشحن">
                      <ErpReadonly value={customerAddress || "الرياض، حي النخيل، شارع الملك فهد"} />
                    </ErpField>
                    <ErpField label="طريقة الشحن">
                      <Select defaultValue="express" dir="rtl">
                        <SelectTrigger className="h-7 text-[11px] rounded-sm border-border/40" size="sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="express" className="text-[11px]">توصيل سريع (24 ساعة)</SelectItem>
                          <SelectItem value="standard" className="text-[11px]">توصيل عادي (3-5 أيام)</SelectItem>
                          <SelectItem value="pickup" className="text-[11px]">استلام من الفرع</SelectItem>
                        </SelectContent>
                      </Select>
                    </ErpField>
                    <ErpField label="ملاحظات الشحن">
                      <textarea
                        className="w-full h-20 px-2 py-1.5 text-[11px] rounded-sm border border-border/40 bg-background resize-none focus:outline-none focus:ring-1 focus:ring-primary/30"
                        placeholder="ملاحظات إضافية للشحن..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                    </ErpField>
                  </div>
                </div>
              )}

              {activeTab === "accounting" && (
                <div className="flex-1 min-h-0 p-5">
                  <div className="space-y-4 max-w-md">
                    <ErpField label="الحساب">
                      <ErpReadonly value="حسابات المدينين" />
                    </ErpField>
                    <ErpField label="مركز التكلفة">
                      <ErpReadonly value="الفرع الرئيسي - الرياض" />
                    </ErpField>
                    <ErpField label="المشروع">
                      <ErpInput value="" onChange={() => {}} placeholder="اختياري" />
                    </ErpField>
                    <ErpField label="كود الضريبة">
                      <ErpReadonly value="VAT15 - ضريبة القيمة المضافة 15%" />
                    </ErpField>
                  </div>
                </div>
              )}

              {activeTab === "attachments" && (
                <div className="flex-1 min-h-0 p-5">
                  <div className="flex flex-col items-center justify-center gap-3 py-10 text-muted-foreground">
                    <div className="w-12 h-12 rounded-full bg-muted/20 flex items-center justify-center">
                      <Plus className="w-5 h-5" />
                    </div>
                    <p className="text-xs">لا توجد مرفقات. اضغط لإضافة مرفق.</p>
                  </div>
                </div>
              )}
            </div>

            {/* ═══ Footer ═══ */}
            <div className="border-t border-border/30 bg-card/30 shrink-0">
              <div className="px-4 py-3 flex gap-8">
                {/* Left: Sales Employee & Owner */}
                <div className="flex-1 space-y-2">
                  <ErpField label="موظف المبيعات">
                    <Select value={salesEmployee || "__none"} onValueChange={(v) => setSalesEmployee(v === "__none" ? "" : v)} dir="rtl">
                      <SelectTrigger className="h-7 text-[11px] rounded-sm border-border/40" size="sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none" className="text-[11px]">-بدون موظف مبيعات-</SelectItem>
                        <SelectItem value="سارة الحربي" className="text-[11px]">سارة الحربي</SelectItem>
                        <SelectItem value="محمد الخالدي" className="text-[11px]">محمد الخالدي</SelectItem>
                        <SelectItem value="فاطمة السالم" className="text-[11px]">فاطمة السالم</SelectItem>
                      </SelectContent>
                    </Select>
                  </ErpField>
                  <ErpField label="المالك">
                    <ErpInput value={owner} onChange={setOwner} placeholder="" />
                  </ErpField>
                </div>

                {/* Right: Totals */}
                <div className="w-[320px] space-y-1.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-muted-foreground">الإجمالي قبل الخصم</span>
                    <div className="h-7 w-32 px-2 flex items-center justify-end text-foreground bg-muted/20 border border-border/30 rounded-sm" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {fmtDecimal(totalBeforeDiscount)}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-muted-foreground flex items-center gap-1">الخصم</span>
                    <div className="flex items-center gap-1">
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        value={discountPercent}
                        onChange={(e) => setDiscountPercent(Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)))}
                        className="h-7 w-16 text-[11px] text-center rounded-sm border-border/40 px-1"
                        style={{ direction: "ltr" }}
                      />
                      <span className="text-[10px] text-muted-foreground">%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-muted-foreground">الشحن</span>
                    <Input
                      type="number"
                      min={0}
                      value={freight}
                      onChange={(e) => setFreight(Math.max(0, parseFloat(e.target.value) || 0))}
                      className="h-7 w-32 text-[11px] text-end rounded-sm border-border/40 px-2"
                      style={{ direction: "ltr" }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-muted-foreground flex items-center gap-1.5">
                      <Checkbox
                        checked={roundingEnabled}
                        onCheckedChange={(c) => setRoundingEnabled(!!c)}
                        className="h-3.5 w-3.5"
                      />
                      التقريب
                    </span>
                    <div className="h-7 w-32 px-2 flex items-center justify-end text-[11px] text-foreground bg-muted/20 border border-border/30 rounded-sm" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {currency === "SAR" ? "SAR" : currency} {fmtDecimal(rounding)}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-muted-foreground">الضريبة (15%)</span>
                    <div className="h-7 w-32 px-2 flex items-center justify-end text-foreground bg-muted/20 border border-border/30 rounded-sm" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {fmtDecimal(taxAmount)}
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-border/30">
                    <span className="text-xs text-foreground">الإجمالي</span>
                    <div className="h-8 w-32 px-2 flex items-center justify-end text-sm text-primary bg-primary/5 border border-primary/20 rounded-sm" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {fmtDecimal(grandTotal)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="px-4 py-2 border-t border-border/20 flex items-center justify-between bg-muted/10">
                <span className="text-[10px] text-muted-foreground">
                  {lines.filter((l) => l.itemNo).length} بنود
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-[10px] gap-1 rounded-sm"
                    onClick={handleClose}
                  >
                    إلغاء
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-[10px] gap-1 rounded-sm"
                    onClick={() => {
                      setSavedDraft(true);
                      setTimeout(() => setSavedDraft(false), 2000);
                    }}
                    disabled={!hasValidLines}
                  >
                    <Save className="w-3 h-3" />
                    {savedDraft ? "تم الحفظ ✓" : "حفظ كمسودة"}
                  </Button>
                  <Button
                    size="sm"
                    className="h-7 text-[10px] gap-1 rounded-sm bg-cyan-500 dark:bg-gradient-to-r dark:from-[#BF953F] dark:to-[#D4AF37] text-white hover:bg-cyan-600 dark:hover:from-[#AA771C] dark:hover:to-[#BF953F] border-none shadow-sm"
                    onClick={async () => {
                      if (onCreateOrder) {
                        // Build real payload for the API
                        const orderLines: CreateOrderLine[] = lines
                          .filter((l) => l.productApiId && l.productApiId > 0 && l.quantity > 0)
                          .map((l, idx) => ({
                            product_id:      l.productApiId!,
                            product_uom_id:  l.uomApiId ?? 1,
                            warehouse_id:    l.warehouseApiId ?? (activeWarehouses[0]?.id ?? 1),
                            quantity:        l.quantity,
                            unit_price:      l.unitPrice,
                            discount_percent: l.discountPercent,
                            sequence:        (idx + 1) * 10,
                          }));
                        const payload: CreateOrderPayload = {
                          partner_id:    0, // container will fill this
                          pricelist_id:  selectedPricelistId ?? 1,
                          invoice_type:  invType,
                          order_lines:   orderLines,
                        };
                        await onCreateOrder(payload);
                      } else {
                        // Fallback (no container): just show success screen
                        setCreated(true);
                      }
                    }}
                    disabled={!hasValidLines || isSubmitting}
                  >
                    {isSubmitting ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Receipt className="w-3 h-3" />
                    )}
                    {isSubmitting ? "جاري الإنشاء..." : "إضافة الفاتورة"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>

    {/* ── Form Settings Dialog ── */}
    <FormSettingsDialog
      open={settingsOpen}
      onClose={() => setSettingsOpen(false)}
      settings={formSettings}
      onApply={(settings) => {
        setFormSettings(settings);
        saveFormSettings(settings);
      }}
    />
    </>
  );
}

// ─── Cell Renderer ──────────────────────────────────────
function renderCell(
  line: InvoiceLineItem,
  colKey: string,
  colIdx: number,
  updateLineProduct: (lineId: string, productId: string) => void,
  updateLineField: (lineId: string, field: keyof InvoiceLineItem, value: number | string) => void,
  widths: Record<string, number>,
  activeCell: { row: string; col: number } | null,
  setActiveCell: (cell: { row: string; col: number } | null) => void,
  products: ApiProduct[],
  warehouses: ApiWarehouse[],
) {
  const cellClass = "w-full h-8 text-xs";

  switch (colKey) {
    case "rowNum":
      return (
        <div className={`${cellClass} flex items-center justify-center text-muted-foreground`}>
          {line.rowNum}
        </div>
      );

    case "itemNo":
      return (
        <Select
          value={line.productApiId ? String(line.productApiId) : ""}
          onValueChange={(val) => updateLineProduct(line.id, val)}
          dir="rtl"
        >
          <SelectTrigger className="h-8 text-xs rounded-none border-0 bg-transparent shadow-none px-1 w-full" size="sm">
            <SelectValue placeholder="—">
              {line.itemNo || "—"}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {products.map((p) => (
              <SelectItem key={p.id} value={String(p.id)} className="text-xs">
                <span className="font-mono text-[10px]" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                  {p.default_code || String(p.id)}
                </span>
                <span className="ms-2 text-muted-foreground">{p.name}</span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );

    case "itemDescription":
      return (
        <div className={`${cellClass} flex items-center px-1.5 text-foreground truncate`}>
          {line.itemDescription || <span className="text-muted-foreground/50">—</span>}
        </div>
      );

    case "quantity":
      return (
        <Input
          type="number"
          min={0}
          value={line.quantity || ""}
          onChange={(e) => updateLineField(line.id, "quantity", Math.max(0, parseInt(e.target.value) || 0))}
          className="h-8 text-xs text-center rounded-none border-0 bg-transparent shadow-none px-1"
          style={{ direction: "ltr" }}
          onFocus={() => setActiveCell({ row: line.id, col: colIdx })}
          onBlur={() => setActiveCell(null)}
        />
      );

    case "uomCode":
      return (
        <div className={`${cellClass} flex items-center justify-center text-muted-foreground`}>
          {line.uomCode || "—"}
        </div>
      );

    case "warehouse":
      return line.itemNo ? (
        <Select
          value={line.warehouse || (warehouses[0]?.code ?? "")}
          onValueChange={(val) => {
            const wh = warehouses.find((w) => w.code === val);
            updateLineField(line.id, "warehouse", val);
            if (wh) updateLineField(line.id, "warehouseApiId", wh.id);
          }}
          dir="rtl"
        >
          <SelectTrigger className="h-8 text-xs rounded-none border-0 bg-transparent shadow-none px-0.5 w-full" size="sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {warehouses.map((w) => (
              <SelectItem key={w.id} value={w.code} className="text-xs">
                {w.code}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <div className={`${cellClass} flex items-center justify-center text-muted-foreground`}>—</div>
      );

    case "unitPrice":
      return (
        <Input
          type="number"
          min={0}
          value={line.unitPrice || ""}
          onChange={(e) => updateLineField(line.id, "unitPrice", Math.max(0, parseFloat(e.target.value) || 0))}
          className="h-8 text-xs text-center rounded-none border-0 bg-transparent shadow-none px-1"
          style={{ direction: "ltr" }}
          onFocus={() => setActiveCell({ row: line.id, col: colIdx })}
          onBlur={() => setActiveCell(null)}
        />
      );

    case "discountPercent":
      return (
        <Input
          type="number"
          min={0}
          max={100}
          value={line.discountPercent || ""}
          onChange={(e) => updateLineField(line.id, "discountPercent", Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)))}
          className="h-8 text-xs text-center rounded-none border-0 bg-transparent shadow-none px-1"
          style={{ direction: "ltr" }}
          onFocus={() => setActiveCell({ row: line.id, col: colIdx })}
          onBlur={() => setActiveCell(null)}
        />
      );

    case "taxCode":
      return (
        <div className={`${cellClass} flex items-center justify-center text-muted-foreground`} style={{ direction: "ltr", unicodeBidi: "embed" }}>
          {line.taxCode || "—"}
        </div>
      );

    case "totalLC":
      return (
        <div className={`${cellClass} flex items-center justify-center text-foreground`} style={{ direction: "ltr", unicodeBidi: "embed" }}>
          {line.totalLC ? fmtDecimal(line.totalLC) : "0.00"}
        </div>
      );

    case "cogsBranch":
      return (
        <div className={`${cellClass} flex items-center justify-center text-muted-foreground`}>
          {line.cogsBranch || "—"}
        </div>
      );

    default:
      return null;
  }
}