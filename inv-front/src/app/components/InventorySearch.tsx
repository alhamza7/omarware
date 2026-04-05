import React, { useState, useRef, useMemo, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router';
import {
  Search, Camera, Database, FileSpreadsheet, LogOut,
  LayoutDashboard, Zap, CheckCircle, AlertCircle, Loader2, Package, X,
} from 'lucide-react';
import imgSettingsDial from 'figma:asset/1cc6baa82b643510195e9fec8ec1d81634157487.png';
import { isAuthenticated, getUser, clearAuth } from '../../services/apiClient';
import { searchProduct, createAudit } from '../../services/inventoryService';
import type { ProductDetail, ProductBarcode } from '../../services/inventoryService';

interface AuthUser { username: string; warehouse_id: number; warehouse_code: string; }

type SearchStatus = 'idle' | 'loading' | 'results' | 'found' | 'not_found' | 'error';
type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error';

export function InventorySearch() {
  const navigate = useNavigate();

  // ── State ─────────────────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery]         = useState('');
  const [searchStatus, setSearchStatus]       = useState<SearchStatus>('idle');
  const [searchResults, setSearchResults]     = useState<ProductDetail[]>([]); // multiple matches
  const [product, setProduct]                 = useState<ProductDetail | null>(null);
  const [selectedBarcode, setSelectedBarcode] = useState<ProductBarcode | null>(null);
  const [quantity, setQuantity]               = useState('');
  const [submitStatus, setSubmitStatus]       = useState<SubmitStatus>('idle');
  const [errorMsg, setErrorMsg]               = useState('');

  // ── Refs ──────────────────────────────────────────────────────────────────
  const inputRef = useRef<HTMLInputElement>(null);

  // ── Derived values ────────────────────────────────────────────────────────
  const user = getUser<AuthUser>();

  /** Stock for the user's selected warehouse */
  const warehouseStock = useMemo(() => {
    if (!product || !user?.warehouse_id) return null;
    return product.warehouses.find(w => w.warehouse_id === user.warehouse_id) ?? null;
  }, [product, user?.warehouse_id]);

  /** The UoM label shown next to the quantity input */
  const activeUom = useMemo(
    () => selectedBarcode?.uom || product?.uom || '',
    [selectedBarcode, product],
  );

  // ── Callbacks ─────────────────────────────────────────────────────────────

  /** Execute product search via API */
  const handleSearch = useCallback(async () => {
    const query = searchQuery.trim();
    if (!query) return;

    setSearchStatus('loading');
    setProduct(null);
    setSearchResults([]);
    setSelectedBarcode(null);
    setQuantity('');
    setSubmitStatus('idle');
    setErrorMsg('');

    try {
      const results = await searchProduct(query, user?.warehouse_id);
      if (results.length === 0) {
        setSearchStatus('not_found');
      } else if (results.length === 1) {
        // Single / exact match — go directly to product detail
        const p = results[0];
        setProduct(p);
        const matched = p.barcodes.find(b => b.matched);
        setSelectedBarcode(matched ?? p.barcodes[0] ?? null);
        setSearchStatus('found');
      } else {
        // Multiple results — show the picker list
        setSearchResults(results);
        setSearchStatus('results');
      }
    } catch {
      setSearchStatus('error');
      setErrorMsg('تعذّر الاتصال بالخادم، يرجى المحاولة مجدداً');
    }
  }, [searchQuery, user?.warehouse_id]);

  /** Select a product from the results list */
  const handleSelectProduct = useCallback((p: ProductDetail) => {
    const matched = p.barcodes.find(b => b.matched);
    setProduct(p);
    setSelectedBarcode(matched ?? p.barcodes[0] ?? null);
    setSearchResults([]);
    setQuantity('');
    setSubmitStatus('idle');
    setErrorMsg('');
    setSearchStatus('found');
  }, []);

  /** Submit an inventory count (audit) */
  const handleSubmitAudit = useCallback(async () => {
    if (!product || !user?.warehouse_id || !quantity) return;

    const qty = parseFloat(quantity);
    if (isNaN(qty) || qty < 0) return;

    setSubmitStatus('submitting');
    setErrorMsg('');

    try {
      await createAudit({
        product_id:   product.id,
        warehouse_id: user.warehouse_id,
        quantity:     qty,
        uom_id:       selectedBarcode?.uom_id ?? product.uom_id ?? undefined,
        barcode_used: selectedBarcode?.barcode ?? undefined,
      });
      setSubmitStatus('success');
      setQuantity('');
      // Auto-clear success after 3 s and reset for next scan
      setTimeout(() => {
        setSubmitStatus('idle');
        setProduct(null);
        setSelectedBarcode(null);
        setSearchStatus('idle');
        setSearchQuery('');
        inputRef.current?.focus();
      }, 3000);
    } catch (err: unknown) {
      setSubmitStatus('error');
      const msg = (err as { message?: string })?.message ?? 'حدث خطأ أثناء الحفظ';
      setErrorMsg(msg);
    }
  }, [product, user?.warehouse_id, quantity, selectedBarcode]);

  /** Clear current result and reset to idle */
  const handleClear = useCallback(() => {
    setProduct(null);
    setSearchResults([]);
    setSelectedBarcode(null);
    setQuantity('');
    setSearchQuery('');
    setSearchStatus('idle');
    setSubmitStatus('idle');
    setErrorMsg('');
    inputRef.current?.focus();
  }, []);

  // ── Effects ───────────────────────────────────────────────────────────────

  /** Redirect to login if not authenticated */
  useEffect(() => {
    if (!isAuthenticated()) void navigate('/', { replace: true });
  }, [navigate]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div dir="rtl" className="min-h-screen bg-[#020617] text-slate-100 font-sans flex flex-col relative overflow-hidden">
      {/* Background Decorative Elements */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-blue-600/10 blur-[150px] rounded-full mix-blend-screen pointer-events-none"></div>

      {/* App Header (Glassmorphism) */}
      <header className="flex justify-between items-center px-6 py-4 bg-white/[0.02] backdrop-blur-2xl border-b border-white/[0.05] sticky top-0 z-30 shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
        <div className="flex items-center gap-6">
          <button
            onClick={() => { clearAuth(); navigate('/'); }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all text-sm border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.1)]"
          >
            <LogOut className="w-4 h-4" />
            <span>خروج</span>
          </button>

          <div className="hidden md:flex items-center gap-3 text-sm">
            <div className="flex items-center gap-2 bg-white/[0.03] px-3 py-1.5 rounded-lg border border-white/[0.05]">
              <span className="text-slate-500 text-xs uppercase tracking-widest">المستخدم</span>
              <span className="font-semibold text-white">{user?.username ?? 'مستخدم'}</span>
            </div>
            <div className="flex items-center gap-2 bg-blue-500/10 px-3 py-1.5 rounded-lg border border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.1)]">
              <span className="text-blue-400/70 text-xs uppercase tracking-widest">المخزن</span>
              <span className="font-semibold text-blue-400">{user?.warehouse_code || user?.warehouse_id || '-'}</span>
            </div>
          </div>
        </div>

        <nav className="flex items-center gap-3">
          <button
            onClick={() => navigate('/admin')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600/90 hover:bg-blue-500 text-white font-medium text-sm transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] border border-blue-400/30 active:scale-[0.98]"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span className="hidden sm:inline">الإدارة</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-slate-300 transition-all text-sm border border-white/[0.05] hover:border-white/[0.1] backdrop-blur-md"
            onClick={() => navigate('/reports')}
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span className="hidden sm:inline">التقارير</span>
          </button>
          <button
            onClick={() => navigate('/select-warehouse')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-slate-300 transition-all text-sm border border-white/[0.05] hover:border-white/[0.1] backdrop-blur-md"
          >
            <Database className="w-4 h-4" />
            <span className="hidden sm:inline">تبديل المخزن</span>
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center p-4 relative z-10">
        <div className="w-full max-w-3xl">
          <div className="text-center mb-12 space-y-4">
            <h1 className="text-4xl md:text-5xl font-light text-white tracking-tight drop-shadow-md">
              محرك <span className="font-semibold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">البحث الذكي</span>
            </h1>
            <p className="text-slate-400/80 max-w-lg mx-auto font-light tracking-wide">
              استخدم الباركود للوصول الفوري، أو ابحث يدوياً عن طريق الاسم أو الكود.
            </p>
          </div>

          {/* Search Card (Glassmorphism 3D effect) */}
          <div className="relative group">
            {/* Outer Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-blue-500/20 rounded-[2rem] blur-xl opacity-50 group-hover:opacity-80 transition duration-1000"></div>

            <div className="relative bg-white/[0.02] backdrop-blur-2xl border border-white/[0.08] shadow-[0_8px_32px_0_rgba(0,0,0,0.4)] rounded-[2rem] p-8 overflow-hidden">

              {/* Inner 3D Highlight */}
              <div className="absolute inset-0 rounded-[2rem] pointer-events-none shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)]"></div>

              {/* Search Bar */}
              <div className="relative flex items-center mb-10 z-10">
                <input
                  ref={inputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && void handleSearch()}
                  placeholder="ابحث بالاسم أو الاسم الأجنبي أو الكود أو الباركود..."
                  className="w-full bg-black/40 border border-white/[0.1] text-white rounded-2xl pl-36 pr-6 py-5 text-lg font-light focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-black/60 transition-all placeholder:text-slate-600 shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]"
                />

                <div className="absolute left-2.5 flex items-center gap-2">
                  <button
                    onClick={() => void handleSearch()}
                    disabled={searchStatus === 'loading'}
                    className="bg-blue-600/90 hover:bg-blue-500 disabled:opacity-50 text-white p-3 rounded-xl transition-all flex items-center justify-center gap-2 text-sm font-medium shadow-[0_0_15px_rgba(37,99,235,0.4)] border border-blue-400/30 group/btn"
                    title="بحث"
                  >
                    {searchStatus === 'loading'
                      ? <Loader2 className="w-4 h-4 animate-spin" />
                      : <><span>بحث</span><Search className="w-4 h-4 group-hover/btn:scale-110 transition-transform" /></>
                    }
                  </button>
                  <button
                    className="bg-white/[0.05] hover:bg-white/[0.1] text-slate-300 p-3 rounded-xl transition-all flex items-center justify-center group/cam border border-white/[0.1] backdrop-blur-md"
                    title="تشغيل الكاميرا للمسح"
                  >
                    <Camera className="w-5 h-5 group-hover/cam:text-blue-400 transition-colors" />
                  </button>
                </div>
              </div>

              {/* Status Indicator */}
              <div className="flex justify-between items-center mb-6 px-2">
                <div className="flex items-center gap-2 opacity-60 mix-blend-screen">
                  <img src={imgSettingsDial} alt="" className="w-12 h-12 object-cover rounded-full" style={{ filter: 'brightness(0.7) contrast(1.2)' }} />
                  <span className="text-xs text-slate-400 uppercase tracking-widest">إعدادات المسح</span>
                </div>
                <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 px-4 py-2 rounded-full shadow-[0_0_15px_rgba(34,197,94,0.1)]">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
                  <span className="text-xs font-medium text-green-400 tracking-wider">النظام جاهز للاستقبال</span>
                </div>
              </div>

              {/* Result / Empty State Area */}
              <div className={`bg-black/30 rounded-2xl border border-white/[0.05] flex flex-col items-center justify-center text-slate-500 relative overflow-hidden shadow-[inset_0_4px_20px_rgba(0,0,0,0.4)] transition-all duration-300 ${
                searchStatus === 'found'   ? 'min-h-[240px] p-0' :
                searchStatus === 'results' ? 'min-h-[240px] p-0 items-stretch' :
                'h-[240px]'
              }`}>

                {/* Scanner Laser Animation */}
                <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-50 animate-[scan_3s_ease-in-out_infinite]"></div>
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.05)_0%,transparent_70%)]"></div>

                {/* ── IDLE: waiting ───────────────────────────────────── */}
                {searchStatus === 'idle' && (
                  <div className="z-10 flex flex-col items-center gap-4">
                    <div className="w-20 h-20 rounded-full bg-white/[0.02] border border-white/[0.05] flex items-center justify-center mb-2 shadow-[0_0_30px_rgba(0,0,0,0.5)]">
                      <Zap className="w-8 h-8 text-slate-600" />
                    </div>
                    <p className="font-light tracking-wide text-slate-400">بانتظار إدخال البيانات...</p>
                  </div>
                )}

                {/* ── LOADING ──────────────────────────────────────────── */}
                {searchStatus === 'loading' && (
                  <div className="z-10 flex flex-col items-center gap-4">
                    <Loader2 className="w-10 h-10 text-blue-400 animate-spin" />
                    <p className="font-light tracking-wide text-slate-400">جاري البحث...</p>
                  </div>
                )}

                {/* ── RESULTS LIST ─────────────────────────────────────── */}
                {searchStatus === 'results' && (
                  <div className="z-10 w-full flex flex-col">
                    {/* Header */}
                    <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.05]">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse shadow-[0_0_8px_rgba(96,165,250,0.8)]" />
                        <span className="text-xs font-medium text-blue-300 tracking-wider">
                          {searchResults.length} نتيجة — اختر المنتج
                        </span>
                      </div>
                      <button
                        onClick={handleClear}
                        className="text-slate-600 hover:text-slate-300 transition-colors"
                        title="مسح البحث"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Scrollable list */}
                    <div className="overflow-y-auto max-h-[360px] divide-y divide-white/[0.04]">
                      {searchResults.map((p) => (
                        <button
                          key={p.id}
                          onClick={() => handleSelectProduct(p)}
                          className="w-full flex items-center gap-3 px-5 py-3.5 hover:bg-white/[0.04] active:bg-blue-500/10 transition-colors text-right group"
                        >
                          {/* Code badge */}
                          <span className="shrink-0 text-[10px] font-mono bg-blue-500/15 text-blue-300 px-2 py-0.5 rounded border border-blue-500/25 min-w-[72px] text-center">
                            {p.code}
                          </span>

                          {/* Names */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white font-medium truncate group-hover:text-blue-200 transition-colors">
                              {p.name}
                            </p>
                            {p.foreign_name && (
                              <p className="text-xs text-slate-500 truncate mt-0.5">{p.foreign_name}</p>
                            )}
                          </div>

                          {/* UOM + category chips */}
                          <div className="shrink-0 flex flex-col items-end gap-1">
                            <span className="text-[10px] text-slate-400 bg-white/[0.04] px-2 py-0.5 rounded">
                              {p.uom}
                            </span>
                            {p.category && (
                              <span className="text-[10px] text-slate-600 truncate max-w-[80px]">
                                {p.category}
                              </span>
                            )}
                          </div>

                          {/* Chevron */}
                          <svg className="shrink-0 w-4 h-4 text-slate-600 group-hover:text-blue-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                          </svg>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── NOT FOUND ────────────────────────────────────────── */}
                {searchStatus === 'not_found' && (
                  <div className="z-10 flex flex-col items-center gap-4">
                    <div className="w-20 h-20 rounded-full bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                      <Package className="w-8 h-8 text-orange-400" />
                    </div>
                    <p className="text-orange-300 tracking-wide">لم يتم العثور على منتج مطابق</p>
                    <button onClick={handleClear} className="text-xs text-slate-500 hover:text-slate-300 transition-colors">بحث جديد</button>
                  </div>
                )}

                {/* ── ERROR ────────────────────────────────────────────── */}
                {searchStatus === 'error' && (
                  <div className="z-10 flex flex-col items-center gap-4">
                    <AlertCircle className="w-10 h-10 text-red-400" />
                    <p className="text-red-300 tracking-wide">{errorMsg}</p>
                    <button onClick={handleClear} className="text-xs text-slate-500 hover:text-slate-300 transition-colors">حاول مجدداً</button>
                  </div>
                )}

                {/* ── PRODUCT FOUND ────────────────────────────────────── */}
                {searchStatus === 'found' && product && (
                  <div className="z-10 w-full p-5 space-y-4">

                    {/* Product header row */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded border border-blue-500/30">{product.code}</span>
                          <span className="text-xs text-slate-500">{product.category}</span>
                        </div>
                        <h3 className="text-white font-semibold text-lg mt-1 leading-snug">{product.name}</h3>
                        {product.foreign_name && (
                          <p className="text-slate-400 text-sm mt-0.5">{product.foreign_name}</p>
                        )}
                      </div>
                      <button
                        onClick={handleClear}
                        className="text-slate-600 hover:text-slate-300 transition-colors shrink-0 mt-1"
                        title="مسح النتيجة"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Stock badge */}
                    <div className="flex items-center gap-3 flex-wrap">
                      {warehouseStock ? (
                        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl">
                          <span className="text-xs text-emerald-400/70">الرصيد في {warehouseStock.warehouse_code || warehouseStock.warehouse}</span>
                          <span className="font-bold text-emerald-400 text-base">{warehouseStock.qty}</span>
                          <span className="text-xs text-emerald-400/60">{product.uom}</span>
                        </div>
                      ) : (
                        <div className="text-xs text-slate-500 bg-white/[0.03] px-3 py-1.5 rounded-xl border border-white/[0.05]">
                          لا يوجد رصيد للمخزن الحالي
                        </div>
                      )}
                    </div>

                    {/* Barcode / UoM selector */}
                    {product.barcodes.length > 0 && (
                      <div className="space-y-1.5">
                        <p className="text-xs text-slate-500 uppercase tracking-widest">اختر الوحدة / الباركود</p>
                        <div className="flex flex-wrap gap-2">
                          {product.barcodes.map((bc, idx) => (
                            <button
                              key={bc.id ?? idx}
                              onClick={() => setSelectedBarcode(bc)}
                              className={`flex flex-col items-center px-3 py-1.5 rounded-xl border text-xs transition-all ${
                                selectedBarcode?.barcode === bc.barcode
                                  ? 'bg-blue-500/20 border-blue-500/50 text-blue-300 shadow-[0_0_10px_rgba(59,130,246,0.2)]'
                                  : 'bg-white/[0.03] border-white/[0.08] text-slate-400 hover:bg-white/[0.06] hover:border-white/[0.15]'
                              }`}
                            >
                              <span className="font-mono text-[11px] leading-tight">{bc.barcode}</span>
                              <span className="text-[10px] opacity-70 mt-0.5">{bc.uom}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Quantity input + submit */}
                    <div className="flex items-center gap-3 pt-1">
                      <div className="flex items-center flex-1 bg-black/40 border border-white/[0.1] rounded-xl overflow-hidden focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/30 transition-all">
                        <input
                          type="number"
                          min="0"
                          step="any"
                          value={quantity}
                          onChange={(e) => setQuantity(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && void handleSubmitAudit()}
                          placeholder="أدخل الكمية..."
                          className="flex-1 bg-transparent text-white px-4 py-3 text-sm font-light focus:outline-none placeholder:text-slate-600 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        />
                        {activeUom && (
                          <span className="px-3 text-xs text-slate-500 border-r border-white/[0.05] shrink-0">{activeUom}</span>
                        )}
                      </div>

                      <button
                        onClick={() => void handleSubmitAudit()}
                        disabled={!quantity || submitStatus === 'submitting'}
                        className={`flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-medium transition-all shrink-0 border ${
                          submitStatus === 'success'
                            ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400'
                            : submitStatus === 'error'
                              ? 'bg-red-500/20 border-red-500/40 text-red-400'
                              : 'bg-blue-600/90 hover:bg-blue-500 border-blue-400/30 text-white shadow-[0_0_15px_rgba(37,99,235,0.3)] disabled:opacity-40'
                        }`}
                      >
                        {submitStatus === 'submitting' && <Loader2 className="w-4 h-4 animate-spin" />}
                        {submitStatus === 'success'    && <><CheckCircle className="w-4 h-4" /><span>تم الحفظ</span></>}
                        {submitStatus === 'error'      && <><AlertCircle className="w-4 h-4" /><span>خطأ</span></>}
                        {(submitStatus === 'idle')     && <span>تسجيل الجرد</span>}
                      </button>
                    </div>

                    {/* Submit error message */}
                    {submitStatus === 'error' && errorMsg && (
                      <p className="text-xs text-red-400 px-1">{errorMsg}</p>
                    )}

                  </div>
                )}

              </div>

            </div>
          </div>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}} />
    </div>
  );
}
