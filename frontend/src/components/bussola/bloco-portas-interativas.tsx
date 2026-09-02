import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Sparkles, X } from "lucide-react";
import { HOUSES, type House } from "./bloco-12-casas";

// Placa de cada porta — precisa de concordância manual (do/da/dos/de).
const PLACAS: Record<number, string> = {
  1: "A porta de Você",
  2: "A porta do Dinheiro",
  3: "A porta da Comunicação",
  4: "A porta da Casa e Família",
  5: "A porta do Amor e Criação",
  6: "A porta da Rotina e Corpo",
  7: "A porta dos Relacionamentos",
  8: "A porta da Transformação",
  9: "A porta da Expansão",
  10: "A porta da Carreira",
  11: "A porta do Futuro e Conexões",
  12: "A porta do Recolhimento",
};

const OPEN_EASE = [0.16, 1, 0.3, 1] as const;
const CLOSE_EASE = [0.7, 0, 0.84, 0] as const;

// HOUSES vem de um arquivo compartilhado com a página publicada e tem
// travessões no texto. Neutraliza só na exibição aqui, sem tocar no arquivo
// original (usado também em /bussola).
const semTraco = (t: string) => t.replace(/\s*—\s*/g, ", ");

function PortaCard({ house, live }: { house: House; live: boolean }) {
  const [open, setOpen] = useState(false);
  const placa = PLACAS[house.n] ?? `A porta de ${house.name}`;

  return (
    <div
      className="relative flex h-[380px] w-[264px] flex-none snap-center transition-[opacity,transform] duration-500"
      style={{
        perspective: 1400,
        opacity: live ? 1 : 0.55,
        transform: live ? "scale(1)" : "scale(.95)",
      }}
    >
      {/* Conteúdo por trás da porta — revelado com um leve atraso em relação
          ao giro, pra dar a sensação de luz entrando antes do conteúdo. */}
      <div
        className="absolute inset-0 flex flex-col overflow-y-auto rounded-[22px] border border-gold/25 p-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        style={{
          background:
            "linear-gradient(168deg, color-mix(in oklab, var(--gold) 8%, var(--background)) 0%, var(--background) 100%)",
        }}
      >
        {/* Feixe de luz que varre a porta ao abrir */}
        <AnimatePresence>
          {open && (
            <motion.div
              aria-hidden
              initial={{ opacity: 0, x: "-100%" }}
              animate={{ opacity: [0, 0.5, 0], x: "120%" }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.9, ease: "easeOut" }}
              className="pointer-events-none absolute inset-y-0 left-0 w-1/3"
              style={{
                background:
                  "linear-gradient(90deg, transparent, color-mix(in oklab, var(--gold) 45%, transparent), transparent)",
              }}
            />
          )}
        </AnimatePresence>

        <motion.div
          initial={false}
          animate={{ opacity: open ? 1 : 0, y: open ? 0 : 8 }}
          transition={{ duration: 0.5, delay: open ? 0.28 : 0, ease: OPEN_EASE }}
          className="flex h-full flex-col"
        >
          <div className="mb-4 flex items-center gap-2.5">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-gold/30 bg-gold/10 text-gold">
              <house.Icon className="h-[18px] w-[18px]" />
            </span>
            <div>
              <p className="text-[9.5px] uppercase tracking-[0.28em] text-gold/60">
                Casa {house.n}
              </p>
              <h3 className="font-display text-lg leading-tight text-foreground">{house.name}</h3>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label={`Fechar ${placa}`}
              tabIndex={open ? 0 : -1}
              className="ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-full border border-gold/25 text-gold/70 transition-colors hover:border-gold/50 hover:text-gold"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <p className="font-display text-[1.05rem] leading-[1.4] text-gold-soft">{semTraco(house.teaser)}</p>
          <p className="mt-3 flex-1 text-[13px] leading-relaxed text-muted-foreground">
            {semTraco(house.body)}
          </p>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {house.tags.slice(0, 4).map((t) => (
              <span
                key={t}
                className="rounded-full border border-gold/20 px-2.5 py-1 text-[10px] text-gold/80"
              >
                {t}
              </span>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Porta — gira sobre a dobradiça esquerda ao tocar. Só abre por aqui;
          fecha pelo X dentro do conteúdo (a porta girada fica com área de
          clique quase nula na tela, não dá pra confiar nela pra fechar). */}
      <motion.button
        type="button"
        onClick={() => setOpen(true)}
        aria-expanded={open}
        aria-label={`Abrir ${placa}`}
        tabIndex={open ? -1 : 0}
        initial={false}
        animate={{
          rotateY: open ? -112 : 0,
          boxShadow: open
            ? "0 6px 20px -10px rgba(0,0,0,0.4)"
            : "0 20px 60px -24px rgba(0,0,0,0.6)",
        }}
        transition={{ duration: open ? 0.9 : 0.55, ease: open ? OPEN_EASE : CLOSE_EASE }}
        className="absolute inset-0 flex flex-col items-center justify-between rounded-[22px] border border-gold/35 px-5 py-6 text-center"
        style={{
          transformOrigin: "left center",
          transformStyle: "preserve-3d",
          backfaceVisibility: "hidden",
          background:
            "linear-gradient(155deg, color-mix(in oklab, var(--gold) 14%, var(--background)) 0%, var(--background) 55%, color-mix(in oklab, var(--gold) 10%, var(--background)) 100%)",
        }}
      >
        {/* Placa */}
        <div className="mt-2 rounded-lg border border-gold/40 bg-background/60 px-4 py-2.5">
          <p className="font-display text-[13px] leading-tight text-gold">{placa}</p>
        </div>

        {/* Miolo da porta: friso, ícone da área (personaliza cada porta) e
            maçaneta pulsante */}
        <div className="relative flex flex-1 w-full items-center justify-center">
          <div className="absolute inset-x-6 inset-y-2 rounded-md border border-gold/15" />
          <div className="absolute inset-x-10 inset-y-6 rounded-md border border-gold/10" />
          <house.Icon className="h-9 w-9 text-gold/25" strokeWidth={1.25} />
          <motion.span
            animate={{ opacity: [0.45, 1, 0.45] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
            className="absolute right-6 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-full bg-gold text-background"
          >
            <Lock className="h-3.5 w-3.5" />
          </motion.span>
        </div>

        {/* Convite */}
        <div className="mb-1 flex items-center gap-1.5 text-[10.5px] uppercase tracking-[0.2em] text-gold/75">
          <Sparkles className="h-3 w-3" />
          Toque para abrir a porta
        </div>
      </motion.button>
    </div>
  );
}

export default function BlocoPortasInterativas() {
  const railRef = useRef<HTMLDivElement | null>(null);
  const [live, setLive] = useState(0);

  const onScroll = useCallback(() => {
    const rail = railRef.current;
    if (!rail) return;
    const mid = rail.scrollLeft + rail.clientWidth / 2;
    let best = 0;
    let gap = Infinity;
    Array.from(rail.children).forEach((child, k) => {
      const c = child as HTMLElement;
      const g = Math.abs(c.offsetLeft + c.offsetWidth / 2 - mid);
      if (g < gap) {
        gap = g;
        best = k;
      }
    });
    setLive((prev) => (prev === best ? prev : best));
  }, []);

  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    let raf = 0;
    const handler = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(onScroll);
    };
    rail.addEventListener("scroll", handler, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      rail.removeEventListener("scroll", handler);
    };
  }, [onScroll]);

  return (
    <section
      aria-label="As 12 portas do seu mapa"
      className="relative isolate w-full overflow-hidden bg-background py-14 md:py-20"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(50% 40% at 50% 30%, color-mix(in oklab, var(--gold) 12%, transparent) 0%, transparent 70%)",
        }}
      />

      <header className="relative mx-auto max-w-xl px-6 text-center">
        <p className="font-body text-[11px] font-medium uppercase tracking-[0.34em] text-gold">
          Bússola Astrológica
        </p>
        <h2 className="mt-4 font-display text-[2.1rem] leading-[1.1] text-foreground sm:text-4xl">
          Suas <em className="italic text-gold">12 portas</em>
        </h2>
        <p className="mx-auto mt-5 max-w-[36ch] text-sm leading-relaxed text-muted-foreground">
          Toque, arraste, abra. Descubra quais das suas 12 portas estão pedindo passagem agora.
        </p>
      </header>

      <div
        ref={railRef}
        className="relative mt-9 flex snap-x snap-mandatory gap-5 overflow-x-auto px-7 pb-4 pt-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {HOUSES.map((h, i) => (
          <PortaCard key={h.n} house={h} live={i === live} />
        ))}
      </div>

      <div className="flex justify-center gap-1.5 pb-1 pt-3">
        {HOUSES.map((h, i) => (
          <span
            key={h.n}
            className="h-1 rounded-full transition-all duration-300"
            style={{
              width: i === live ? 16 : 4,
              background:
                i === live ? "var(--gold)" : "color-mix(in oklab, var(--gold) 28%, transparent)",
            }}
          />
        ))}
      </div>

      <p className="pt-3 text-center text-[10px] uppercase tracking-[0.26em] text-gold/60">
        Arraste para o lado
      </p>
    </section>
  );
}
