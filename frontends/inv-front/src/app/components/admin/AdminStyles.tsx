import React from 'react';

export function AdminStyles() {
  return (
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
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        opacity: 0;
      }
      .animate-fade-in-down {
        animation: fadeInDown 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        opacity: 0;
      }
      @keyframes floatSpace {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(5deg); }
        100% { transform: translateY(0px) rotate(0deg); }
      }
      .animate-float-space {
        animation: floatSpace 8s ease-in-out infinite;
      }

      /* Neumorphic Purple Space Theme Overrides */
      /* Core Backgrounds */
      .theme-purple.bg-\\[\\#05060A\\] { background-color: #514E7B !important; }
      
      /* Cards */
      .theme-purple .bg-\\[\\#0A0C13\\] { 
        background-color: #686396 !important; 
        border-color: rgba(255,255,255,0.15) !important;
        box-shadow: 10px 10px 25px rgba(45, 40, 75, 0.4), inset 1px 1px 2px rgba(255, 255, 255, 0.3) !important;
      }
      .theme-purple .bg-\\[\\#0A0C13\\]\\/80 { 
        background-color: rgba(104, 99, 150, 0.85) !important; 
        border-color: rgba(255,255,255,0.2) !important;
      }
      .theme-purple .bg-\\[\\#0A0C13\\]\\/90 { 
        background-color: rgba(90, 85, 130, 0.9) !important; 
        border-color: rgba(255,255,255,0.1) !important;
      }
      
      /* Table Headers & Secondary Backgrounds */
      .theme-purple .bg-\\[\\#08090E\\] { 
        background-color: #5E5A8A !important; 
        border-bottom-color: rgba(255,255,255,0.1) !important; 
      }
      
      /* Borders */
      .theme-purple .border-\\[\\#161925\\] { border-color: rgba(255, 255, 255, 0.12) !important; }
      .theme-purple .divide-\\[\\#161925\\] > :not([hidden]) ~ :not([hidden]) { border-color: rgba(255, 255, 255, 0.1) !important; }
      .theme-purple .bg-\\[\\#161925\\] { background-color: rgba(255, 255, 255, 0.08) !important; }
      
      /* Hover States & Stripes */
      .theme-purple .bg-\\[\\#1A1E2E\\] { background-color: rgba(255, 255, 255, 0.05) !important; }
      .theme-purple .hover\\:bg-\\[\\#1A1E2E\\]:hover { background-color: rgba(255, 255, 255, 0.1) !important; }
      
      /* Typography */
      .theme-purple .text-slate-300 { color: #FFFFFF !important; }
      .theme-purple .text-slate-200 { color: #FFFFFF !important; }
      .theme-purple .text-slate-400 { color: #E8E6F5 !important; }
      .theme-purple .text-\\[\\#475569\\] { color: #D5D1EB !important; }
      .theme-purple .text-\\[\\#94A3B8\\] { color: #EBE8FA !important; }
      .theme-purple .text-\\[\\#E2E8F0\\] { color: #FFFFFF !important; }
      
      /* Specific Colors */
      .theme-purple .text-\\[\\#3B82F6\\] { color: #D8B4FE !important; }
      .theme-purple .bg-\\[\\#3B82F6\\]\\/10 { background-color: rgba(216, 180, 254, 0.15) !important; }
      .theme-purple .border-\\[\\#3B82F6\\] { border-color: #D8B4FE !important; }
      
      .theme-purple .bg-\\[\\#2563EB\\] { background-color: #8B5CF6 !important; }
      .theme-purple .hover\\:bg-\\[\\#1D4ED8\\]:hover { background-color: #7C3AED !important; }
      .theme-purple .shadow-\\[0_0_15px_rgba\\(37\\,99\\,235\\,0\\.4\\)\\] { box-shadow: 0 0 15px rgba(139, 92, 246, 0.5) !important; }
      .theme-purple .shadow-\\[inset_0_1px_3px_rgba\\(59\\,130\\,246\\,0\\.3\\)\\] { box-shadow: inset 0 1px 3px rgba(216, 180, 254, 0.4) !important; }
      
      .theme-purple .border-\\[\\#1F2230\\] { border-color: rgba(255,255,255,0.1) !important; }
      .theme-purple .bg-\\[\\#1F2230\\] { background-color: rgba(255,255,255,0.2) !important; }
    `}} />
  );
}
