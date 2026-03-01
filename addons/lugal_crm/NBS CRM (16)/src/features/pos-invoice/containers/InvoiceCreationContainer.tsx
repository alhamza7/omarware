import { useEffect } from 'react';
import { usePosInvoice } from '../hooks/usePosInvoice';
import { InvoiceCreationDialog } from '../../../app/components/invoice-creation-dialog';
import type { CreateOrderPayload, ApiProductDetail } from '../types';

interface InvoiceCreationContainerProps {
  open: boolean;
  onClose: () => void;
  customerName: string;
  /** CRM customer ID (string of an integer) */
  customerId: string;
  customerAddress?: string;
  customerPhone?: string;
}

/**
 * Smart wrapper around InvoiceCreationDialog.
 * Handles all API calls: context loading, product search, product detail
 * fetching, and order creation.  The InvoiceCreationDialog itself stays
 * purely presentational.
 */
export function InvoiceCreationContainer({
  open,
  onClose,
  customerName,
  customerId,
  customerAddress,
  customerPhone,
}: InvoiceCreationContainerProps) {
  const {
    context,
    products,
    warehouses,
    pricelists,
    invoiceTypes,
    isLoadingContext,
    isSearchingProducts,
    isSubmitting,
    createdOrder,
    error,
    partnerId,
    exchangeRate,
    selectedPricelistId,
    loadContext,
    searchProducts,
    fetchProductDetail,
    submitOrder,
    setPricelist,
    reset,
  } = usePosInvoice();

  /** Load context whenever dialog opens. */
  useEffect(() => {
    if (!open) return;
    const id = parseInt(customerId, 10);
    if (!Number.isNaN(id)) {
      loadContext(id);
    }
  }, [open, customerId, loadContext]);

  /** Clean up state when dialog is closed. */
  const handleClose = () => {
    reset();
    onClose();
  };

  /**
   * Fetch full product details so the line can be auto-populated with
   * real price, UoM, and default warehouse.
   */
  const handleProductDetailFetch = async (
    productId: number,
  ): Promise<ApiProductDetail | null> => {
    return fetchProductDetail(productId);
  };

  /**
   * Build the POS order payload from the dialog's resolved lines and
   * header fields, then submit to the backend.
   */
  const handleSubmit = async (payload: CreateOrderPayload): Promise<void> => {
    if (!partnerId) {
      console.error('[InvoiceCreationContainer] No partner_id resolved for customer', customerId);
      return;
    }
    await submitOrder({
      ...payload,
      partner_id: partnerId,
      exchange_rate: exchangeRate ?? undefined,
    });
  };

  return (
    <InvoiceCreationDialog
      open={open}
      onClose={handleClose}
      customerName={customerName}
      customerId={customerId}
      customerAddress={customerAddress}
      customerPhone={customerPhone}
      // External data replaces hardcoded mocks
      externalProducts={products}
      externalWarehouses={warehouses}
      externalPricelists={pricelists.map(p => ({ value: String(p.id), label: p.name }))}
      externalInvoiceTypes={invoiceTypes.map(t => ({ value: t.key, label: t.label }))}
      selectedPricelistId={selectedPricelistId ?? undefined}
      onPricelistChange={(id) => setPricelist(id)}
      // Loading states
      isContextLoading={isLoadingContext}
      isSearchingProducts={isSearchingProducts}
      isSubmitting={isSubmitting}
      // Callbacks
      onProductSearch={searchProducts}
      onProductDetailFetch={handleProductDetailFetch}
      onCreateOrder={handleSubmit}
      // Result
      externalCreatedOrder={createdOrder ?? undefined}
      contextError={error ?? undefined}
    />
  );
}
