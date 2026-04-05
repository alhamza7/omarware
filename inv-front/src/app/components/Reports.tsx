import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router';
import {
  FileSpreadsheet, LogOut, Search, LayoutDashboard,
  LayoutGrid, Loader2, Database, AlertCircle,
  RefreshCcw, ArrowRight, ArrowLeft,
} from 'lucide-react';
import { isAuthenticated, getUser, clearAuth } from '../../services/apiClient';
import { fetchAudits } from '../../services/inventoryService';
import type { AuditData } from '../components/admin/types';

interface AuthUser { username: string; warehouse_id: number; warehouse_code: string; }

const PER_PAGE = 50;

/** Format ISO date to readable Arabic format */
function formatDate(iso: string): string {
  if (!iso) return '—';
  const d = new Date(iso);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  let h = d.getHours();
  const ampm = h >= 12 ? 'م' : 'ص';
  h = h % 12 || 12;
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${dd}/${mm}/${yyyy}  ${h}:${min} ${ampm}`;
}

export function Reports() {
  const navigate = useNavigate();
  const user = getUser<AuthUser>();

  // ── State ──────────────────────────────────────────────────────────────────
  const [audits, setAudits]     = useState<AuditData[]>([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [search, setSearch]     = useState('');
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');

  // ── Auth guard ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isAuthenticated()) void navigate('/', { replace: true });
  }, [navigate]);

  // ── Fetch audits for current warehouse ────────────────────────────────────
  const loadAudits = useCallback(async (p: number, q: string) => {
    setLoading(true);
    setError('');
    try {
      const result = await fetchAudits({
        page: p,
        per_page: PER_PAGE,
        search: q || undefined,
        warehouse_id: user?.warehouse_id || undefined,
      });
      setAudits(result.audits);
      setTotal(result.total);
    } catch (err: unknown) {
      setError((err as { message?: string })?.message ?? 'فشل تحميل التقارير');
    } finally {
      setLoading(false);
    }
  }, [user?.warehouse_id]);

  useEffect(() => {
    void loadAudits(page, search);
  }, [loadAudits, page, search]);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleSearchChange = (v: string) => {
    setSearch(v);
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE));

  return (
    <div dir="rtl" className="min-h-screen bg-[#020617] text-slate-100 font-sans flex flex-col relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 right-1/4 w-[500px] h-[500px] bg-purple-600/10 blur-[150px] rounded-full mix-blend-screen pointer-events-none" />

      {/* Header */}
      <header className="flex justify-between items-center px-6 py-4 bg-white/[0.02] backdrop-blur-2xl border-b border-white/[0.05] sticky top-0 z-30 shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
        <div className="flex items-center gap-6">
          <button
            onClick={() => { clearAuth(); navigate('/'); }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all text-sm border border-red-500/20"
          >
            <LogOut className="w-4 h-4" />
            <span>خروج</span>
          </button>

          <div className="hidden md:flex items-center gap-3 text-sm">
            <div className="flex items-center gap-2 bg-white/[0.03] px-3 py-1.5 rounded-lg border border-white/[0.05]">
              <span className="text-slate-500 text-xs uppercase tracking-widest">المستخدم</span>
              <span className="font-semibold text-white">{user?.username ?? 'مستخدم'}</span>
            </div>
            <div className="flex items-center gap-2 bg-blue-500/10 px-3 py-1.5 rounded-lg border border-blue-500/20">
              <span className="text-blue-400/70 text-xs uppercase tracking-widest">المخزن</span>
              <span className="font-semibold text-blue-400">{user?.warehouse_code || user?.warehouse_id || '—'}</span>
            </div>
          </div>
        </div>

        <nav className="flex items-center gap-3">
          <button
            onClick={() => navigate('/admin')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600/90 hover:bg-blue-500 text-white font-medium text-sm transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] border border-blue-400/30"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span className="hidden sm:inline">الإدارة</span>
          </button>
          <button
            onClick={() => navigate('/inventory')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-slate-300 transition-all text-sm border border-white/[0.05]"
          >
            <LayoutGrid className="w-4 h-4" />
            <span className="hidden sm:inline">الجرد</span>
          </button>
          <button
            onClick={() => navigate('/select-warehouse')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-slate-300 transition-all text-sm border border-white/[0.05]"
          >
            <Database className="w-4 h-4" />
            <span className="hidden sm:inline">تبديل المخزن</span>
          </button>
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1 p-6 relative z-10">
        <div className="max-w-6xl mx-auto space-y-6">

          {/* Page title */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-500/10 border border-purple-500/20 rounded-xl flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">تقارير الجرد</h1>
                <p className="text-slate-400/70 text-xs">
                  {user?.warehouse_code ? `مخزن: ${user.warehouse_code}` : 'جميع المخازن'}
                  {total > 0 && <span className="mr-2 text-slate-500">— {total.toLocaleString('ar-SA')} سجل</span>}
                </p>
              </div>
            </div>
            <button
              onClick={() => void loadAudits(page, search)}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-slate-400 hover:text-white transition-all text-sm border border-white/[0.05] disabled:opacity-40"
            >
              <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>تحديث</span>
            </button>
          </div>

          {/* Search bar */}
          <div className="relative">
            <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="ابحث بالاسم أو الكود..."
              className="w-full bg-black/40 border border-white/[0.08] text-white rounded-xl pr-11 pl-4 py-3 text-sm font-light focus:outline-none focus:ring-1 focus:ring-purple-500/50 focus:border-purple-500/50 focus:bg-black/60 transition-all placeholder:text-slate-600 shadow-[inset_0_2px_10px_rgba(0,0,0,0.3)]"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/20 rounded-xl px-5 py-4 text-red-400">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Table */}
          <div className="relative bg-white/[0.02] backdrop-blur-2xl border border-white/[0.08] rounded-2xl overflow-hidden shadow-[0_8px_32px_0_rgba(0,0,0,0.4)]">

            {/* Loading overlay */}
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-10 rounded-2xl">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
              </div>
            )}

            {/* Empty state */}
            {!loading && audits.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-4">
                <FileSpreadsheet className="w-12 h-12 opacity-30" />
                <p className="font-light tracking-wide">لا توجد سجلات جرد</p>
                {search && (
                  <button
                    onClick={() => handleSearchChange('')}
                    className="text-xs text-slate-600 hover:text-slate-300 transition-colors underline underline-offset-2"
                  >
                    مسح البحث
                  </button>
                )}
              </div>
            )}

            {/* Data table */}
            {audits.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.05] bg-white/[0.02]">
                      <th className="px-5 py-4 text-right font-medium text-slate-400 text-xs uppercase tracking-wider">#</th>
                      <th className="px-5 py-4 text-right font-medium text-slate-400 text-xs uppercase tracking-wider">الكود</th>
                      <th className="px-5 py-4 text-right font-medium text-slate-400 text-xs uppercase tracking-wider">اسم المنتج</th>
                      <th className="px-5 py-4 text-right font-medium text-slate-400 text-xs uppercase tracking-wider">الكمية</th>
                      <th className="px-5 py-4 text-right font-medium text-slate-400 text-xs uppercase tracking-wider hidden md:table-cell">المستخدم</th>
                      <th className="px-5 py-4 text-right font-medium text-slate-400 text-xs uppercase tracking-wider hidden lg:table-cell">التاريخ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.03]">
                    {audits.map((audit, idx) => (
                      <tr
                        key={audit.id}
                        className="hover:bg-white/[0.02] transition-colors group"
                      >
                        <td className="px-5 py-3.5 text-slate-600 text-xs font-mono">
                          {(page - 1) * PER_PAGE + idx + 1}
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="font-mono text-xs bg-blue-500/10 text-blue-300 px-2 py-1 rounded-lg border border-blue-500/20">
                            {audit.code}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-white font-light max-w-[280px] truncate">
                          {audit.name}
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="font-semibold text-emerald-400 text-base">
                            {parseFloat(audit.quantity).toLocaleString('ar-SA')}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-slate-400 hidden md:table-cell">
                          {audit.user}
                        </td>
                        <td className="px-5 py-3.5 text-slate-500 text-xs font-mono hidden lg:table-cell">
                          {formatDate(audit.date)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-5 py-4 border-t border-white/[0.05] bg-white/[0.01]">
                <span className="text-xs text-slate-500">
                  صفحة {page} من {totalPages} ({total.toLocaleString('ar-SA')} سجل)
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="flex items-center gap-1.5 px-4 py-2 bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.07] rounded-xl text-xs text-slate-400 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <ArrowRight className="w-3.5 h-3.5" />
                    السابق
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="flex items-center gap-1.5 px-4 py-2 bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.07] rounded-xl text-xs text-slate-400 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    التالي
                    <ArrowLeft className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in-up { animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
      `}} />
    </div>
  );
}
