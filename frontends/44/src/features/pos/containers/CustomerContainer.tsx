import { useState, useCallback, useRef, useEffect } from 'react';
import { usePosStore } from '../store/posStore';
import { useCustomerSearch } from '../hooks/useCustomerSearch';
import type { Customer } from '../../../types/pos';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Search, X, User, Phone } from 'lucide-react';

interface CustomerContainerProps {
  pricelists:   { id: number; name: string }[];
  invoiceTypes: { key: string; label: string }[];
  orderName:    string;
  orderState:   string;
  onNewOrder:   () => void;
  onLoadOrder:  (name: string) => void;
}

/**
 * Handles customer search, selection, pricelist and invoice type selection.
 * Renders the top toolbar of the POS.
 */
export function CustomerContainer({
  pricelists,
  invoiceTypes,
  orderName,
  orderState,
  onNewOrder,
  onLoadOrder,
}: CustomerContainerProps) {
  const store = usePosStore();
  const { results, isLoading, search, clearResults } = useCustomerSearch();

  const [query,        setQuery]        = useState('');
  const [isDropOpen,   setIsDropOpen]   = useState(false);
  const [loadOrderNum, setLoadOrderNum] = useState(orderName);

  const containerRef = useRef<HTMLDivElement>(null);

  /** Close dropdown when clicking outside */
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsDropOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  /** Sync load order input when order name changes externally */
  useEffect(() => {
    setLoadOrderNum(orderName);
  }, [orderName]);

  const handleSearchChange = useCallback((val: string) => {
    setQuery(val);
    if (val.length >= 1) {
      search(val);
      setIsDropOpen(true);
    } else {
      setIsDropOpen(false);
      clearResults();
    }
  }, [search, clearResults]);

  const handleSelectCustomer = useCallback((c: Customer) => {
    store.setSelectedCustomer(c);
    setQuery(c.name);
    setIsDropOpen(false);
    clearResults();
  }, [store, clearResults]);

  const handleClearCustomer = useCallback(() => {
    store.setSelectedCustomer(null);
    setQuery('');
    clearResults();
  }, [store, clearResults]);

  const stateColor: Record<string, string> = {
    draft:     'bg-gray-100 text-gray-700',
    quotation: 'bg-yellow-100 text-yellow-700',
    confirmed: 'bg-green-100 text-green-700',
    cancel:    'bg-red-100 text-red-700',
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3 shadow-sm">
      <div className="max-w-[1800px] mx-auto">
        <div className="flex items-center gap-3 flex-wrap">

          {/* ── Customer Search ─────────────────────────────── */}
          <div className="relative flex items-center gap-2" ref={containerRef}>
            <label className="text-sm text-gray-600 whitespace-nowrap">Customer:</label>
            <div className="relative w-52">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
              <Input
                value={query}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Search customer..."
                className="pl-8 pr-7 h-9 text-sm"
              />
              {store.selectedCustomer && (
                <button
                  onClick={handleClearCustomer}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-500"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}

              {/* Dropdown */}
              {isDropOpen && (
                <div className="absolute top-full left-0 mt-1 w-72 bg-white border border-gray-200 rounded-lg shadow-xl z-50 overflow-hidden">
                  {isLoading && (
                    <div className="px-4 py-3 text-sm text-gray-500">Searching…</div>
                  )}
                  {!isLoading && results.length === 0 && (
                    <div className="px-4 py-3 text-sm text-gray-500">No customers found</div>
                  )}
                  {results.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => handleSelectCustomer(c)}
                      className="w-full text-left px-4 py-2.5 hover:bg-blue-50 border-b border-gray-100 last:border-0 flex items-start gap-3"
                    >
                      <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
                        <User className="w-3.5 h-3.5 text-blue-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{c.name}</p>
                        {c.phone && (
                          <p className="text-xs text-gray-500 flex items-center gap-1">
                            <Phone className="w-3 h-3" />{c.phone}
                          </p>
                        )}
                        {c.ref && <p className="text-xs text-gray-400">Ref: {c.ref}</p>}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Selected customer badge */}
            {store.selectedCustomer && (
              <span className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-1 rounded-md">
                ✓ {store.selectedCustomer.name}
              </span>
            )}
          </div>

          {/* ── Pricelist ──────────────────────────────────── */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">Pricelist:</label>
            <select
              value={store.pricelistId ?? ''}
              onChange={(e) => store.setPricelistId(e.target.value ? Number(e.target.value) : null)}
              className="h-9 px-3 border border-gray-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {pricelists.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* ── Invoice Type ───────────────────────────────── */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">Type:</label>
            <select
              value={store.invoiceType}
              onChange={(e) => store.setInvoiceType(e.target.value)}
              className="h-9 px-3 border border-gray-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {invoiceTypes.map((t) => (
                <option key={t.key} value={t.key}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* ── Order # + Load ─────────────────────────────── */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">Order #:</label>
            <div className="flex items-center gap-1">
              <Input
                value={loadOrderNum}
                onChange={(e) => setLoadOrderNum(e.target.value)}
                placeholder="Order number…"
                className="w-32 h-9 text-sm"
              />
              {orderState && (
                <span className={`text-xs px-2 py-1 rounded-md font-medium ${stateColor[orderState] ?? 'bg-gray-100 text-gray-700'}`}>
                  {orderState}
                </span>
              )}
            </div>
          </div>

          {/* ── Actions ──────────────────────────────────────── */}
          <div className="flex gap-2 ml-auto items-center">
            {/* Warning when no customer selected */}
            {!store.selectedCustomer && (
              <span className="text-xs text-amber-600 bg-amber-50 border border-amber-200 px-2 py-1 rounded-md flex items-center gap-1">
                ⚠️ Select a customer first
              </span>
            )}
            <Button
              onClick={() => onLoadOrder(loadOrderNum)}
              disabled={!loadOrderNum}
              className="h-9 bg-blue-600 hover:bg-blue-700 text-white text-sm"
            >
              # Load
            </Button>
            <Button
              onClick={onNewOrder}
              disabled={!store.selectedCustomer}
              title={!store.selectedCustomer ? 'Select a customer first' : 'Create new order'}
              className="h-9 bg-green-600 hover:bg-green-700 text-white text-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              + New Order
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
