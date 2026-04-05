import React from 'react';
import { useNavigate } from 'react-router';
import { LogOut, FileSpreadsheet, LayoutGrid, Building2 } from 'lucide-react';

export function BottomNav() {
  const navigate = useNavigate();

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40 animate-fade-in-up" style={{ animationDelay: '700ms' }}>
      <div className="bg-[#0A0C13]/90 backdrop-blur-xl border border-[#1F2230] rounded-full p-1.5 flex items-center shadow-[0_15px_40px_rgba(0,0,0,0.8)]">
        <button onClick={() => navigate('/inventory')} className="flex items-center gap-2 px-6 py-2.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white rounded-full text-sm font-medium transition-colors shadow-[0_0_15px_rgba(37,99,235,0.4)]">
          <LayoutGrid className="w-4 h-4" />
          <span>الجرد</span>
        </button>
        
        <button onClick={() => navigate('/reports')} className="flex items-center gap-2 px-6 py-2.5 text-[#94A3B8] hover:text-white hover:bg-white/[0.05] rounded-full text-sm transition-colors">
          <FileSpreadsheet className="w-4 h-4" />
          <span>التقارير</span>
        </button>

        <div className="w-px h-5 bg-[#1F2230] mx-1"></div>

        <button onClick={() => navigate('/select-warehouse')} className="flex items-center gap-2 px-6 py-2.5 text-[#94A3B8] hover:text-white hover:bg-white/[0.05] rounded-full text-sm transition-colors">
          <Building2 className="w-4 h-4" />
          <span>تغيير المخزن</span>
        </button>

        <div className="w-px h-5 bg-[#1F2230] mx-1"></div>

        <button onClick={() => navigate('/')} className="flex items-center gap-2 px-6 py-2.5 text-[#F87171] hover:text-[#FCA5A5] hover:bg-red-500/10 rounded-full text-sm transition-colors group">
          <span>تسجيل خروج</span>
          <LogOut className="w-4 h-4 rtl:rotate-180 group-hover:-translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
}
