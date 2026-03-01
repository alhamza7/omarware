import { useCallback } from 'react';
import type { PosStore, OrderLineLocal } from '../store/posStore';
import { usePosStore } from '../store/posStore';
import posPerfumeApi from '../../../services/posPerfumeApi';
import type { Order, OrderLine } from '../../../types/pos';

/** Map an API OrderLine to the store's local format (with IQD price). */
function toLocalLine(line: OrderLine, exchangeRate: number): OrderLineLocal {
  return {
    ...line,
    unit_price_iqd: (line.unit_price ?? 0) * exchangeRate,
  };
}

/** Map a full Order's lines into the store. */
function syncLinesFromOrder(order: Order, exchangeRate: number, store: PosStore) {
  const lines = (order.order_lines ?? []).map((l) => toLocalLine(l, exchangeRate));
  store.setOrderLines(lines);
}

/**
 * All order CRUD operations — create, load, add/update/delete lines,
 * confirm, quotation, cancel, draft.
 */
export function useOrder() {
  const store = usePosStore();

  /** Create a new blank draft order. */
  const createOrder = useCallback(async () => {
    store.setOrderLoading(true);
    store.setOrderError(null);
    try {
      const res = await posPerfumeApi.createOrder({
        ...(store.selectedCustomer?.id ? { partner_id: store.selectedCustomer.id } : {}),
        pricelist_id:  store.pricelistId ?? undefined,
        invoice_type:  store.invoiceType as '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8',
        exchange_rate: store.exchangeRate,
      });
      if (res.success && res.data) {
        store.setCurrentOrder(res.data);
        syncLinesFromOrder(res.data, store.exchangeRate, store);
      } else {
        store.setOrderError(res.error ?? 'Failed to create order');
      }
      return res;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Network error';
      store.setOrderError(msg);
      return { success: false, error: msg };
    } finally {
      store.setOrderLoading(false);
    }
  }, [store]);

  /** Load an existing order by ID. */
  const loadOrder = useCallback(async (orderId: number) => {
    store.setOrderLoading(true);
    store.setOrderError(null);
    try {
      const res = await posPerfumeApi.getOrder(orderId);
      if (res.success && res.data) {
        store.setCurrentOrder(res.data);
        syncLinesFromOrder(res.data, store.exchangeRate, store);
        if (res.data.partner_id) {
          store.setSelectedCustomer({
            id:     res.data.partner_id.id,
            name:   res.data.partner_id.name,
            phone:  res.data.partner_id.phone,
            mobile: res.data.partner_id.mobile ?? '',
            email:  res.data.partner_id.email ?? '',
            ref:    '',
            street: '',
            city:   '',
          } as never);
        }
      } else {
        store.setOrderError(res.error ?? 'Failed to load order');
      }
      return res;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Network error';
      store.setOrderError(msg);
      return { success: false, error: msg };
    } finally {
      store.setOrderLoading(false);
    }
  }, [store]);

  /**
   * Add a product line to the current order.
   * Auto-creates the order if none exists.
   */
  const addLine = useCallback(async (lineData: {
    product_id:       number;
    product_uom_id?:  number;
    warehouse_id:     number;
    quantity?:        number;
    unit_price?:      number;
    discount_percent?: number;
    custom_product_name?: string;
    location_id?:     number;
  }) => {
    let orderId = store.currentOrder?.id;

    // Auto-create order if none exists
    if (!orderId) {
      const createRes = await createOrder();
      if (!createRes.success || !(createRes as { data?: { id: number } }).data) return;
      orderId = (createRes as { data?: { id: number } }).data!.id;
    }

    store.setOrderLoading(true);
    try {
      const res = await posPerfumeApi.addOrderLine(orderId!, lineData);
      if (res.success && res.data) {
        store.addOrUpdateLine(toLocalLine(res.data, store.exchangeRate));
        // Refresh order totals
        const orderRes = await posPerfumeApi.getOrder(orderId!);
        if (orderRes.success && orderRes.data) {
          store.setCurrentOrder(orderRes.data);
        }
      } else {
        store.setOrderError(res.error ?? 'Failed to add line');
      }
    } catch (err) {
      store.setOrderError(err instanceof Error ? err.message : 'Network error');
    } finally {
      store.setOrderLoading(false);
    }
  }, [store, createOrder]);

  /** Update quantity or discount on an existing line. */
  const updateLine = useCallback(async (
    lineId: number,
    changes: { quantity?: number; discount_percent?: number; unit_price?: number },
  ) => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return;

    try {
      const res = await posPerfumeApi.updateOrderLine(orderId, lineId, changes);
      if (res.success && res.data) {
        store.addOrUpdateLine(toLocalLine(res.data, store.exchangeRate));
        const orderRes = await posPerfumeApi.getOrder(orderId);
        if (orderRes.success && orderRes.data) store.setCurrentOrder(orderRes.data);
      } else {
        store.setOrderError(res.error ?? 'Failed to update line');
      }
    } catch (err) {
      store.setOrderError(err instanceof Error ? err.message : 'Network error');
    }
  }, [store]);

  /** Delete a line from the current order. */
  const deleteLine = useCallback(async (lineId: number) => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return;

    try {
      const res = await posPerfumeApi.deleteOrderLine(orderId, lineId);
      if (res.success) {
        store.removeLine(lineId);
        const orderRes = await posPerfumeApi.getOrder(orderId);
        if (orderRes.success && orderRes.data) store.setCurrentOrder(orderRes.data);
      } else {
        store.setOrderError(res.error ?? 'Failed to delete line');
      }
    } catch (err) {
      store.setOrderError(err instanceof Error ? err.message : 'Network error');
    }
  }, [store]);

  /** Confirm → creates Sale Order + SAP sync */
  const confirmOrder = useCallback(async () => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return;
    store.setOrderLoading(true);
    try {
      const res = await posPerfumeApi.confirmOrder(orderId);
      if (res.success && res.data) {
        const orderRes = await posPerfumeApi.getOrder(orderId);
        if (orderRes.success && orderRes.data) store.setCurrentOrder(orderRes.data);
      } else {
        store.setOrderError(res.error ?? 'Confirm failed');
      }
      return res;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Network error';
      store.setOrderError(msg);
      return { success: false, error: msg };
    } finally {
      store.setOrderLoading(false);
    }
  }, [store]);

  /** Set order to quotation state */
  const quotationOrder = useCallback(async () => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return;
    store.setOrderLoading(true);
    try {
      const res = await posPerfumeApi.quotationOrder(orderId);
      if (res.success) {
        const orderRes = await posPerfumeApi.getOrder(orderId);
        if (orderRes.success && orderRes.data) store.setCurrentOrder(orderRes.data);
      } else {
        store.setOrderError(res.error ?? 'Quotation failed');
      }
    } finally {
      store.setOrderLoading(false);
    }
  }, [store]);

  /** Cancel the current order */
  const cancelOrder = useCallback(async () => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return;
    store.setOrderLoading(true);
    try {
      const res = await posPerfumeApi.cancelOrder(orderId);
      if (res.success) {
        const orderRes = await posPerfumeApi.getOrder(orderId);
        if (orderRes.success && orderRes.data) store.setCurrentOrder(orderRes.data);
      } else {
        store.setOrderError(res.error ?? 'Cancel failed');
      }
    } finally {
      store.setOrderLoading(false);
    }
  }, [store]);

  /** Reset cancelled order to draft */
  const draftOrder = useCallback(async () => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return;
    store.setOrderLoading(true);
    try {
      const res = await posPerfumeApi.draftOrder(orderId);
      if (res.success) {
        const orderRes = await posPerfumeApi.getOrder(orderId);
        if (orderRes.success && orderRes.data) store.setCurrentOrder(orderRes.data);
      } else {
        store.setOrderError(res.error ?? 'Draft failed');
      }
    } finally {
      store.setOrderLoading(false);
    }
  }, [store]);

  /** Send WhatsApp message for the current order */
  const sendWhatsApp = useCallback(async () => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return { success: false, error: 'No order' };
    return posPerfumeApi.sendWhatsApp(orderId);
  }, [store]);

  /** Download PDF report */
  const downloadReport = useCallback(async () => {
    const orderId = store.currentOrder?.id;
    if (!orderId) return;
    const blob = await posPerfumeApi.downloadOrderReport(orderId);
    if (blob) {
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => URL.revokeObjectURL(url), 10_000);
    }
  }, [store]);

  return {
    currentOrder:  store.currentOrder,
    orderLines:    store.orderLines,
    isLoading:     store.isOrderLoading,
    error:         store.orderError,
    createOrder,
    loadOrder,
    addLine,
    updateLine,
    deleteLine,
    confirmOrder,
    quotationOrder,
    cancelOrder,
    draftOrder,
    sendWhatsApp,
    downloadReport,
  };
}
