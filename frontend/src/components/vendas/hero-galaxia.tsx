import { ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import GalaxyScroll from "../ui/galaxy-scroll";

const titles: Record<number, string> = {
  0: "ASTROWAKE",
  1: "LABIRINTO",
  2: "O RUMO",
};

const subtitles: Record<number, { line1: string; line2: string }> = {
  0: { line1: "O despertar de um conhecimento ancestral....", line2: "" },
  1: {
    line1: "Você passou anos se anulando para agradar todo mundo,",
    line2: "tentando tomar decisões no escuro",
  },
  2: {
    line1: "Chega de dar murro em ponta de faca,",
    line2: "o seu mapa guarda a resposta que você procura",
  },
};

const TOTAL_SECTIONS = 2;
const clamp01 = (v: number) => (v < 0 ? 0 : v > 1 ? 1 : v);

export default function HeroGalaxia() {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const nebulaRef = useRef<HTMLDivElement | null>(null);
  const auraRef = useRef<HTMLDivElement | null>(null);

  const [currentSection, setCurrentSection] = useState(0);
  const [outro, setOutro] = useState(0);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let ticking = false;

    const update = () => {
      ticking = false;
      const total = root.offsetHeight - window.innerHeight;
      const p = clamp01(total > 0 ? -root.getBoundingClientRect().top / total : 0);

      if (!reduced) {
        if (nebulaRef.current) {
          nebulaRef.current.style.transform = `translate3d(0, ${-p * 14}vh, 0) scale(${1 + p * 0.22})`;
          nebulaRef.current.style.opacity = String(0.55 + p * 0.35);
        }
        if (auraRef.current) {
          auraRef.current.style.transform = `translate3d(-50%, ${(0.5 - p) * 10}vh, 0) scale(${0.9 + p * 0.35})`;
          auraRef.current.style.opacity = String(0.35 + p * 0.5);
        }
      }

      const section = Math.min(TOTAL_SECTIONS, Math.round(p * TOTAL_SECTIONS));
      setCurrentSection((prev) => (prev === section ? prev : section));

      const fadeStart = 0.86;
      setOutro(clamp01((p - fadeStart) / (1 - fadeStart)));
    };

    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  const subtitle = subtitles[currentSection] ?? subtitles[0]!;
  const sceneOpacity = 1 - outro;

  return (
    <div ref={rootRef} className="relative w-full bg-background">
      {/* Céu profundo + nebulosa */}
      <div
        className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-[#000]"
        style={{ opacity: sceneOpacity }}
        aria-hidden
      >
        <div
          ref={nebulaRef}
          className="absolute inset-[-15%] will-change-transform"
          style={{
            background: [
              "radial-gradient(45% 32% at 22% 26%, color-mix(in oklab, var(--gold-deep) 26%, transparent) 0%, transparent 70%)",
              "radial-gradient(50% 38% at 78% 68%, rgba(60,86,160,0.22) 0%, transparent 72%)",
              "radial-gradient(70% 55% at 50% 105%, color-mix(in oklab, var(--gold) 12%, transparent) 0%, transparent 70%)",
            ].join(","),
            filter: "blur(2px)",
          }}
        />
        {/* Aura central dourada */}
        <div
          ref={auraRef}
          className="absolute left-1/2 top-1/2 h-[70vh] w-[70vh] -translate-x-1/2 -translate-y-1/2 rounded-full will-change-transform"
          style={{
            background:
              "radial-gradient(closest-side, color-mix(in oklab, var(--gold) 26%, transparent) 0%, color-mix(in oklab, var(--gold-deep) 12%, transparent) 45%, transparent 72%)",
          }}
        />
        {/* Vinheta para legibilidade */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(58% 42% at 50% 50%, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.5) 55%, rgba(0,0,0,0.86) 100%)",
          }}
        />
      </div>

      {/* Campo estelar */}
      <GalaxyScroll opacity={sceneOpacity} />

      {/* Marca lateral */}
      <div className="pointer-events-none fixed left-5 top-1/2 z-10 hidden -translate-y-1/2 md:block">
        <p
          className="text-xs font-bold uppercase tracking-[0.5em] text-gold/80"
          style={{ writingMode: "vertical-rl" }}
        >
          Astrowake
        </p>
      </div>

      {/* Conteúdo */}
      <div
        className="pointer-events-none fixed inset-0 z-10 flex flex-col items-center justify-center px-6 pb-36 text-center sm:pb-28"
        style={{ opacity: sceneOpacity, transform: `translateY(${-outro * 60}px)` }}
      >
        <h1
          key={`title-${currentSection}`}
          className="relative max-w-[92vw] animate-fade-in font-display text-[2.75rem] font-black leading-none tracking-tighter text-foreground drop-shadow-[0_10px_45px_rgba(214,164,68,0.45)] sm:text-7xl md:text-8xl lg:text-9xl"
        >
          {titles[currentSection] ?? titles[0]}
        </h1>

        <div
          key={`sub-${currentSection}`}
          className="relative mt-5 max-w-[34rem] animate-fade-in space-y-2 sm:mt-6"
        >
          <p className="text-[0.95rem] font-medium leading-snug tracking-tight text-foreground drop-shadow-[0_4px_18px_rgba(0,0,0,0.9)] sm:text-xl">
            {subtitle.line1}
          </p>
          {subtitle.line2 ? (
            <p className="text-[0.85rem] font-normal leading-snug tracking-tight text-gold-soft drop-shadow-[0_4px_22px_rgba(0,0,0,0.8)] sm:text-lg">
              {subtitle.line2}
            </p>
          ) : null}
        </div>
      </div>

      {/* Indicador de scroll */}
      <div
        className="pointer-events-none fixed bottom-[max(1.5rem,env(safe-area-inset-bottom))] left-1/2 z-20 flex -translate-x-1/2 flex-col items-center gap-3"
        style={{ opacity: sceneOpacity }}
      >
        <span className="max-w-[80vw] text-center text-[0.7rem] font-semibold uppercase leading-relaxed tracking-[0.22em] text-foreground/85 drop-shadow-[0_2px_12px_rgba(0,0,0,0.9)] sm:text-xs sm:tracking-[0.3em]">
          {currentSection === 0
            ? "Desça para acessar as instruções da sua alma"
            : currentSection < TOTAL_SECTIONS
              ? "Continue descendo"
              : "Você chegou — siga para o próximo passo"}
        </span>

        <ChevronDown className="h-5 w-5 animate-bounce text-gold drop-shadow-[0_2px_14px_rgba(214,164,68,0.6)]" />

        <div className="hidden items-center gap-2 md:flex">
          {Array.from({ length: TOTAL_SECTIONS + 1 }).map((_, i) => (
            <span
              key={i}
              className={`h-1.5 rounded-full transition-all duration-500 ${
                i === currentSection ? "w-7 bg-gold" : "w-1.5 bg-foreground/25"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Alturas de scroll */}
      <div className="relative z-[5]">
        {Array.from({ length: TOTAL_SECTIONS + 1 }).map((_, i) => (
          <section key={i} className="h-[100svh] w-full" />
        ))}
      </div>
    </div>
  );
}
