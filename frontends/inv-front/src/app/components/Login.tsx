import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import imgGlassyPanel from 'figma:asset/72b153857e79471275ad26858336b4131717a696.png';
import { loginUser } from '../../services/authService';
import { isAuthenticated } from '../../services/apiClient';

export function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  /** Redirect if already authenticated */
  useEffect(() => {
    if (isAuthenticated()) void navigate('/select-warehouse', { replace: true });
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await loginUser({ username, password });
      void navigate('/select-warehouse');
    } catch (err: unknown) {
      const raw = err instanceof Error ? err.message : '';
      // Translate known server messages to Arabic
      if (raw.toLowerCase().includes('invalid credentials') || raw.includes('401')) {
        setError('اسم المستخدم أو كلمة المرور غير صحيحة');
      } else if (raw.toLowerCase().includes('required')) {
        setError('يرجى إدخال اسم المستخدم وكلمة المرور');
      } else if (raw.toLowerCase().includes('connection') || raw.toLowerCase().includes('network')) {
        setError('تعذر الاتصال بالخادم، تحقق من الشبكة');
      } else {
        setError(raw || 'فشل تسجيل الدخول');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div dir="rtl" className="min-h-screen bg-[#020617] relative overflow-hidden flex items-center justify-center font-sans text-slate-100 p-4 selection:bg-blue-500/30">
      
      {/* Background Decorative Elements */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 blur-[120px] rounded-full mix-blend-screen pointer-events-none"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600/20 blur-[120px] rounded-full mix-blend-screen pointer-events-none"></div>

      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center z-10">
        
        {/* Left Side: Visual/Branding */}
        <div className="hidden lg:flex flex-col items-center justify-center relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent rounded-3xl blur-2xl"></div>
          <img 
            src={imgGlassyPanel} 
            alt="Dashboard Concept" 
            className="w-[80%] max-w-md object-contain drop-shadow-[0_20px_50px_rgba(0,0,0,0.5)] animate-[pulse_4s_ease-in-out_infinite] hover:scale-105 transition-transform duration-700"
            style={{ filter: 'brightness(0.9) contrast(1.1)' }}
          />
          <div className="mt-8 text-center space-y-2 relative z-10">
            <h2 className="text-3xl font-light tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              نظام الجرد الذكي
            </h2>
            <p className="text-slate-400/80 text-sm tracking-widest uppercase">الجيل القادم من إدارة المخزون</p>
          </div>
        </div>

        {/* Right Side: Login Form (Glassy Panel) */}
        <div className="w-full max-w-md mx-auto relative group">
          {/* Subtle glow behind the card */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-3xl blur opacity-20 group-hover:opacity-30 transition duration-1000"></div>
          
          <div className="relative bg-white/[0.03] backdrop-blur-2xl p-8 sm:p-12 rounded-3xl shadow-[0_8px_32px_0_rgba(0,0,0,0.36)] border border-white/[0.08]">
            <div className="text-center mb-10">
              <div className="w-16 h-16 mx-auto bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-6 flex items-center justify-center shadow-lg shadow-blue-500/30 ring-1 ring-white/20">
                <span className="text-2xl font-bold text-white">W</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-semibold mb-2 text-white/90">تسجيل الدخول</h1>
              <p className="text-slate-400/80 text-sm">أدخل بيانات الاعتماد للوصول لنظامك</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-6">
              <div className="space-y-2 group/input">
                <label className="block text-xs font-medium text-slate-400/80 uppercase tracking-wider text-right" htmlFor="username">
                  اسم المستخدم
                </label>
                <div className="relative">
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-black/20 border border-white/[0.05] text-white rounded-xl px-4 py-3.5 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-white/[0.05] transition-all text-left placeholder:text-slate-600"
                    dir="ltr"
                    placeholder="Username"
                    required
                  />
                  <div className="absolute inset-0 rounded-xl pointer-events-none shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"></div>
                </div>
              </div>

              <div className="space-y-2 group/input">
                <label className="block text-xs font-medium text-slate-400/80 uppercase tracking-wider text-right" htmlFor="password">
                  كلمة المرور
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-black/20 border border-white/[0.05] text-white rounded-xl px-4 py-3.5 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-white/[0.05] transition-all text-left placeholder:text-slate-600"
                    dir="ltr"
                    placeholder="••••••••"
                    required
                  />
                  <div className="absolute inset-0 rounded-xl pointer-events-none shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"></div>
                </div>
              </div>

              {error && (
                <p className="text-red-400 text-sm text-center bg-red-500/10 border border-red-500/20 rounded-xl py-2 px-4">{error}</p>
              )}

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full relative overflow-hidden bg-blue-600 text-white font-medium py-3.5 px-4 rounded-xl transition-all hover:bg-blue-500 active:scale-[0.98] shadow-[0_0_20px_rgba(37,99,235,0.4)] group/btn border border-blue-400/30 disabled:opacity-60"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400/0 via-white/20 to-blue-400/0 -translate-x-[100%] group-hover/btn:translate-x-[100%] transition-transform duration-700 ease-in-out"></div>
                  <span className="relative z-10">
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" />
                        جاري الدخول...
                      </span>
                    ) : 'دخول آمن'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>

      </div>
    </div>
  );
}
