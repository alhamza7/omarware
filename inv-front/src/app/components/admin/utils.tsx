import React from 'react';
import { SortConfig } from './types';

// Improved custom date formatter to strictly prevent RTL layout mixing 
// and implement single-digit hour format (h:mm)
export const formatCustomDate = (isoString: string) => {
  const d = new Date(isoString);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  
  let h = d.getHours();
  const ampm = h >= 12 ? 'م' : 'ص';
  h = h % 12;
  h = h ? h : 12; // '0' becomes '12'
  
  const formattedHour = h.toString();
  const min = String(d.getMinutes()).padStart(2, '0');

  return (
    <div className="flex items-center justify-end gap-3 font-mono text-sm" dir="ltr">
      <span className="text-slate-300 font-medium tracking-wide">
        {formattedHour}:{min} <span className="font-sans font-normal text-xs opacity-80">{ampm}</span>
      </span>
      <span className="text-[#475569]">{yyyy}/{mm}/{dd}</span>
    </div>
  );
};

// Get sorted items based on current sort direction and key
export const getSortedData = <T extends Record<string, any>>(dataArray: T[], sortConfig: SortConfig): T[] => {
  if (sortConfig.dir === 'none') return dataArray;
  
  return [...dataArray].sort((a, b) => {
    const { key, dir } = sortConfig;
    let valA = a[key];
    let valB = b[key];
    
    if (key === 'dateAdded' || key === 'date') {
      valA = new Date(valA as string).getTime();
      valB = new Date(valB as string).getTime();
    } else if (typeof valA === 'string' && typeof valB === 'string') {
      valA = valA.toLowerCase();
      valB = valB.toLowerCase();
    } else if (typeof valA === 'number' && typeof valB === 'number') {
      // Keep as numbers
    } else {
      valA = String(valA).toLowerCase();
      valB = String(valB).toLowerCase();
    }
    
    if (valA < valB) return dir === 'asc' ? -1 : 1;
    if (valA > valB) return dir === 'asc' ? 1 : -1;
    return 0;
  });
};
