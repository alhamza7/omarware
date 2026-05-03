import { useState } from 'react';
import { PosAppContainer }    from './features/pos/containers/PosAppContainer';
import { PoContainer }        from './features/supply/containers/PoContainer';
import { ContainerContainer } from './features/supply/containers/ContainerContainer';
import { VendorContainer }    from './features/supply/containers/VendorContainer';
import { Package, ShoppingCart, Ship, Building2 } from 'lucide-react';

type AppTab = 'pos' | 'supply' | 'containers' | 'vendors';

const NAV_ITEMS: { id: AppTab; label: string; icon: React.ReactNode }[] = [
  { id: 'supply',     label: 'Purchase Orders', icon: <Package className="w-4 h-4" /> },
  { id: 'containers', label: 'Containers',      icon: <Ship className="w-4 h-4" /> },
  { id: 'vendors',    label: 'Vendors',         icon: <Building2 className="w-4 h-4" /> },
  { id: 'pos',        label: 'POS',             icon: <ShoppingCart className="w-4 h-4" /> },
];

export default function App() {
  const [tab, setTab] = useState<AppTab>('supply');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* App-level nav */}
      <div className="bg-gray-900 text-white flex items-center gap-1 px-4 py-2">
        <span className="text-sm font-bold text-gray-300 mr-4">Lugal</span>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => setTab(item.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition ${
              tab === item.id
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            {item.icon} {item.label}
          </button>
        ))}
      </div>

      {tab === 'supply'     && <PoContainer />}
      {tab === 'containers' && <ContainerContainer />}
      {tab === 'vendors'    && <VendorContainer />}
      {tab === 'pos'        && <PosAppContainer />}
    </div>
  );
}
