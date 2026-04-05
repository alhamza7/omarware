import React, { useState } from 'react';
import { X, UserPlus, Loader2, AlertCircle } from 'lucide-react';
import type { Warehouse } from '../../../services/warehouseService';

export interface AddUserPayload {
  username: string;
  full_name: string;
  password: string;
  role: 'admin' | 'user';
  warehouse_id: number;
}

interface AddUserModalProps {
  warehouses: Warehouse[];
  loading: boolean;
  error: string;
  onClose: () => void;
  onSubmit: (payload: AddUserPayload) => void;
}

/** Presentational modal for adding a new inventory user. All logic handled by parent. */
export function AddUserModal({ warehouses, loading, error, onClose, onSubmit }: AddUserModalProps) {
  const [username, setUsername]   = useState('');
  const [fullName, setFullName]   = useState('');
  const [password, setPassword]   = useState('');
  const [role, setRole]           = useState<'admin' | 'user'>('user');
  const [warehouseId, setWarehouseId] = useState<number>(warehouses[0]?.id ?? 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ username: username.trim(), full_name: fullName.trim(), password, role, warehouse_id: warehouseId });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal card */}
      <div className="relative w-full max-w-md bg-[#0A0C13] border border-[#1F2230] rounded-3xl shadow-[0_25px_60px_rgba(0,0,0,0.8)] z-10 overflow-hidden animate-fade-in-up">

        {/* Header */}
        <div className="flex items-center justify-between px-7 py-5 border-b border-[#161925]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-[#C084FC]/10 border border-[#C084FC]/20 rounded-xl flex items-center justify-center">
              <UserPlus className="w-4 h-4 text-[#C084FC]" />
            </div>
            <h2 className="text-lg font-semibold text-white">إضافة مستخدم جديد</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-[#475569] hover:text-white hover:bg-white/[0.05] transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} dir="rtl" className="px-7 py-6 space-y-4">

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Username */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
              اسم المستخدم <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              dir="ltr"
              placeholder="username"
              className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#C084FC]/50 focus:border-[#C084FC]/50 transition-all placeholder:text-[#475569]"
            />
          </div>

          {/* Full name */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
              الاسم الكامل
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="اسم المستخدم الكامل"
              className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#C084FC]/50 focus:border-[#C084FC]/50 transition-all placeholder:text-[#475569]"
            />
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
              كلمة المرور <span className="text-red-400">*</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              dir="ltr"
              placeholder="••••••••"
              className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#C084FC]/50 focus:border-[#C084FC]/50 transition-all placeholder:text-[#475569]"
            />
          </div>

          {/* Role + Warehouse in a row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
                الصلاحية
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'admin' | 'user')}
                className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#C084FC]/50 focus:border-[#C084FC]/50 transition-all appearance-none cursor-pointer"
              >
                <option value="user">مستخدم</option>
                <option value="admin">مدير</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">
                المخزن <span className="text-red-400">*</span>
              </label>
              <select
                value={warehouseId}
                onChange={(e) => setWarehouseId(Number(e.target.value))}
                required
                className="w-full bg-[#08090E] border border-[#161925] text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#C084FC]/50 focus:border-[#C084FC]/50 transition-all appearance-none cursor-pointer"
              >
                {warehouses.map((wh) => (
                  <option key={wh.id} value={wh.id}>{wh.code || wh.name} — {wh.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Permissions info */}
          <div className="bg-[#08090E] border border-[#161925] rounded-xl px-4 py-3 space-y-1.5">
            <p className="text-xs font-medium text-[#94A3B8] mb-2">الصلاحيات الممنوحة في نظام الجرد:</p>
            <div className="flex items-center gap-2 text-xs text-[#475569]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
              <span>تسجيل الدخول وإجراء عمليات الجرد</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-[#475569]">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
              <span>البحث عن المنتجات وتسجيل الكميات</span>
            </div>
            {role === 'admin' && (
              <>
                <div className="flex items-center gap-2 text-xs text-[#C084FC]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#C084FC] shrink-0" />
                  <span>الوصول للوحة التحكم الإدارية</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-[#C084FC]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#C084FC] shrink-0" />
                  <span>إدارة المستخدمين وحذف الجردات</span>
                </div>
              </>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 bg-[#0D1018] border border-[#161925] text-[#94A3B8] hover:text-white rounded-xl text-sm font-medium transition-all hover:bg-[#161925]"
            >
              إلغاء
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-3 bg-[#C084FC] hover:bg-[#A855F7] text-white rounded-xl text-sm font-semibold transition-all shadow-[0_0_15px_rgba(192,132,252,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <UserPlus className="w-4 h-4" />
              }
              إضافة المستخدم
            </button>
          </div>
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
