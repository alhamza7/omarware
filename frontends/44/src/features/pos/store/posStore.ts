import { create } from 'zustand';
import type {
  PosSetup,
  Customer,
  Order,
  OrderLine,
} from '../../../types/pos';

export interface OrderLineLocal extends OrderLine {
  /** Price in IQD = unit_price × exchange_rate */
  unit_price_iqd: number;
}

export interface PosStore {
  // ── Setup ─────────────────────────────────────────────────
  setup:          PosSetup | null;
  isSetupLoaded:  boolean;
  setupError:     string | null;

  // ── Session / User ─────────────────────────────────────────
  userName:       string;
  companyName:    string;
  exchangeRate:   number;

  // ── Current Order ──────────────────────────────────────────
  currentOrder:   Order | null;
  orderLines:     OrderLineLocal[];
  isOrderLoading: boolean;
  orderError:     string | null;

  // ── Customer ───────────────────────────────────────────────
  selectedCustomer:  Customer | null;
  customerSearch:    string;

  // ── Selected Pricelist / Warehouse / Invoice type ──────────
  pricelistId:    number | null;
  warehouseId:    number | null;
  invoiceType:    string;

  // ── Actions ────────────────────────────────────────────────
  setSetup:           (s: PosSetup) => void;
  setSetupError:      (e: string | null) => void;
  setSession:         (userName: string, companyName: string, rate: number) => void;
  setCurrentOrder:    (o: Order | null) => void;
  setOrderLines:      (lines: OrderLineLocal[]) => void;
  addOrUpdateLine:    (line: OrderLineLocal) => void;
  removeLine:         (lineId: number) => void;
  setOrderLoading:    (v: boolean) => void;
  setOrderError:      (e: string | null) => void;
  setSelectedCustomer:(c: Customer | null) => void;
  setCustomerSearch:  (q: string) => void;
  setPricelistId:     (id: number | null) => void;
  setWarehouseId:     (id: number | null) => void;
  setInvoiceType:     (t: string) => void;
  setExchangeRate:    (rate: number) => void;
  resetOrder:         () => void;
}

export const usePosStore = create<PosStore>((set) => ({
  setup:            null,
  isSetupLoaded:    false,
  setupError:       null,

  userName:         '',
  companyName:      '',
  exchangeRate:     1500,

  currentOrder:     null,
  orderLines:       [],
  isOrderLoading:   false,
  orderError:       null,

  selectedCustomer: null,
  customerSearch:   '',

  pricelistId:      null,
  warehouseId:      null,
  invoiceType:      '1',

  // ── Setters ─────────────────────────────────────────────
  setSetup: (setup) =>
    set({
      setup,
      isSetupLoaded:  true,
      setupError:     null,
      exchangeRate:   setup.exchange_rate,
      pricelistId:    setup.default_pricelist_id ?? null,
    }),

  setSetupError:   (setupError) => set({ setupError }),

  setSession: (userName, companyName, exchangeRate) =>
    set({ userName, companyName, exchangeRate }),

  setCurrentOrder: (currentOrder) =>
    set({ currentOrder }),

  setOrderLines: (orderLines) => set({ orderLines }),

  addOrUpdateLine: (line) =>
    set((state) => {
      const exists = state.orderLines.find((l) => l.id === line.id);
      return {
        orderLines: exists
          ? state.orderLines.map((l) => (l.id === line.id ? line : l))
          : [...state.orderLines, line],
      };
    }),

  removeLine: (lineId) =>
    set((state) => ({
      orderLines: state.orderLines.filter((l) => l.id !== lineId),
    })),

  setOrderLoading: (isOrderLoading) => set({ isOrderLoading }),

  setOrderError: (orderError) => set({ orderError }),

  setSelectedCustomer: (selectedCustomer) => set({ selectedCustomer }),

  setCustomerSearch: (customerSearch) => set({ customerSearch }),

  setPricelistId: (pricelistId) => set({ pricelistId }),

  setWarehouseId: (warehouseId) => set({ warehouseId }),

  setInvoiceType: (invoiceType) => set({ invoiceType }),

  setExchangeRate: (exchangeRate) => set({ exchangeRate }),

  resetOrder: () =>
    set({
      currentOrder:     null,
      orderLines:       [],
      selectedCustomer: null,
      orderError:       null,
      invoiceType:      '1',
    }),
}));
