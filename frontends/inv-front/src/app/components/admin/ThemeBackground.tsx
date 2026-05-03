import React from 'react';
import { ImageWithFallback } from '../figma/ImageWithFallback';

interface ThemeBackgroundProps {
  isPurpleTheme: boolean;
  selectedFigure: number;
  onSelectFigure: (idx: number) => void;
  figures: string[];
}

export function ThemeBackground({ isPurpleTheme, selectedFigure, onSelectFigure, figures }: ThemeBackgroundProps) {
  return (
    <div className={`fixed inset-0 pointer-events-none transition-opacity duration-1000 z-0 ${isPurpleTheme ? 'opacity-100' : 'opacity-0'}`}>
      <div className="absolute top-[-10%] right-[-5%] w-[40vw] h-[40vw] rounded-full bg-purple-500/10 blur-[100px]" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-indigo-500/10 blur-[120px]" />
      
      {/* Floating Astronaut/Theme Accent Image */}
      <div className="absolute top-10 left-10 w-72 h-72 opacity-80 mix-blend-screen animate-float-space">
        <div className="relative w-full h-full pointer-events-auto">
          <ImageWithFallback 
            src={figures[selectedFigure]} 
            alt="Space Theme Main Figure" 
            className="w-full h-full object-contain filter drop-shadow-[0_0_20px_rgba(255,255,255,0.4)] transition-all duration-500" 
          />
          <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 flex gap-2 bg-[#0A0C13]/80 backdrop-blur-xl p-1.5 rounded-full border border-white/20 z-50 shadow-xl">
            {figures.map((fig, idx) => (
              <button 
                key={idx}
                onClick={() => onSelectFigure(idx)}
                className={`w-10 h-10 rounded-full overflow-hidden transition-all duration-300 ${
                  selectedFigure === idx 
                    ? 'ring-2 ring-purple-400 scale-110 shadow-[0_0_15px_rgba(192,132,252,0.5)]' 
                    : 'opacity-50 hover:opacity-100 hover:scale-105'
                }`}
                title={`Select Figure ${idx + 1}`}
              >
                <ImageWithFallback src={fig} alt={`Figure Option ${idx + 1}`} className="w-full h-full object-cover" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
