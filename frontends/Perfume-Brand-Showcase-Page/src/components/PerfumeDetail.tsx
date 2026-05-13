import { motion } from 'motion/react';
import { X, Droplet, Clock, Wind, Calendar, Sparkles, Share2, Tag } from 'lucide-react';
import { Perfume } from '../types/perfume';
import { NotesPyramid } from './NotesPyramid';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface PerfumeDetailProps {
  perfume: Perfume;
  onClose: () => void;
}

export function PerfumeDetail({ perfume, onClose }: PerfumeDetailProps) {
  const handleSharePerfume = () => {
    const baseUrl = window.location.origin + window.location.pathname;
    const url = `${baseUrl}?brand=${encodeURIComponent(
      perfume.brandId,
    )}&perfume=${encodeURIComponent(perfume.id)}`;
    const text = `جرب هذا العطر "${perfume.name}" من ${perfume.brand}: ${url}`;
    const waUrl = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(waUrl, '_blank');
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-slate-900 via-emerald-900/20 to-slate-900 rounded-3xl border border-white/20 shadow-2xl"
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 z-10 p-2 rounded-full bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/20 transition-colors"
        >
          <X className="w-5 h-5 text-white" />
        </button>

        {/* Content */}
        <div className="p-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Left Column - Image */}
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="relative rounded-2xl overflow-hidden aspect-square bg-black/20"
              >
                <ImageWithFallback
                  src={perfume.image}
                  alt={perfume.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
              </motion.div>

              {/* Quick Stats */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="grid grid-cols-2 gap-3"
              >
                <div className="p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4 text-teal-400" />
                    <span className="text-sm text-white/60">Longevity</span>
                  </div>
                  <div className="text-white">{perfume.longevity}</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Wind className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm text-white/60">Sillage</span>
                  </div>
                  <div className="text-white">{perfume.sillage}</div>
                </div>
              </motion.div>
            </div>

            {/* Right Column - Details */}
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-3">
                    <Sparkles className="w-6 h-6 text-amber-400" />
                    <div className="flex flex-col">
                      <span className="text-sm text-amber-400">{perfume.brand}</span>
                      <h2 className="text-4xl text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-teal-400 to-emerald-400">
                        {perfume.name}
                      </h2>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleSharePerfume}
                    className="inline-flex items-center gap-2 rounded-full border border-emerald-400/40 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-200 hover:bg-emerald-500/20 transition-colors"
                  >
                    <Share2 className="w-4 h-4" />
                    <span>Share</span>
                  </button>
                </div>
                <p className="text-white/70 leading-relaxed">
                  {perfume.description}
                </p>
              </motion.div>

              {/* Seasons, Occasions & Tags */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="space-y-3"
              >
                <div className="p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-4 h-4 text-amber-400" />
                    <span className="text-sm text-white/60">Best Seasons</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {perfume.season.map((season) => (
                      <span
                        key={season}
                        className="px-3 py-1 rounded-full bg-gradient-to-r from-amber-500/20 to-teal-500/20 border border-amber-400/30 text-sm text-amber-300"
                      >
                        {season}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Droplet className="w-4 h-4 text-teal-400" />
                    <span className="text-sm text-white/60">Occasions</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {perfume.occasion.map((occasion) => (
                      <span
                        key={occasion}
                        className="px-3 py-1 rounded-full bg-gradient-to-r from-teal-500/20 to-emerald-500/20 border border-teal-400/30 text-sm text-teal-300"
                      >
                        {occasion}
                      </span>
                    ))}
                  </div>
                </div>

                {perfume.tags && perfume.tags.length > 0 && (
                  <div className="p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
                    <div className="flex items-center gap-2 mb-2">
                      <Tag className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm text-white/60">Tags</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {perfume.tags.map((tag) => (
                        <span
                          key={tag.id}
                          className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-400/40 text-sm text-emerald-200"
                        >
                          #{tag.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            </div>
          </div>

          {/* Notes Pyramid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-8 p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10"
          >
            <h3 className="text-center text-2xl text-white mb-2">Fragrance Pyramid</h3>
            <p className="text-center text-white/60 text-sm mb-6">
              Explore the layered composition of notes
            </p>
            <NotesPyramid
              topNotes={perfume.notes.top}
              middleNotes={perfume.notes.middle}
              baseNotes={perfume.notes.base}
            />
          </motion.div>
        </div>

        {/* Animated background elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      </motion.div>
    </motion.div>
  );
}
