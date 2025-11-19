import { motion } from 'motion/react';
import { Sparkles } from 'lucide-react';
import { Perfume } from '../types/perfume';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface PerfumeCardProps {
  perfume: Perfume;
  onClick: () => void;
}

export function PerfumeCard({ perfume, onClick }: PerfumeCardProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ y: -8, scale: 1.02 }}
      onClick={onClick}
      className="group relative cursor-pointer rounded-2xl overflow-hidden bg-gradient-to-br from-white/5 to-white/10 backdrop-blur-xl border border-white/20 hover:border-white/40 transition-all duration-300"
    >
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/20 via-transparent to-teal-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      {/* Image Container */}
      <div className="relative aspect-square overflow-hidden bg-black/20">
        <ImageWithFallback
          src={perfume.image}
          alt={perfume.name}
          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
        
        {/* Season badges */}
        <div className="absolute top-3 right-3 flex gap-2">
          {perfume.season.slice(0, 2).map((season) => (
            <span
              key={season}
              className="px-2 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs text-white"
            >
              {season}
            </span>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-5 relative z-10">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-white mb-1 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-amber-400 group-hover:to-emerald-400 transition-all duration-300">
              {perfume.name}
            </h3>
            <p className="text-sm text-white/60">{perfume.brand}</p>
          </div>
          <Sparkles className="w-5 h-5 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </div>

        {/* Mini Notes Pyramid Preview */}
        <div className="space-y-1.5 mt-4">
          <div className="flex items-center gap-2">
            <div className="h-1 w-full rounded-full bg-gradient-to-r from-amber-500/40 to-amber-500/10" />
            <span className="text-xs text-amber-400 whitespace-nowrap">
              {perfume.notes.top.slice(0, 2).join(', ')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-1 w-full rounded-full bg-gradient-to-r from-teal-500/40 to-teal-500/10" />
            <span className="text-xs text-teal-400 whitespace-nowrap">
              {perfume.notes.middle.slice(0, 2).join(', ')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-1 w-full rounded-full bg-gradient-to-r from-emerald-500/40 to-emerald-500/10" />
            <span className="text-xs text-emerald-400 whitespace-nowrap">
              {perfume.notes.base.slice(0, 2).join(', ')}
            </span>
          </div>
        </div>
      </div>

      {/* Hover border glow */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-amber-500 via-teal-500 to-emerald-500 opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-300" />
    </motion.div>
  );
}
