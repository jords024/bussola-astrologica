import { useEffect, useRef } from "react";

type Star = {
  x: number;
  y: number;
  z: number;
  size: number;
  hue: 0 | 1 | 2;
  phase: number;
  tw: number;
};

type Shooting = { x: number; y: number; vx: number; vy: number; life: number; len: number };

/**
 * Campo estelar volumétrico com estrelas redondas (sprites com halo radial),
 * cintilação individual, deriva ambiente lenta e rastros durante o scroll.
 * O render pausa quando a cena sai da tela.
 */
export default function GalaxyScroll({ opacity = 1 }: { opacity?: number }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const isMobile = window.matchMedia("(max-width: 767px)").matches;
    const cores =
      (navigator as unknown as { hardwareConcurrency?: number }).hardwareConcurrency ?? 4;
    const mem = (navigator as unknown as { deviceMemory?: number }).deviceMemory ?? 4;
    const lowEnd = isMobile && (cores <= 4 || mem <= 4);

    let width = 0;
    let height = 0;
    const DEPTH = 1400;
    const count = reduced ? 0 : lowEnd ? 110 : isMobile ? 190 : 520;
    const stars: Star[] = [];

    const spawn = (z?: number): Star => {
      const r = Math.random();
      return {
        x: (Math.random() - 0.5) * 2400,
        y: (Math.random() - 0.5) * 2400,
        z: z ?? Math.random() * DEPTH,
        size: 0.5 + Math.random() * 1.5,
        hue: r > 0.88 ? 1 : r > 0.72 ? 2 : 0,
        phase: Math.random() * Math.PI * 2,
        tw: 0.6 + Math.random() * 1.6,
      };
    };
    for (let i = 0; i < count; i++) stars.push(spawn());

    // sprites redondos pré-renderizados (branco, dourado, azulado)
    const PALETTE: Array<[number, number, number]> = [
      [232, 240, 255],
      [226, 178, 92],
      [150, 186, 255],
    ];
    const SPRITE = 64;
    const sprites = PALETTE.map(([r, g, b]) => {
      const c = document.createElement("canvas");
      c.width = c.height = SPRITE;
      const sc = c.getContext("2d")!;
      const grd = sc.createRadialGradient(
        SPRITE / 2,
        SPRITE / 2,
        0,
        SPRITE / 2,
        SPRITE / 2,
        SPRITE / 2,
      );
      grd.addColorStop(0, `rgba(255,255,255,1)`);
      grd.addColorStop(0.18, `rgba(${r},${g},${b},0.95)`);
      grd.addColorStop(0.42, `rgba(${r},${g},${b},0.28)`);
      grd.addColorStop(1, `rgba(${r},${g},${b},0)`);
      sc.fillStyle = grd;
      sc.fillRect(0, 0, SPRITE, SPRITE);
      return c;
    });

    const scale = lowEnd ? 0.65 : isMobile ? 0.8 : 1;
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, isMobile ? 1.25 : 1.75) * scale;
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    let velocity = 0;
    let raf = 0;
    let running = false;
    let visible = true;
    let lastScrollY = window.scrollY;
    let t = 0;

    const focal = isMobile ? 340 : 470;
    const AMBIENT = reduced ? 0 : lowEnd ? 0.16 : 0.34; // deriva constante suave
    const shooting: Shooting[] = [];
    let nextShoot = 2600 + Math.random() * 4000;

    const render = (now: number) => {
      const dt = Math.min(48, now - t || 16);
      t = now;

      velocity *= 0.93;
      if (Math.abs(velocity) < 0.03) velocity = 0;
      const move = velocity + AMBIENT;

      ctx.clearRect(0, 0, width, height);
      ctx.globalCompositeOperation = "lighter";

      const cx = width / 2;
      const cy = height / 2;
      const speed = Math.abs(velocity);
      const drawTrails = !lowEnd && speed > 0.6;

      for (let i = 0; i < stars.length; i++) {
        const s = stars[i]!;
        s.z -= move;
        if (s.z <= 1) Object.assign(s, spawn(DEPTH));
        else if (s.z > DEPTH) Object.assign(s, spawn(1 + Math.random() * 40));

        const k = focal / s.z;
        const x = cx + s.x * k;
        const y = cy + s.y * k;
        if (x < -60 || x > width + 60 || y < -60 || y > height + 60) continue;

        const depthFade = 1 - s.z / DEPTH;
        const twinkle = 0.72 + 0.28 * Math.sin(now * 0.0016 * s.tw + s.phase);
        const alpha = Math.max(0, Math.min(1, (0.06 + depthFade * 0.94) * twinkle));
        const r = Math.max(0.55, s.size * k * 1.5);

        if (drawTrails) {
          const pk = focal / Math.max(s.z + velocity, 1);
          const px = cx + s.x * pk;
          const py = cy + s.y * pk;
          if (Math.abs(px - x) + Math.abs(py - y) > 2) {
            const p = PALETTE[s.hue]!;
            ctx.strokeStyle = `rgba(${p[0]},${p[1]},${p[2]},${alpha * 0.35})`;
            ctx.lineWidth = r * 1.1;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(x, y);
            ctx.stroke();
          }
        }

        const d = r * 6; // halo do sprite
        ctx.globalAlpha = alpha;
        ctx.drawImage(sprites[s.hue]!, x - d / 2, y - d / 2, d, d);
      }
      ctx.globalAlpha = 1;

      // estrelas cadentes ocasionais (desktop e mobile não-fraco)
      if (!reduced && !lowEnd) {
        nextShoot -= dt;
        if (nextShoot <= 0) {
          nextShoot = 5000 + Math.random() * 9000;
          const sx = Math.random() * width * 0.8;
          const sy = Math.random() * height * 0.5;
          const ang = Math.PI * (0.12 + Math.random() * 0.16);
          shooting.push({
            x: sx,
            y: sy,
            vx: Math.cos(ang) * 0.9,
            vy: Math.sin(ang) * 0.9,
            life: 1,
            len: 140 + Math.random() * 160,
          });
        }
        for (let i = shooting.length - 1; i >= 0; i--) {
          const sh = shooting[i]!;
          sh.x += sh.vx * dt;
          sh.y += sh.vy * dt;
          sh.life -= dt / 1100;
          if (sh.life <= 0) {
            shooting.splice(i, 1);
            continue;
          }
          const g = ctx.createLinearGradient(
            sh.x,
            sh.y,
            sh.x - sh.vx * sh.len,
            sh.y - sh.vy * sh.len,
          );
          g.addColorStop(0, `rgba(255,246,225,${0.75 * sh.life})`);
          g.addColorStop(1, "rgba(255,246,225,0)");
          ctx.strokeStyle = g;
          ctx.lineWidth = 1.6;
          ctx.lineCap = "round";
          ctx.beginPath();
          ctx.moveTo(sh.x, sh.y);
          ctx.lineTo(sh.x - sh.vx * sh.len, sh.y - sh.vy * sh.len);
          ctx.stroke();
        }
      }

      ctx.globalCompositeOperation = "source-over";

      if (AMBIENT === 0 && velocity === 0 && shooting.length === 0) {
        running = false;
        raf = 0;
        return;
      }
      raf = requestAnimationFrame(render);
    };

    const start = () => {
      if (running || !visible || count === 0) return;
      running = true;
      t = performance.now();
      raf = requestAnimationFrame(render);
    };

    const onScroll = () => {
      const y = window.scrollY;
      const delta = y - lastScrollY;
      lastScrollY = y;
      const nextVisible = y < window.innerHeight * 3.6;
      if (nextVisible !== visible) {
        visible = nextVisible;
        canvas.style.display = visible ? "block" : "none";
        if (!visible) {
          velocity = 0;
          if (raf) cancelAnimationFrame(raf);
          raf = 0;
          running = false;
          ctx.clearRect(0, 0, width, height);
          return;
        }
      }
      if (!visible) return;
      velocity += delta * (reduced ? 0 : isMobile ? 0.55 : 0.85);
      velocity = Math.max(-70, Math.min(70, velocity));
      start();
    };

    let resizeTimer = 0;
    const onResize = () => {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(() => {
        resize();
        start();
      }, 150);
    };

    const onVisibility = () => {
      if (document.hidden) {
        if (raf) cancelAnimationFrame(raf);
        raf = 0;
        running = false;
      } else start();
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    document.addEventListener("visibilitychange", onVisibility);
    start();

    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", onVisibility);
      window.clearTimeout(resizeTimer);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-[1] h-full w-full"
      style={{ opacity, transition: "opacity 0.2s linear", contain: "strict" }}
    />
  );
}
