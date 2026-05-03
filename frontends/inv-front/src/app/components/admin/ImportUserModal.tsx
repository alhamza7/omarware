import React, { useState } from 'react';
import { X, Download, Loader2, AlertCircle, Search } from 'lucide-react';
import type { Warehouse } from '../../../services/warehouseService';
import type { OdooCandidate } from '../../../services/adminService';

export interface ImportUserPayload {
  odoo_user_id: number;
  full_name: string;
  role: 'admin' | 'user';
  warehouse_id: number;
}

interface ImportUserModalProps {
  candidates: OdooCandidate[];
  warehouses: Warehouse[];
  loading: boolean;
  error: string;
  onClose: () => void;
  onSubmit: (payload: ImportUserPayload) => void;
}

/** Presentational modal for importing an existing Odoo user into the inventory system. */
export function ImportUserModal({
  candidates, warehouses, loading, error, onClose, onSubmit,
}: ImportUserModalProps) {
  const [search, setSearch]         = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [role, setRole]             = useState<'admin' | 'user'>('user');
  const [warehouseId, setWarehouseId] = useState<number>(warehouses[0]?.id ?? 0);

  /** Filter candidates by search input */
  const filtered = candidates.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.login.toLowerCase().includes(search.toLowerCase())
  );

  const selectedCandidate = candidates.find((c) => c.id === selectedId);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedId) return;
    onSubmit({
      odoo_user_id: selectedId,
      full_name: selectedCandidate?.name ?? '',
      role,
      warehouse_id: warehouseId,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      {/* Modal card */}
      <div className="relative w-full max-w-md bg-[#0A0C13] border border-[#1F2230] rounded-3xl shadow-[0_25px_60px_rgba(0,0,0,0.8)] z-10 overflow-hidden animate-fade-in-up">

        {/* Header */}
        <div className="flex items-center justify-between px-7 py-5 border-b border-[#161925]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-center">
              <Download className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">استيراد من أودو</h2>
              <p className="text-xs text-[#475569]">{candidates.length} مستخدم متاح للاستيراد</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-[#475569] hover:text-white hover:bg-white/[0.05] transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} dir="rtl" className="px-7 py-6 space-y-4">

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* No candidates */}
          {candidates.length === 0 && (
            <div className="text-center py-8 text-[#475569] space-y-2">
              <Download className="w-10 h-10 mx-auto opacity-30" />
              <p className="text-sm">جميع مستخدمي أودو مسجلون في نظام الجرد مسبقاً</p>
            </div>
          )}

          {candidates.length > 0 && (
            <>
              {/* Search */}
              <div className="relative">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#475569] pointer-events-none" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="ابحث بالاسم أو اسم الدخول..."
                  className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl pr-9 pl-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500/40 transition-all placeholder:text-[#475569]"
                />
              </div>

              {/* Candidates list */}
              <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 scrollbar-thin">
                {filtered.length === 0 && (
                  <p className="text-center text-xs text-[#475569] py-4">لا توجد نتائج</p>
                )}
                {filtered.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setSelectedId(c.id)}
                    className={`
                      w-full flex items-center justify-between px-4 py-3 rounded-xl border text-sm transition-all
                      ${selectedId === c.id
                        ? 'bg-emerald-500/10 border-emerald-500/40 text-white'
                        : 'bg-[#08090E] border-[#161925] text-[#94A3B8] hover:border-[#2D3748] hover:text-white'
                      }
                    `}
                  >
                    <span className="font-medium">{c.name}</span>
                    <span className="font-mono text-xs opacity-60">{c.login}</span>
                  </button>
                ))}
              </div>

              {/* Role + Warehouse */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">الصلاحية</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as 'admin' | 'user')}
                    className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500/40 transition-all appearance-none cursor-pointer"
                  >
                    <option value="user">مستخدم</option>
                    <option value="admin">مدير</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">المخزن <span className="text-red-400">*</span></label>
                  <select
                    value={warehouseId}
                    onChange={(e) => setWarehouseId(Number(e.target.value))}
                    required
                    className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500/40 transition-all appearance-none cursor-pointer"
                  >
                    {warehouses.map((wh) => (
                      <option key={wh.id} value={wh.id}>{wh.code || wh.name} — {wh.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={onClose}
                  className="flex-1 py-3 bg-[#0D1018] border border-[#161925] text-[#94A3B8] hover:text-white rounded-xl text-sm font-medium transition-all hover:bg-[#161925]">
                  إلغاء
                </button>
                <button type="submit" disabled={!selectedId || loading}
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  استيراد المستخدم
                </button>
              </div>
            </>
          )}
        </form>
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-fade-in-up { animation: fadeInUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
      `}} />
    </div>
  );
}
