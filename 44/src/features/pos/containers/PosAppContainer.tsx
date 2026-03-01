import { useState, useCallback } from 'react';
import { usePosSetup } from '../hooks/usePosSetup';
import { useOrder } from '../hooks/useOrder';
import { usePosStore } from '../store/posStore';
import posPerfumeApi from '../../../services/posPerfumeApi';
import { CustomerContainer } from './CustomerContainer';
import { ProductSearchContainer } from './ProductSearchContainer';
import { OrderContainer } from './OrderContainer';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '../../../components/ui/button';

/**
 * Root POS container — orchestrates setup, order lifecycle, and renders
 * the three sub-containers: Customer toolbar, Order lines, Order summary.
 */
export function PosAppContainer() {
  const { isSetupLoaded, setupError, pricelists, warehouses, invoiceTypes, exchangeRate, userName, companyName } =
    usePosSetup();
  const { createOrder, loadOrder, currentOrder } = useOrder();
  const store = usePosStore();

  const [isSearchOpen, setIsSearchOpen] = useState(false);

  /** Set the first warehouse as default once setup loads */
  const handleNewOrder = useCallback(async () => {
    store.resetOrder();
    if (warehouses.length > 0 && !store.warehouseId) {
      store.setWarehouseId(warehouses[0].id);
    }
    await createOrder();
  }, [createOrder, store, warehouses]);

  /** Load an existing order by name/number */
  const handleLoadOrder = useCallback(async (name: string) => {
    if (!name.trim()) return;
    try {
      const res = await posPerfumeApi.listOrders({ query: name.trim(), limit: 1 });
      if (res.success && res.data?.items?.length) {
        await loadOrder(res.data.items[0].id);
      }
    } catch {
      store.setOrderError('Order not found: ' + name);
    }
  }, [loadOrder, store]);

  // ── Loading state ──────────────────────────────────────────
  if (!isSetupLoaded && !setupError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading POS…</p>
        </div>
      </div>
    );
  }

  // ── Setup error ────────────────────────────────────────────
  if (setupError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-4" />
          <p className="text-gray-800 font-medium mb-2">Failed to load POS</p>
          <p className="text-sm text-gray-500 mb-4">{setupError}</p>
          <Button onClick={() => window.location.reload()} className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">

      {/* ── Header ─────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 shadow-lg">
        <div className="flex justify-between items-center max-w-[1800px] mx-auto">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-lg flex items-center justify-center">
              <span className="text-lg">🏪</span>
            </div>
            <div>
              <h1 className="text-lg font-bold leading-none">NBS POS</h1>
              <p className="text-[10px] text-white/70">{companyName}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm">
            <div className="bg-white/10 px-3 py-1.5 rounded-lg">
              👤 {userName || 'User'}
            </div>
            <div className="bg-white/10 px-3 py-1.5 rounded-lg font-mono">
              1 USD = {exchangeRate.toLocaleString()} IQD
            </div>
            <div className="bg-white/10 px-3 py-1.5 rounded-lg">
              🕐 {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}
            </div>
          </div>
        </div>
      </div>

      {/* ── Customer / Toolbar ─────────────────────────────── */}
      <CustomerContainer
        pricelists={pricelists}
        invoiceTypes={invoiceTypes}
        orderName={currentOrder?.name ?? ''}
        orderState={currentOrder?.state ?? ''}
        onNewOrder={handleNewOrder}
        onLoadOrder={handleLoadOrder}
      />

      {/* ── Order lines + Summary ──────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-0">
        <OrderContainer
          onSearchClick={() => setIsSearchOpen(true)}
          exchangeRate={exchangeRate}
        />
      </div>

      {/* ── Product Search Modal ───────────────────────────── */}
      <ProductSearchContainer
        open={isSearchOpen}
        onOpenChange={setIsSearchOpen}
      />
    </div>
  );
}
