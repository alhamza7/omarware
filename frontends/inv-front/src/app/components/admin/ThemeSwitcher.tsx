import React from 'react';
import ToggleGastly from '../../../imports/Toggle';
import TogglePokeball from '../../../imports/Group18';

interface ThemeSwitcherProps {
  isPurpleTheme: boolean;
  onToggle: () => void;
}

export function ThemeSwitcher({ isPurpleTheme, onToggle }: ThemeSwitcherProps) {
  return (
    <button 
      onClick={onToggle}
      className="fixed top-8 right-8 z-[100] hover:scale-105 transition-all duration-300 focus:outline-none drop-shadow-[0_4px_10px_rgba(0,0,0,0.5)] hover:drop-shadow-[0_0_15px_rgba(168,85,247,0.4)] group"
      title={isPurpleTheme ? 'العودة للوضع الداكن' : 'تفعيل المظهر البنفسجي'}
    >
      <div className="relative w-[67px] h-[34px] cursor-pointer">
        <div 
          className="absolute top-0 left-0 w-[268.5px] h-[134px] pointer-events-none"
          style={{
            transform: 'scale(0.25)',
            transformOrigin: 'top left'
          }}
        >
          {/* Pokeball / Dark Mode (OFF state) */}
          <div className={`absolute top-0 left-0 w-[268px] h-[134px] transition-opacity duration-500 ${isPurpleTheme ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}`}>
            <TogglePokeball />
          </div>

          <div className="absolute top-[-133px] left-0 w-[390px] h-[400px]">
            {/* Gastly / Purple Mode (ON state) */}
            <div className={`absolute inset-0 transition-opacity duration-500 ${isPurpleTheme ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
              <ToggleGastly />
            </div>
          </div>
        </div>
      </div>
    </button>
  );
}
