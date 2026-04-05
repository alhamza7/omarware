import { useState } from 'react';
import { PosAppContainer } from './features/pos/containers/PosAppContainer';
import { PoContainer }     from './features/supply/containers/PoContainer';
import { Package, ShoppingCart } from 'lucide-react';

type AppTab = 'pos' | 'supply';

export default function App() {
  const [tab, setTab] = useState<AppTab>('supply');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* App-level nav */}
      <div className="bg-gray-900 text-white flex items-center gap-1 px-4 py-2">
        <span className="text-sm font-bold text-gray-300 mr-3">Lugal</span>
        <button
          onClick={() => setTab('supply')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition ${
            tab === 'supply' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
        >
          <Package className="w-4 h-4" /> Supply Chain
        </button>
        <button
          onClick={() => setTab('pos')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition ${
            tab === 'pos' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700'
          }`}
        >
          <ShoppingCart className="w-4 h-4" /> POS
        </button>
      </div>

      {tab === 'supply' && <PoContainer />}
      {tab === 'pos'    && <PosAppContainer />}
    </div>
  );
}
