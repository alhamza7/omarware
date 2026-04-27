import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { BrandSidebar } from './components/BrandSidebar';
import { PerfumeCard } from './components/PerfumeCard';
import { PerfumeDetail } from './components/PerfumeDetail';
import { perfumeAPI, Brand, Perfume } from './services/api';

export default function App() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [selectedPerfume, setSelectedPerfume] = useState<Perfume | null>(null);
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const updateUrl = (opts: { brand?: string | null; perfume?: string | null; tag?: string | null }) => {
    const params = new URLSearchParams(window.location.search);

    if ('brand' in opts) {
      if (opts.brand) params.set('brand', opts.brand);
      else params.delete('brand');
    }
    if ('perfume' in opts) {
      if (opts.perfume) params.set('perfume', opts.perfume);
      else params.delete('perfume');
    }
    if ('tag' in opts) {
      if (opts.tag) params.set('tag', opts.tag);
      else params.delete('tag');
    }

    const query = params.toString();
    const newUrl = `${window.location.pathname}${query ? `?${query}` : ''}`;
    window.history.replaceState({}, '', newUrl);
  };

  useEffect(() => {
    const fetchBrands = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await perfumeAPI.getBrands();
        setBrands(data);

        const params = new URLSearchParams(window.location.search);
        const brandParam = params.get('brand');
        const perfumeParam = params.get('perfume');
        const tagParam = params.get('tag');

        let initialBrand: Brand | undefined;
        if (brandParam) {
          initialBrand = data.find((b) => b.id === brandParam);
        }
        if (!initialBrand && data.length > 0) {
          initialBrand = data[0];
        }

        if (initialBrand) {
          setSelectedBrand(initialBrand.id);
        }

        if (tagParam) {
          setActiveTag(tagParam);
        }

        if (perfumeParam && initialBrand) {
          const foundPerfume = initialBrand.perfumes.find((p) => p.id === perfumeParam);
          if (foundPerfume) {
            setSelectedPerfume(foundPerfume);
          }
        }
      } catch (err) {
        console.error('Error fetching brands:', err);
        setError(err instanceof Error ? err.message : 'Failed to load brands');
      } finally {
        setLoading(false);
      }
    };

    fetchBrands();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const currentBrand = brands.find((brand) => brand.id === selectedBrand);
  const visiblePerfumes = currentBrand
    ? currentBrand.perfumes.filter((perfume) =>
        !activeTag ? true : perfume.tags?.some((tag) => tag.id === activeTag),
      )
    : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-emerald-950 to-slate-950">
      <div className="flex h-screen">
        {/* Sidebar - Brand Navigation */}
        <div className="w-80 flex-shrink-0">
          <BrandSidebar
            brands={brands}
            selectedBrand={selectedBrand}
            onSelectBrand={(id) => {
              setSelectedBrand(id);
              setSelectedPerfume(null);
              updateUrl({ brand: id, perfume: null });
            }}
          />
        </div>

        {/* Main Content - Perfume Grid */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-8">
            {loading && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-white/20 flex items-center justify-center"
                  >
                    <span className="text-4xl animate-spin">🌸</span>
                  </motion.div>
                  <h3 className="text-xl text-white mb-2">Loading...</h3>
                  <p className="text-white/60">Fetching perfume data</p>
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-20 h-20 mx-auto mb-4 rounded-full bg-red-500/20 border border-red-500/20 flex items-center justify-center"
                  >
                    <span className="text-4xl">⚠️</span>
                  </motion.div>
                  <h3 className="text-xl text-white mb-2">Error Loading Data</h3>
                  <p className="text-white/60 mb-4">{error}</p>
                  <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-300 hover:bg-emerald-500/30 transition-colors"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            {!loading && !error && currentBrand && (
              <motion.div
                key={currentBrand.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                {/* Header */}
                <div className="mb-8 flex items-center justify-between gap-4">
                  <motion.h2
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-4xl text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-teal-400 to-emerald-400 mb-2"
                  >
                    {currentBrand.name}
                  </motion.h2>
                  <div className="flex flex-col items-end gap-2">
                    <motion.p
                      initial={{ opacity: 0, y: -20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                      className="text-white/60"
                    >
                      Discover {currentBrand.perfumes.length} exquisite{' '}
                      {currentBrand.perfumes.length === 1 ? 'fragrance' : 'fragrances'}
                    </motion.p>
                    <button
                      type="button"
                      onClick={() => {
                        const baseUrl = window.location.origin + window.location.pathname;
                        const url = `${baseUrl}?brand=${encodeURIComponent(currentBrand.id)}`;
                        const text = `اكتشف عطور \"${currentBrand.name}\" هنا: ${url}`;
                        const waUrl = `https://wa.me/?text=${encodeURIComponent(text)}`;
                        window.open(waUrl, '_blank');
                      }}
                      className="inline-flex items-center gap-2 rounded-full border border-emerald-400/40 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-200 hover:bg-emerald-500/20 transition-colors"
                    >
                      <span>Share Brand</span>
                    </button>
                  </div>
                </div>

                {/* Perfume Grid */}
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentBrand.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                  >
                    {visiblePerfumes.map((perfume) => (
                      <PerfumeCard
                        key={perfume.id}
                        perfume={perfume}
                        onClick={() => {
                          setSelectedPerfume(perfume);
                          updateUrl({ brand: perfume.brandId || currentBrand.id, perfume: perfume.id });
                        }}
                      />
                    ))}
                  </motion.div>
                </AnimatePresence>
              </motion.div>
            )}

            {!loading && !error && !currentBrand && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-white/20 flex items-center justify-center"
                  >
                    <span className="text-4xl">🌸</span>
                  </motion.div>
                  <h3 className="text-xl text-white mb-2">Select a House</h3>
                  <p className="text-white/60">Choose a fragrance house from the sidebar</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Perfume Detail Modal */}
      <AnimatePresence>
        {selectedPerfume && (
          <PerfumeDetail
            perfume={selectedPerfume}
            onClose={() => {
              setSelectedPerfume(null);
              updateUrl({ perfume: null });
            }}
          />
        )}
      </AnimatePresence>

      {/* Animated background elements */}
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none animate-pulse" />
      <div className="fixed bottom-0 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none animate-pulse" style={{ animationDelay: '1s' }} />
    </div>
  );
}
