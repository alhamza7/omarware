import React from 'react';
import { 
  CheckCircle, PieChart, Box, Users, Barcode, ClipboardList, RefreshCcw, Trash2, AlertOctagon,
  Database, Settings, Plus, Edit2, ArrowRight
} from 'lucide-react';
import { systemStats, measurementUnits, initialItemsData, initialUsersData, initialBarcodesData, initialAuditsData } from './mockData';
import { getSortedData, formatCustomDate } from './utils';
import { SortHeader } from './SortHeader';
import { ViewState, SortConfig, ItemData, UserData, BarcodeData, AuditData } from './types';

// ── Shared stat card shape (mirrors mockData.systemStats) ──────────────────
export interface StatCard {
  label: string; subLabel: string; value: string;
  color: string; shadowGlow: string;
}

// ==========================================
// Main Dashboard View
// ==========================================
export function MainDashboardView({
  onViewChange,
  stats = systemStats,
  uomStats = measurementUnits,
  onDeleteWarehouseAudits,
  onDeleteAllAudits,
}: {
  onViewChange: (view: ViewState) => void;
  stats?: StatCard[];
  uomStats?: { name: string; items: string; barcodes: string }[];
  onDeleteWarehouseAudits?: () => void;
  onDeleteAllAudits?: () => void;
}) {
  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Banner Section */}
      <div className="relative w-full rounded-tr-[3rem] rounded-bl-[3rem] rounded-tl-xl rounded-br-xl bg-[#0A0C13]/80 backdrop-blur-xl border border-white/5 p-10 flex flex-col justify-center shadow-[0_15px_50px_-10px_rgba(139,92,246,0.25)] hover:shadow-[0_20px_60px_-10px_rgba(59,130,246,0.35)] transition-all duration-500 group">
        <div className="absolute inset-0 overflow-hidden rounded-tr-[3rem] rounded-bl-[3rem] rounded-tl-xl rounded-br-xl pointer-events-none">
          <div className="absolute -top-24 -right-24 w-64 h-64 bg-blue-600/20 rounded-full blur-[80px] transition-all duration-1000 group-hover:bg-blue-600/30"></div>
          <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-purple-600/20 rounded-full blur-[80px] transition-all duration-1000 group-hover:bg-purple-600/30"></div>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent -translate-x-[100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out"></div>
        </div>
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="flex flex-col items-start gap-6">
            <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 text-[#34d399] text-sm font-medium shadow-[0_0_20px_rgba(16,185,129,0.15)] relative overflow-hidden group/badge transition-all hover:bg-[#10B981]/20 cursor-default">
              <CheckCircle className="w-4 h-4 relative z-10" />
              <span className="relative z-10">نظام SAP متصل ونشط</span>
              <span className="relative z-10 w-1.5 h-1.5 bg-[#10B981] rounded-full mr-1 animate-pulse shadow-[0_0_8px_#10B981]"></span>
            </div>
            
            <div className="space-y-2">
              <h2 className="text-3xl md:text-4xl font-light text-slate-300 tracking-wide flex items-center gap-4">
                لوحة تحكم
                <div className="h-px w-16 bg-gradient-to-l from-slate-500/50 to-transparent"></div>
              </h2>
              <h2 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-l from-[#A855F7] via-[#8B5CF6] to-[#3B82F6] drop-shadow-[0_0_20px_rgba(168,85,247,0.2)] pb-4 leading-normal">
                إدارة النظام المركزية
              </h2>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div 
            key={i}
            style={{ animationDelay: `${i * 100}ms` }}
            className={`
              bg-[#0A0C13] border rounded-3xl p-6 relative group 
              transition-all duration-400 ease-out hover:-translate-y-2 animate-fade-in-up
              ${stat.shadowGlow}
            `}
          >
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-white/[0.04] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            
            <div className="relative z-10 flex justify-between items-start">
              <div className="flex flex-col text-right">
                <span className={`text-4xl font-light mb-3 tracking-tight ${stat.color} transition-all duration-300 drop-shadow-sm group-hover:drop-shadow-[0_0_8px_currentColor]`}>
                  {stat.value}
                </span>
                <h3 className="text-sm font-semibold text-white/90">{stat.label}</h3>
                <p className="text-[11px] text-[#475569] mt-1">{stat.subLabel}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Data Management Section */}
      <div className="bg-[#0A0C13] border border-[#161925] rounded-[2rem] overflow-hidden flex flex-col animate-fade-in-up" style={{ animationDelay: '300ms' }}>
        <div className="px-8 py-5 border-b border-[#161925] flex items-center justify-between bg-[#08090E]">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-[#3B82F6]" />
            <h3 className="text-lg font-semibold text-white">إدارة البيانات</h3>
          </div>
          <Settings className="w-5 h-5 text-[#475569]" />
        </div>

        <div className="p-8 space-y-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button onClick={() => onViewChange('items')} className="flex flex-col items-center justify-center gap-3 py-6 px-4 bg-[#0D1018] border border-[#3B82F6]/20 shadow-[0_15px_30px_-15px_rgba(59,130,246,0.2)] rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:border-[#3B82F6]/50 hover:shadow-[0_15px_40px_-10px_rgba(59,130,246,0.4)] group cursor-pointer">
              <Box className="w-7 h-7 text-[#3B82F6] group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-[#E2E8F0] group-hover:text-white">عرض الأصناف</span>
            </button>
            
            <button onClick={() => onViewChange('users')} className="flex flex-col items-center justify-center gap-3 py-6 px-4 bg-[#0D1018] border border-[#C084FC]/20 shadow-[0_15px_30px_-15px_rgba(192,132,252,0.2)] rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:border-[#C084FC]/50 hover:shadow-[0_15px_40px_-10px_rgba(192,132,252,0.4)] group cursor-pointer">
              <Users className="w-7 h-7 text-[#C084FC] group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-[#E2E8F0] group-hover:text-white">عرض المستخدمين</span>
            </button>

            <button onClick={() => onViewChange('barcodes')} className="flex flex-col items-center justify-center gap-3 py-6 px-4 bg-[#0D1018] border border-[#10B981]/20 shadow-[0_15px_30px_-15px_rgba(16,185,129,0.2)] rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:border-[#10B981]/50 hover:shadow-[0_15px_40px_-10px_rgba(16,185,129,0.4)] group cursor-pointer">
              <Barcode className="w-7 h-7 text-[#10B981] group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-[#E2E8F0] group-hover:text-white">عرض الباركودات</span>
            </button>

            <button onClick={() => onViewChange('audits')} className="flex flex-col items-center justify-center gap-3 py-6 px-4 bg-[#0D1018] border border-[#F43F5E]/20 shadow-[0_15px_30px_-15px_rgba(244,63,94,0.2)] rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:border-[#F43F5E]/50 hover:shadow-[0_15px_40px_-10px_rgba(244,63,94,0.4)] group cursor-pointer">
              <ClipboardList className="w-7 h-7 text-[#F43F5E] group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium text-[#E2E8F0] group-hover:text-white">عرض الجردات</span>
            </button>
          </div>

          <div className="w-full h-px bg-gradient-to-r from-transparent via-[#1C1F2E] to-transparent"></div>

          <div className="flex flex-wrap items-center justify-start gap-4">
            <button className="flex items-center gap-3 py-3 px-6 bg-[#032314]/30 border border-[#064e3b]/50 rounded-xl transition-all duration-300 hover:-translate-y-1 hover:bg-[#032314]/60 hover:shadow-[0_10px_20px_-10px_rgba(16,185,129,0.2)] text-[#34d399] group">
              <RefreshCcw className="w-4 h-4 group-hover:animate-spin-slow" />
              <span className="text-sm font-medium">اختبار SAP</span>
            </button>
            <div className="flex-1"></div>
            <button onClick={onDeleteWarehouseAudits} className="flex items-center gap-3 py-3 px-6 bg-[#2A0E17]/30 border border-[#4C1425]/50 rounded-xl transition-all duration-300 hover:-translate-y-1 hover:bg-[#3E1121]/60 hover:shadow-[0_10px_20px_-10px_rgba(244,63,94,0.2)] text-[#F43F5E] group">
              <Trash2 className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span className="text-sm font-medium">حذف جردات المخزن</span>
            </button>
            <button onClick={onDeleteAllAudits} className="flex items-center gap-3 py-3 px-6 bg-[#2A0E17]/60 border border-[#F43F5E]/50 rounded-xl transition-all duration-300 hover:-translate-y-1 hover:bg-[#F43F5E] hover:text-white hover:shadow-[0_10px_30px_-5px_rgba(244,63,94,0.4)] text-[#F43F5E] group">
              <AlertOctagon className="w-4 h-4 group-hover:animate-pulse" />
              <span className="text-sm font-medium">حذف كل الجردات</span>
            </button>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-[#0A0C13] border border-[#161925] rounded-[2rem] overflow-hidden flex flex-col animate-fade-in-up" style={{ animationDelay: '500ms' }}>
        <div className="px-8 py-5 border-b border-[#161925] flex justify-between items-center bg-[#08090E]">
          <div className="flex items-center gap-3">
            <PieChart className="w-5 h-5 text-[#C084FC]" />
            <h3 className="text-lg font-semibold text-white">عرض البيانات (توزيع وحدات القياس)</h3>
          </div>
          <button className="text-sm text-[#3B82F6] hover:text-[#60A5FA] transition-colors font-medium">تصدير</button>
        </div>
        <div className="p-4">
          <table className="w-full text-sm text-right">
            <thead className="text-[#475569] font-light text-[11px] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-4 font-normal">الوحدة</th>
                <th className="px-6 py-4 font-normal">الأصناف</th>
                <th className="px-6 py-4 font-normal text-left">الباركودات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#161925]">
              {uomStats.map((row, i) => (
                <tr key={i} className="hover:bg-[#1A1E2E] hover:shadow-[inset_4px_0_0_#C084FC] transition-all duration-200 group/row">
                  <td className="px-6 py-5 font-medium text-slate-200 group-hover/row:text-[#C084FC] transition-colors">{row.name}</td>
                  <td className="px-6 py-5 text-[#94A3B8] font-mono">{row.items}</td>
                  <td className="px-6 py-5 text-[#94A3B8] text-left font-mono">{row.barcodes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// Items View
// ==========================================
export function ItemsView({ 
  onViewChange, 
  sortConfig, 
  onSortClick,
  items = initialItemsData,
  onDeleteItem,
}: { 
  onViewChange: (v: ViewState) => void;
  sortConfig: SortConfig;
  onSortClick: (k: string) => void;
  items?: ItemData[];
  onDeleteItem?: (id: number) => void;
}) {
  return (
    <div className="animate-fade-in-up space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button onClick={() => onViewChange('main')} className="flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors bg-[#0A0C13] border border-[#161925] px-4 py-2 rounded-xl w-fit group">
          <ArrowRight className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">العودة للوحة التحكم</span>
        </button>
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] text-sm">
            <Plus className="w-4 h-4" />
            <span>إضافة صنف</span>
          </button>
          <div className="flex items-center gap-3 px-6 py-2.5 bg-[#0A0C13] border border-[#161925] rounded-xl">
            <h2 className="text-xl font-semibold text-white">الأصناف</h2>
            <Box className="w-6 h-6 text-[#3B82F6]" />
          </div>
        </div>
      </div>

      <div className="bg-[#0A0C13] border border-[#161925] rounded-[2rem] overflow-hidden flex flex-col shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-right whitespace-nowrap">
            <thead className="bg-[#08090E] border-b border-[#161925]">
              <tr className="text-[#94A3B8] text-sm font-medium">
                <SortHeader label="رقم" sortKey="id" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="كود الصنف" sortKey="code" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="اسم الصنف" sortKey="name" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="تاريخ الإضافة" sortKey="dateAdded" sortConfig={sortConfig} onSort={onSortClick} />
                <th className="px-6 py-5 w-[120px]">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#161925]">
              {getSortedData(items, sortConfig).map((item, index) => (
                <tr key={item.id} className="hover:bg-[#1A1E2E] hover:shadow-[inset_4px_0_0_#3B82F6] transition-all duration-200 group/row" style={{ animationDelay: `${index * 50}ms` }}>
                  <td className="px-6 py-5 text-[#E2E8F0] font-mono text-sm">{item.id}</td>
                  <td className="px-6 py-5 text-[#94A3B8] font-mono text-sm group-hover/row:text-white transition-colors">{item.code}</td>
                  <td className="px-6 py-5 font-medium text-slate-200 group-hover/row:text-[#3B82F6] transition-colors">{item.name}</td>
                  <td className="px-6 py-5">{formatCustomDate(item.dateAdded)}</td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-3">
                      <button className="p-2 bg-[#1E293B]/40 hover:bg-[#1E293B] border border-[#334155]/50 hover:border-[#F59E0B]/50 rounded-lg text-[#F59E0B] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button className="p-2 bg-[#2A0E17]/40 hover:bg-[#3E1121] border border-[#4C1425]/50 hover:border-[#F43F5E]/50 rounded-lg text-[#F43F5E] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(244,63,94,0.2)]">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// Users View
// ==========================================
export function UsersView({ 
  onViewChange, 
  sortConfig, 
  onSortClick,
  users = initialUsersData,
  onDeleteUser,
  onAddUser,
  onImportUser,
}: { 
  onViewChange: (v: ViewState) => void;
  sortConfig: SortConfig;
  onSortClick: (k: string) => void;
  users?: UserData[];
  onDeleteUser?: (id: number) => void;
  onAddUser?: () => void;
  onImportUser?: () => void;
}) {
  return (
    <div className="animate-fade-in-up space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button onClick={() => onViewChange('main')} className="flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors bg-[#0A0C13] border border-[#161925] px-4 py-2 rounded-xl w-fit group">
          <ArrowRight className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">العودة للوحة التحكم</span>
        </button>
        <div className="flex items-center gap-4">
          <button onClick={onImportUser} className="flex items-center gap-2 bg-[#0A0C13] hover:bg-[#0D1018] border border-[#10B981]/40 hover:border-[#10B981]/70 text-[#10B981] px-5 py-2.5 rounded-xl font-medium transition-all text-sm">
            <Plus className="w-4 h-4" />
            <span>استيراد من أودو</span>
          </button>
          <button onClick={onAddUser} className="flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] text-sm">
            <Plus className="w-4 h-4" />
            <span>إضافة مستخدم</span>
          </button>
          <div className="flex items-center gap-3 px-6 py-2.5 bg-[#0A0C13] border border-[#161925] rounded-xl">
            <h2 className="text-xl font-semibold text-white">المستخدمين</h2>
            <Users className="w-6 h-6 text-[#C084FC]" />
          </div>
        </div>
      </div>

      <div className="bg-[#0A0C13] border border-[#161925] rounded-[2rem] overflow-hidden flex flex-col shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-right whitespace-nowrap">
            <thead className="bg-[#08090E] border-b border-[#161925]">
              <tr className="text-[#94A3B8] text-sm font-medium">
                <SortHeader label="رقم" sortKey="id" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="الاسم الكامل" sortKey="fullName" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="اسم المستخدم" sortKey="username" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="الدور" sortKey="role" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="المخزن" sortKey="warehouse" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="تاريخ الإنشاء" sortKey="dateAdded" sortConfig={sortConfig} onSort={onSortClick} />
                <th className="px-6 py-5 w-[120px]">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#161925]">
              {getSortedData(users, sortConfig).map((user, index) => (
                <tr key={user.id} className="hover:bg-[#1A1E2E] hover:shadow-[inset_4px_0_0_#C084FC] transition-all duration-200 group/row" style={{ animationDelay: `${index * 50}ms` }}>
                  <td className="px-6 py-5 text-[#E2E8F0] font-mono text-sm">{user.id}</td>
                  <td className="px-6 py-5 font-medium text-slate-200 group-hover/row:text-[#C084FC] transition-colors">{user.fullName}</td>
                  <td className="px-6 py-5 text-[#94A3B8] group-hover/row:text-white transition-colors">{user.username}</td>
                  <td className="px-6 py-5 text-[#E2E8F0]">{user.role}</td>
                  <td className="px-6 py-5 text-[#94A3B8] font-mono text-sm">{user.warehouse}</td>
                  <td className="px-6 py-5">{formatCustomDate(user.dateAdded)}</td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-3">
                      <button className="p-2 bg-[#1E293B]/40 hover:bg-[#1E293B] border border-[#334155]/50 hover:border-[#F59E0B]/50 rounded-lg text-[#F59E0B] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => onDeleteUser?.(user.id)} className="p-2 bg-[#2A0E17]/40 hover:bg-[#3E1121] border border-[#4C1425]/50 hover:border-[#F43F5E]/50 rounded-lg text-[#F43F5E] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(244,63,94,0.2)]">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// Barcodes View
// ==========================================
export function BarcodesView({ 
  onViewChange, 
  sortConfig, 
  onSortClick,
  barcodes = initialBarcodesData,
  onDeleteBarcode,
}: { 
  onViewChange: (v: ViewState) => void;
  sortConfig: SortConfig;
  onSortClick: (k: string) => void;
  barcodes?: BarcodeData[];
  onDeleteBarcode?: (id: number) => void;
}) {
  return (
    <div className="animate-fade-in-up space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button onClick={() => onViewChange('main')} className="flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors bg-[#0A0C13] border border-[#161925] px-4 py-2 rounded-xl w-fit group">
          <ArrowRight className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">العودة للوحة التحكم</span>
        </button>
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] text-sm">
            <Plus className="w-4 h-4" />
            <span>إضافة باركود</span>
          </button>
          <div className="flex items-center gap-3 px-6 py-2.5 bg-[#0A0C13] border border-[#161925] rounded-xl">
            <h2 className="text-xl font-semibold text-white">الباركودات</h2>
            <Barcode className="w-6 h-6 text-[#10B981]" />
          </div>
        </div>
      </div>

      <div className="bg-[#0A0C13] border border-[#161925] rounded-[2rem] overflow-hidden flex flex-col shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-right whitespace-nowrap">
            <thead className="bg-[#08090E] border-b border-[#161925]">
              <tr className="text-[#94A3B8] text-sm font-medium">
                <SortHeader label="رقم" sortKey="id" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="كود الصنف" sortKey="code" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="اسم الصنف" sortKey="name" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="الباركود" sortKey="barcode" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="وحدة القياس" sortKey="unit" sortConfig={sortConfig} onSort={onSortClick} />
                <th className="px-6 py-5 w-[120px]">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#161925]">
              {getSortedData(barcodes, sortConfig).map((item, index) => (
                <tr key={item.id} className="hover:bg-[#1A1E2E] hover:shadow-[inset_4px_0_0_#10B981] transition-all duration-200 group/row" style={{ animationDelay: `${index * 50}ms` }}>
                  <td className="px-6 py-5 text-[#E2E8F0] font-mono text-sm">{item.id}</td>
                  <td className="px-6 py-5 text-[#94A3B8] font-mono text-sm group-hover/row:text-white transition-colors">{item.code}</td>
                  <td className="px-6 py-5 font-medium text-slate-200 group-hover/row:text-[#10B981] transition-colors">{item.name}</td>
                  <td className="px-6 py-5 text-[#E2E8F0] font-mono text-sm">{item.barcode}</td>
                  <td className="px-6 py-5 text-[#94A3B8]">{item.unit}</td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-3">
                      <button className="p-2 bg-[#1E293B]/40 hover:bg-[#1E293B] border border-[#334155]/50 hover:border-[#F59E0B]/50 rounded-lg text-[#F59E0B] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => onDeleteBarcode?.(item.id)} className="p-2 bg-[#2A0E17]/40 hover:bg-[#3E1121] border border-[#4C1425]/50 hover:border-[#F43F5E]/50 rounded-lg text-[#F43F5E] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(244,63,94,0.2)]">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// Audits View
// ==========================================
export function AuditsView({ 
  onViewChange, 
  sortConfig, 
  onSortClick,
  audits = initialAuditsData,
  onDeleteAudit,
}: { 
  onViewChange: (v: ViewState) => void;
  sortConfig: SortConfig;
  onSortClick: (k: string) => void;
  audits?: AuditData[];
  onDeleteAudit?: (id: number) => void;
}) {
  return (
    <div className="animate-fade-in-up space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button onClick={() => onViewChange('main')} className="flex items-center gap-2 text-[#94A3B8] hover:text-white transition-colors bg-[#0A0C13] border border-[#161925] px-4 py-2 rounded-xl w-fit group">
          <ArrowRight className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">العودة للوحة التحكم</span>
        </button>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 px-6 py-2.5 bg-[#0A0C13] border border-[#161925] rounded-xl">
            <h2 className="text-xl font-semibold text-white">الجردات</h2>
            <ClipboardList className="w-6 h-6 text-[#F43F5E]" />
          </div>
        </div>
      </div>

      <div className="bg-[#0A0C13] border border-[#161925] rounded-[2rem] overflow-hidden flex flex-col shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-right whitespace-nowrap">
            <thead className="bg-[#08090E] border-b border-[#161925]">
              <tr className="text-[#94A3B8] text-sm font-medium">
                <SortHeader label="رقم" sortKey="id" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="كود الصنف" sortKey="code" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="اسم الصنف" sortKey="name" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="المخزن" sortKey="warehouse" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="الكمية" sortKey="quantity" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="المستخدم" sortKey="user" sortConfig={sortConfig} onSort={onSortClick} />
                <SortHeader label="التاريخ" sortKey="date" sortConfig={sortConfig} onSort={onSortClick} />
                <th className="px-6 py-5 w-[120px]">إجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#161925]">
              {getSortedData(audits, sortConfig).map((audit, index) => (
                <tr key={audit.id} className="hover:bg-[#1A1E2E] hover:shadow-[inset_4px_0_0_#F43F5E] transition-all duration-200 group/row" style={{ animationDelay: `${index * 50}ms` }}>
                  <td className="px-6 py-5 text-[#E2E8F0] font-mono text-sm">{audit.id}</td>
                  <td className="px-6 py-5 text-[#94A3B8] font-mono text-sm group-hover/row:text-white transition-colors">{audit.code}</td>
                  <td className="px-6 py-5 font-medium text-slate-200 group-hover/row:text-[#F43F5E] transition-colors">{audit.name}</td>
                  <td className="px-6 py-5 text-[#E2E8F0] font-mono text-sm">{audit.warehouse}</td>
                  <td className="px-6 py-5 text-[#3B82F6] font-mono font-medium">{audit.quantity}</td>
                  <td className="px-6 py-5 text-[#94A3B8]">{audit.user}</td>
                  <td className="px-6 py-5">{formatCustomDate(audit.date)}</td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-3">
                      <button className="p-2 bg-[#1E293B]/40 hover:bg-[#1E293B] border border-[#334155]/50 hover:border-[#F59E0B]/50 rounded-lg text-[#F59E0B] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(245,158,11,0.2)]">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => onDeleteAudit?.(audit.id)} className="p-2 bg-[#2A0E17]/40 hover:bg-[#3E1121] border border-[#4C1425]/50 hover:border-[#F43F5E]/50 rounded-lg text-[#F43F5E] transition-all shadow-sm hover:shadow-[0_0_10px_rgba(244,63,94,0.2)]">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
