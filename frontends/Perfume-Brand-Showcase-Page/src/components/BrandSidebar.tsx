import { motion } from 'motion/react';
import { Sparkles, MapPin } from 'lucide-react';
import { Brand } from '../types/perfume';

interface BrandSidebarProps {
  brands: Brand[];
  selectedBrand: string | null;
  onSelectBrand: (brandId: string) => void;
}

export function BrandSidebar({ brands, selectedBrand, onSelectBrand }: BrandSidebarProps) {
  return (
    <div className="h-full bg-gradient-to-b from-slate-900 via-emerald-900/20 to-slate-900 border-r border-white/10 p-6 overflow-y-auto">
      {/* Header */}
      <div className="mb-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 mb-2"
        >
          <Sparkles className="w-8 h-8 text-amber-400" />
          <h1 className="text-2xl text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-emerald-400">
            Maisons
          </h1>
        </motion.div>
        <p className="text-sm text-white/60">Luxury fragrance houses</p>
      </div>

      {/* Brand List */}
      <div className="space-y-3">
        {brands.map((brand, index) => (
          <motion.button
            key={brand.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => onSelectBrand(brand.id)}
            className={`w-full text-left p-4 rounded-xl transition-all duration-300 group ${
              selectedBrand === brand.id
                ? 'bg-gradient-to-r from-emerald-500/30 to-teal-500/30 border-2 border-emerald-400/50 shadow-lg shadow-emerald-500/20'
                : 'bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/30 hover:bg-white/10'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3
                  className={`mb-1 transition-all duration-300 ${
                    selectedBrand === brand.id
                      ? 'text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-emerald-400'
                      : 'text-white group-hover:text-emerald-300'
                  }`}
                >
                  {brand.name}
                </h3>
                <div className="flex items-center gap-1.5 text-xs text-white/60">
                  <MapPin className="w-3 h-3" />
                  <span>{brand.country}</span>
                </div>
              </div>
              {selectedBrand === brand.id && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-2 h-2 rounded-full bg-gradient-to-r from-amber-400 to-emerald-400"
                />
              )}
            </div>
            <div className="mt-3 text-xs text-white/50">
              {brand.perfumes.length} {brand.perfumes.length === 1 ? 'fragrance' : 'fragrances'}
            </div>

            {/* Hover glow effect */}
            {selectedBrand !== brand.id && (
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-emerald-500/0 via-emerald-500/10 to-teal-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            )}
          </motion.button>
        ))}
      </div>

      {/* Footer decoration */}
      <div className="mt-8 pt-6 border-t border-white/10">
        <div className="text-xs text-white/40 text-center">
          Select a house to explore
        </div>
      </div>
    </div>
  );
}
