import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import { SortConfig } from './types';

interface SortHeaderProps {
  label: string;
  sortKey: string;
  sortConfig: SortConfig;
  onSort: (key: string) => void;
}

export function SortHeader({ label, sortKey, sortConfig, onSort }: SortHeaderProps) {
  const isActive = sortConfig.key === sortKey;
  const dir = isActive ? sortConfig.dir : 'none';
  
  return (
    <th 
      className="px-6 py-5 cursor-pointer hover:bg-white/[0.02] transition-colors group select-none relative"
      onClick={() => onSort(sortKey)}
    >
      <div className="flex items-center gap-3 w-fit">
        <span>{label}</span>
        <div className="relative flex items-center justify-center w-5 h-5 text-[#475569] group-hover:text-slate-300 transition-colors">
          {/* Bubble State - Bursts when activated */}
          <div className={`absolute inset-0 flex items-center justify-center transition-all duration-300 ease-out ${dir !== 'none' ? 'opacity-0 scale-[2.5] blur-[2px] invisible' : 'opacity-50 group-hover:opacity-100 scale-100 visible'}`}>
            <div className="w-2.5 h-2.5 rounded-full border border-[#3B82F6] bg-[#3B82F6]/10 shadow-[inset_0_1px_3px_rgba(59,130,246,0.3)] backdrop-blur-sm"></div>
          </div>
          
          {/* Ascending State */}
          <div className={`absolute inset-0 flex items-center justify-center transition-all duration-300 ease-out ${dir === 'asc' ? 'opacity-100 scale-100 visible delay-100' : 'opacity-0 scale-50 invisible'}`}>
            <ArrowUp className="w-4 h-4 text-[#3B82F6]" />
          </div>

          {/* Descending State */}
          <div className={`absolute inset-0 flex items-center justify-center transition-all duration-300 ease-out ${dir === 'desc' ? 'opacity-100 scale-100 visible delay-100' : 'opacity-0 scale-50 invisible'}`}>
            <ArrowDown className="w-4 h-4 text-[#3B82F6]" />
          </div>
        </div>
      </div>
    </th>
  );
}
