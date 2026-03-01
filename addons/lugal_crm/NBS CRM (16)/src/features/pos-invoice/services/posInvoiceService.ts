import { apiPost } from '../../../shared/services/apiClient';
import type {
  ApiInvoiceContext,
  ApiProduct,
  ApiProductDetail,
  CreateOrderPayload,
  CreatedOrder,
} from '../types';

/** Load invoice context + partner_id for the given CRM customer. */
const fetchInvoiceContext = async (
  customerId: number,
): Promise<{ success: boolean; data?: ApiInvoiceContext; error?: string }> => {
  try {
    return await apiPost<ApiInvoiceContext>('/api/crm/pos/invoice_context', {
      customer_id: customerId,
    });
  } catch (err) {
    return { success: false, error: String(err) };
  }
};

/** Search products by name / default_code. */
const searchProducts = async (
  query: string,
  pricelistId?: number,
  limit = 80,
): Promise<{ success: boolean; data?: { items: ApiProduct[]; total: number }; error?: string }> => {
  try {
    return await apiPost<{ items: ApiProduct[]; total: number }>(
      '/api/crm/pos/products',
      { query, pricelist_id: pricelistId ?? null, limit },
    );
  } catch (err) {
    return { success: false, error: String(err) };
  }
};

/** Fetch full details (price per pricelist, warehouses stock) for a single product. */
const fetchProductDetail = async (
  productId: number,
  pricelistId?: number,
): Promise<{ success: boolean; data?: ApiProductDetail; error?: string }> => {
  try {
    return await apiPost<ApiProductDetail>('/api/crm/pos/product_detail', {
      product_id: productId,
      pricelist_id: pricelistId ?? null,
    });
  } catch (err) {
    return { success: false, error: String(err) };
  }
};

/** Submit order lines to create a pos.perfume.order. */
const createOrder = async (
  payload: CreateOrderPayload,
): Promise<{ success: boolean; data?: CreatedOrder; error?: string }> => {
  try {
    return await apiPost<CreatedOrder>('/api/crm/pos/orders/create', {
      partner_id: payload.partner_id,
      pricelist_id: payload.pricelist_id,
      invoice_type: payload.invoice_type,
      order_lines: payload.order_lines,
      exchange_rate: payload.exchange_rate ?? null,
      call_id: payload.call_id ?? null,
    });
  } catch (err) {
    return { success: false, error: String(err) };
  }
};

export const posInvoiceService = {
  fetchInvoiceContext,
  searchProducts,
  fetchProductDetail,
  createOrder,
};
