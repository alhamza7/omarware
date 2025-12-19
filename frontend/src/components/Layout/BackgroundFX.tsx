import { useEffect, useMemo, useRef } from 'react';

type Vec2 = { x: number; y: number };

function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n));
}

export default function BackgroundFX() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<Vec2>({ x: -9999, y: -9999 });
  const sizeRef = useRef<{ w: number; h: number; dpr: number }>({ w: 0, h: 0, dpr: 1 });

  const lines = useMemo(() => {
    // Pre-generate some diagonal “threads”
    const arr: Array<{ a: number; b: number; speed: number; phase: number }> = [];
    for (let i = 0; i < 18; i++) {
      arr.push({
        a: (Math.random() * 2 - 1) * 0.9, // slope-ish
        b: Math.random(), // intercept-ish
        speed: 0.08 + Math.random() * 0.18,
        phase: Math.random() * Math.PI * 2,
      });
    }
    return arr;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      const dpr = clamp(window.devicePixelRatio || 1, 1, 2);
      const w = window.innerWidth;
      const h = window.innerHeight;
      sizeRef.current = { w, h, dpr };
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const onMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    const onLeave = () => {
      mouseRef.current = { x: -9999, y: -9999 };
    };

    resize();
    window.addEventListener('resize', resize, { passive: true });
    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('mouseleave', onLeave, { passive: true });

    let raf = 0;
    const t0 = performance.now();

    const draw = (t: number) => {
      const { w, h } = sizeRef.current;
      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;
      const tt = (t - t0) / 1000;

      // Clear
      ctx.clearRect(0, 0, w, h);

      // Base subtle grid
      ctx.globalAlpha = 1;
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(0,0,0,0.04)';
      const grid = 56;
      for (let x = 0; x <= w; x += grid) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y <= h; y += grid) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Animated “threads”
      for (let i = 0; i < lines.length; i++) {
        const L = lines[i];
        const wave = Math.sin(tt * L.speed + L.phase);
        // Very subtle drift, plus a tiny cursor influence (no glow)
        const cursorInfluence = mx > -1000 ? (mx / w - 0.5) * 0.06 : 0;
        const offset = (wave * 0.018 + 0.5 + cursorInfluence) * h; // base vertical offset

        // Distance to mouse to brighten nearby lines
        const yAtMx = (L.a * (mx / w) + L.b) * h;
        const dist = Math.abs(yAtMx - my);
        const intensity = mx > -1000 ? (1 - clamp(dist / 240, 0, 1)) : 0;

        ctx.strokeStyle = `rgba(0,0,0,${0.03 + intensity * 0.06})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, offset * 0.2 + (L.b * h) * 0.8);
        ctx.bezierCurveTo(
          w * 0.33,
          offset * 0.45 + (L.a * 0.25 + L.b) * h,
          w * 0.66,
          offset * 0.65 + (L.a * 0.55 + L.b) * h,
          w,
          offset * 0.85 + (L.a * 0.85 + L.b) * h
        );
        ctx.stroke();
      }

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize as any);
      window.removeEventListener('mousemove', onMove as any);
      window.removeEventListener('mouseleave', onLeave as any);
    };
  }, [lines]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}


