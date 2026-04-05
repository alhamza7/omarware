import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { fetchWarehousesAuth, type Warehouse } from '../../services/warehouseService';
import { getUser, isAuthenticated, setAuth, getToken } from '../../services/apiClient';

interface AuthUser { warehouse_id: number; username: string; full_name: string; role: string; warehouse_code: string; token: string; }

/** Fallback list while warehouses are loading */
const FALLBACK: Warehouse[] = Array.from({ length: 18 }, (_, i) => ({
  id: i + 1,
  name: String(i + 1).padStart(2, '0'),
}));

export function WarehouseSelect() {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState<Warehouse[]>(FALLBACK);
  const [selectedId, setSelectedId] = useState<number>(getUser<AuthUser>()?.warehouse_id ?? 0);

  /** Redirect to login if not authenticated */
  useEffect(() => {
    if (!isAuthenticated()) void navigate('/', { replace: true });
  }, [navigate]);

  useEffect(() => {
    fetchWarehousesAuth()
      .then((list) => {
        // Filter out "My Company / WH" — keep only numbered warehouses
        const numbered = list.filter((w) => w.name !== 'My Company' && w.code !== 'WH');
        setWarehouses(numbered.length ? numbered : FALLBACK);
      })
      .catch(() => setWarehouses(FALLBACK));
  }, []);

  /** Persist selected warehouse in stored user data then navigate */
  const handleSelect = (wh: Warehouse) => {
    const currentUser = getUser<AuthUser>();
    const token = getToken() ?? '';
    if (currentUser && token) {
      setAuth(token, { ...currentUser, warehouse_id: wh.id, warehouse_code: wh.code ?? wh.name });
    }
    void navigate('/inventory');
  };

  return (
    <div dir="rtl" className="min-h-screen bg-[#05060A] text-slate-200 font-sans flex flex-col items-center justify-center py-16 px-4 selection:bg-blue-500/30">
      
      {/* Title Area */}
      <div className="text-center mb-16 space-y-4 animate-fade-in-down w-full">
        <h1 className="text-3xl md:text-4xl font-light text-white tracking-wide drop-shadow-sm">
          تحديد نقطة الجرد
        </h1>
        <p className="text-[#64748B] text-sm max-w-xl mx-auto font-light leading-relaxed">
          يرجى اختيار المخزن المستهدف. سيتم تطبيق إعدادات هذا المخزن على كافة العمليات اللاحقة.
        </p>
      </div>

      {/* Grid Area */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-5 w-full max-w-5xl">
        {warehouses.map((wh, i) => {
          const isActive = wh.id === selectedId;
          return (
            <button
              key={wh.id}
              onClick={() => handleSelect(wh)}
              style={{ animationDelay: `${i * 30}ms` }}
              className={`
                group relative flex flex-col items-center justify-center py-8 rounded-2xl transition-all duration-400
                animate-fade-in-up
                ${isActive 
                  ? 'bg-[#2563EB] shadow-[0_15px_40px_-10px_rgba(37,99,235,0.6)] transform -translate-y-2' 
                  : 'bg-[#0A0C13] border border-[#161925] hover:bg-[#0D1018] hover:border-[#1E293B] hover:-translate-y-2 hover:shadow-[0_15px_40px_-10px_rgba(59,130,246,0.15)]'
                }
              `}
            >
              {/* Inner highlight overlay for 3D effect on hover (for non-active cards) */}
              {!isActive && (
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/[0.04] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              )}

              {/* Inner highlight overlay for active card */}
              {isActive && (
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/[0.15] to-transparent pointer-events-none"></div>
              )}

              <div className="relative z-10 flex flex-col items-center gap-3">
                <span className={`text-[28px] leading-none font-semibold transition-colors duration-300 ${isActive ? 'text-white drop-shadow-md' : 'text-[#94A3B8] group-hover:text-white'}`}>
                  {wh.name}
                </span>
                <span className={`text-[13px] transition-colors duration-300 ${isActive ? 'text-blue-100' : 'text-[#475569] group-hover:text-[#94A3B8]'}`}>
                  مخزن
                </span>
              </div>

              {/* Active State Pill overlapping bottom edge */}
              {isActive && (
                <div className="absolute -bottom-3.5 left-1/2 -translate-x-1/2 whitespace-nowrap z-20">
                  <span className="flex items-center justify-center text-[11px] font-medium bg-[#1D4ED8] text-white px-5 py-1.5 rounded-full shadow-[0_4px_12px_rgba(0,0,0,0.4)] border border-blue-400/20">
                    النشط حالياً
                  </span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeInDown {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up {
          animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          opacity: 0;
        }
        .animate-fade-in-down {
          animation: fadeInDown 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          opacity: 0;
        }
      `}} />
    </div>
  );
}
