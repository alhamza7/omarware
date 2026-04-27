import { useState, useCallback } from 'react';
import { useOrder } from '../hooks/useOrder';
import { usePosStore } from '../store/posStore';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Separator } from '../../../components/ui/separator';
import {
  X, FileText, ShoppingCart, Save, XCircle,
  MessageSquare, Loader2, AlertCircle, Download,
  RotateCcw, Plus,
} from 'lucide-react';

interface OrderContainerProps {
  /** Open product search modal */
  onSearchClick: () => void;
  exchangeRate:  number;
}

/**
 * Order lines table + order summary footer.
 * Shows all real line data: UoM, warehouse, available_qty, discount, totals.
 * Wires all order actions: confirm, quotation, cancel, reset draft, WhatsApp, PDF.
 */
export function OrderContainer({ onSearchClick, exchangeRate }: OrderContainerProps) {
  const store = usePosStore();
  const {
    orderLines,
    currentOrder,
    isLoading,
    error,
    updateLine,
    deleteLine,
    confirmOrder,
    quotationOrder,
    cancelOrder,
    draftOrder,
    sendWhatsApp,
    downloadReport,
  } = useOrder();

  const [whatsappSent, setWhatsappSent] = useState(false);

  const isEditable  = !currentOrder || currentOrder.state === 'draft' || currentOrder.state === 'quotation';
  const isCancelled = currentOrder?.state === 'cancel';
  const isConfirmed = currentOrder?.state === 'sale' || currentOrder?.state === 'done';

  const handleQtyChange = useCallback(async (lineId: number, qty: number) => {
    if (qty <= 0) return;
    await updateLine(lineId, { quantity: qty });
  }, [updateLine]);

  const handlePriceChange = useCallback(async (lineId: number, price: number) => {
    if (price < 0) return;
    await updateLine(lineId, { unit_price: price });
  }, [updateLine]);

  const handleDiscountChange = useCallback(async (lineId: number, disc: number) => {
    await updateLine(lineId, { discount_percent: Math.min(100, Math.max(0, disc)) });
  }, [updateLine]);

  const handleWhatsApp = useCallback(async () => {
    const res = await sendWhatsApp();
    if (res?.success) {
      setWhatsappSent(true);
      setTimeout(() => setWhatsappSent(false), 3000);
    }
  }, [sendWhatsApp]);

  /** Server-computed totals from the order header */
  const subtotal   = currentOrder?.amount_subtotal   ?? 0;
  const discount   = currentOrder?.amount_discount   ?? 0;
  const tax        = currentOrder?.amount_tax        ?? 0;
  const grandTotal = currentOrder?.amount_total      ?? 0;
  const totalIQD   = currentOrder?.amount_total_iqd  ?? Math.round(grandTotal * exchangeRate);

  /** Number of empty clickable rows to fill the table */
  const emptyRowCount = Math.max(0, 6 - orderLines.length);

  return (
    <>
      {/* ── Error banner ──────────────────────────────────────── */}
      {error && (
        <div className="mx-6 my-2 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
          <button onClick={() => store.setOrderError(null)} className="ml-auto text-red-400 hover:text-red-600">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* ── Order Lines Table ─────────────────────────────────── */}
      <div className="flex-1 px-6 py-2 max-w-[1800px] mx-auto w-full overflow-hidden">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-full flex flex-col">
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-sm">
              {/* Header */}
              <thead className="bg-blue-600 text-white">
                <tr>
                  <th className="w-9 px-3 py-3 text-center">#</th>
                  <th className="px-3 py-3 text-left min-w-[180px]">Product</th>
                  <th className="px-3 py-3 text-center w-16">Qty</th>
                  <th className="px-3 py-3 text-center w-28">Unit (وحدة)</th>
                  <th className="px-3 py-3 text-center w-24">Warehouse</th>
                  <th className="px-3 py-3 text-center w-16">Avail.</th>
                  <th className="px-3 py-3 text-center w-28">Price USD</th>
                  <th className="px-3 py-3 text-center w-28">Price IQD</th>
                  <th className="px-3 py-3 text-center w-16">Disc%</th>
                  <th className="px-3 py-3 text-center w-20">Disc Amt</th>
                  <th className="px-3 py-3 text-center w-28">Total USD</th>
                  <th className="px-3 py-3 text-center w-28">Total IQD</th>
                  <th className="w-9 px-2"></th>
                </tr>
              </thead>
              <tbody>
                {/* Real order lines */}
                {orderLines.map((line, idx) => (
                  <tr key={line.id} className="border-b border-gray-100 hover:bg-blue-50/30 transition-colors">

                    {/* # */}
                    <td className="px-3 py-2 text-center text-gray-400 text-xs">{idx + 1}</td>

                    {/* Product */}
                    <td className="px-3 py-2">
                      <div className="font-medium text-gray-800 leading-tight">
                        {line.custom_product_name || line.product_id?.name || '—'}
                      </div>
                      {line.product_id?.default_code && (
                        <div className="text-xs font-mono text-blue-500 mt-0.5">
                          {line.product_id.default_code}
                        </div>
                      )}
                      {line.product_id?.foreign_name && (
                        <div className="text-xs text-gray-400">{line.product_id.foreign_name}</div>
                      )}
                    </td>

                    {/* Qty */}
                    <td className="px-2 py-2">
                      {isEditable ? (
                        <Input
                          type="number"
                          value={line.quantity}
                          min={0.001}
                          step={1}
                          onChange={(e) => handleQtyChange(line.id, parseFloat(e.target.value) || 1)}
                          className="text-center h-7 w-16 border-gray-200 focus:border-blue-500 text-xs px-1"
                          disabled={isLoading}
                        />
                      ) : (
                        <span className="block text-center font-medium">{line.quantity}</span>
                      )}
                    </td>

                    {/* UoM — الوحدة الفرعية */}
                    <td className="px-3 py-2 text-center">
                      <span className="text-xs bg-purple-50 text-purple-700 border border-purple-200 px-2 py-0.5 rounded-md">
                        {line.product_uom_id?.name ?? '—'}
                      </span>
                    </td>

                    {/* Warehouse */}
                    <td className="px-3 py-2 text-center">
                      <span className="text-xs font-mono bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                        {line.warehouse_id?.code ?? '—'}
                      </span>
                    </td>

                    {/* Available qty in selected warehouse */}
                    <td className="px-3 py-2 text-center">
                      <span className={`text-xs font-semibold ${(line.available_qty ?? 0) > 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {line.available_qty ?? 0}
                      </span>
                    </td>

                    {/* Unit Price USD */}
                    <td className="px-2 py-2">
                      {isEditable ? (
                        <Input
                          type="number"
                          value={line.unit_price ?? 0}
                          min={0}
                          step={0.01}
                          onChange={(e) => handlePriceChange(line.id, parseFloat(e.target.value) || 0)}
                          className="text-center h-7 w-24 border-gray-200 focus:border-blue-500 text-xs font-mono px-1"
                          disabled={isLoading}
                        />
                      ) : (
                        <span className="block text-center font-mono">${(line.unit_price ?? 0).toFixed(2)}</span>
                      )}
                    </td>

                    {/* Unit Price IQD */}
                    <td className="px-3 py-2 text-center text-xs font-mono text-gray-500">
                      {Math.round((line.unit_price ?? 0) * exchangeRate).toLocaleString()}
                    </td>

                    {/* Discount % */}
                    <td className="px-2 py-2">
                      {isEditable ? (
                        <Input
                          type="number"
                          value={line.discount_percent ?? 0}
                          min={0}
                          max={100}
                          step={0.5}
                          onChange={(e) => handleDiscountChange(line.id, parseFloat(e.target.value) || 0)}
                          className="text-center h-7 w-14 border-gray-200 focus:border-blue-500 text-xs px-1"
                          disabled={isLoading}
                        />
                      ) : (
                        <span className="block text-center">{line.discount_percent ?? 0}%</span>
                      )}
                    </td>

                    {/* Discount amount */}
                    <td className="px-3 py-2 text-center text-xs font-mono text-red-500">
                      {(line.discount_amount ?? 0) > 0 ? `-$${(line.discount_amount ?? 0).toFixed(2)}` : '—'}
                    </td>

                    {/* Line Total USD */}
                    <td className="px-3 py-2 text-center font-mono font-semibold text-blue-700">
                      ${(line.line_total ?? 0).toFixed(2)}
                    </td>

                    {/* Line Total IQD */}
                    <td className="px-3 py-2 text-center text-xs font-mono text-gray-600">
                      {Math.round((line.line_total ?? 0) * exchangeRate).toLocaleString()}
                    </td>

                    {/* Delete */}
                    <td className="px-2 py-2 text-center">
                      {isEditable && (
                        <button
                          onClick={() => deleteLine(line.id)}
                          disabled={isLoading}
                          className="w-6 h-6 flex items-center justify-center text-red-300 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}

                {/* Empty / Add-product rows */}
                {isEditable && emptyRowCount > 0 && Array.from({ length: emptyRowCount }, (_, i) => (
                  <tr
                    key={`empty-${i}`}
                    className="border-b border-gray-50 hover:bg-blue-50/20 cursor-pointer transition-colors"
                    onClick={onSearchClick}
                  >
                    <td className="px-3 py-3 text-center text-gray-200 text-xs">
                      {orderLines.length + i + 1}
                    </td>
                    <td className="px-3 py-3" colSpan={2}>
                      {i === 0 ? (
                        <span className="flex items-center gap-1.5 text-blue-400 text-sm">
                          <Plus className="w-3.5 h-3.5" />
                          Click to search and add product…
                        </span>
                      ) : <span className="text-gray-100">—</span>}
                    </td>
                    {Array.from({ length: 10 }, (_, j) => <td key={j} />)}
                  </tr>
                ))}

                {/* Global loading */}
                {isLoading && orderLines.length === 0 && (
                  <tr>
                    <td colSpan={13} className="text-center py-12">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto text-blue-500" />
                    </td>
                  </tr>
                )}

                {/* No order state */}
                {!currentOrder && !isLoading && (
                  <tr>
                    <td colSpan={13} className="text-center py-12 text-gray-400">
                      <ShoppingCart className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">Select a customer and click "+ New Order" to begin</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── Order Summary Footer ──────────────────────────────── */}
      <div className="bg-white border-t-2 border-gray-200 px-6 py-3 shadow-lg shrink-0">
        <div className="max-w-[1800px] mx-auto flex items-center gap-6 flex-wrap">

          {/* Totals block */}
          <div className="flex items-center gap-5 flex-wrap">
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-20">Subtotal:</span>
                <span className="font-mono text-sm font-medium">${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-20">Discount:</span>
                <span className="font-mono text-sm text-red-500">
                  {discount > 0 ? `-$${discount.toFixed(2)}` : '$0.00'}
                </span>
              </div>
            </div>

            <Separator orientation="vertical" className="h-10" />

            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-16">Tax:</span>
                <span className="font-mono text-sm">${tax.toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-gray-700 w-16">Total:</span>
                <span className="text-2xl font-bold text-blue-600 font-mono">${grandTotal.toFixed(2)}</span>
              </div>
            </div>

            <Separator orientation="vertical" className="h-10" />

            <div>
              <div className="text-xs text-gray-400 mb-0.5">Total IQD</div>
              <div className="text-lg font-bold font-mono text-gray-800">
                {Math.round(totalIQD).toLocaleString()}
                <span className="text-xs font-normal text-gray-500 ml-1">IQD</span>
              </div>
            </div>

            {/* Order info */}
            {currentOrder?.name && (
              <>
                <Separator orientation="vertical" className="h-10" />
                <div>
                  <div className="text-xs text-gray-400 mb-0.5">Order</div>
                  <div className="font-semibold text-gray-800">{currentOrder.name}</div>
                  {currentOrder.sale_order_id && (
                    <div className="text-xs text-green-600">
                      SO: {currentOrder.sale_order_id.name}
                    </div>
                  )}
                  {currentOrder.sap_doc_num && (
                    <div className="text-xs text-orange-500">
                      SAP: {currentOrder.sap_doc_num}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex gap-2 ml-auto flex-wrap">

            {/* Draft save - just visual, auto-saved */}
            {isEditable && currentOrder && (
              <Button
                variant="outline"
                className="h-9 border-gray-300 text-gray-700"
                onClick={() => {}}
                disabled={isLoading}
              >
                <Save className="w-4 h-4 mr-1.5" />
                Draft
              </Button>
            )}

            {/* Quotation */}
            {isEditable && currentOrder && (
              <Button
                variant="outline"
                className="h-9 border-yellow-400 text-yellow-700 hover:bg-yellow-50"
                onClick={quotationOrder}
                disabled={isLoading}
              >
                <FileText className="w-4 h-4 mr-1.5" />
                Quotation
              </Button>
            )}

            {/* Confirm → Sale Order */}
            {isEditable && currentOrder && (
              <Button
                className="h-9 bg-green-600 hover:bg-green-700 text-white"
                onClick={confirmOrder}
                disabled={isLoading || orderLines.length === 0}
              >
                {isLoading
                  ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                  : <ShoppingCart className="w-4 h-4 mr-1.5" />
                }
                Sale Order
              </Button>
            )}

            {/* Cancel */}
            {isEditable && currentOrder && (
              <Button
                className="h-9 bg-red-600 hover:bg-red-700 text-white"
                onClick={cancelOrder}
                disabled={isLoading}
              >
                <XCircle className="w-4 h-4 mr-1.5" />
                Cancel
              </Button>
            )}

            {/* Reset to draft */}
            {isCancelled && (
              <Button
                className="h-9 bg-blue-600 hover:bg-blue-700 text-white"
                onClick={draftOrder}
                disabled={isLoading}
              >
                <RotateCcw className="w-4 h-4 mr-1.5" />
                Reset Draft
              </Button>
            )}

            {/* Confirmed badge */}
            {isConfirmed && (
              <div className="h-9 flex items-center px-3 bg-green-50 border border-green-300 rounded-md text-sm text-green-700 font-medium">
                ✓ Confirmed
              </div>
            )}

            {/* PDF */}
            {currentOrder && (
              <Button
                variant="outline"
                className="h-9 border-gray-300 text-gray-700"
                onClick={downloadReport}
                disabled={isLoading}
              >
                <Download className="w-4 h-4 mr-1.5" />
                PDF
              </Button>
            )}

            {/* WhatsApp */}
            {currentOrder && (
              <Button
                className={`h-9 text-white ${whatsappSent ? 'bg-green-500' : 'bg-green-500 hover:bg-green-600'}`}
                onClick={handleWhatsApp}
                disabled={isLoading}
              >
                <MessageSquare className="w-4 h-4 mr-1.5" />
                {whatsappSent ? 'Sent ✓' : 'WhatsApp'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
