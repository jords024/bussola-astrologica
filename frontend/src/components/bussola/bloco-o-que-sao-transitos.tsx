import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { KeyRound, DoorOpen } from "lucide-react";

export default function BlocoOQueSaoTransitos() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const glowRef = useRef<HTMLDivElement | null>(null);
  const keyRef = useRef<SVGCircleElement | null>(null);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    gsap.registerPlugin(ScrollTrigger);
    const isMobile = window.matchMedia("(max-width: 767px)").matches;

    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el, i) => {
        gsap.from(el, {
          opacity: 0,
          y: 28,
          duration: 0.9,
          delay: (i % 3) * 0.05,
          ease: "power3.out",
          scrollTrigger: { trigger: el, start: "top 88%", once: true },
        });
      });

      gsap.fromTo(
        glowRef.current,
        { yPercent: isMobile ? -6 : -14, opacity: 0.25 },
        {
          yPercent: isMobile ? 6 : 14,
          opacity: 0.6,
          ease: "none",
          scrollTrigger: { trigger: section, start: "top bottom", end: "bottom top", scrub: 0.6 },
        },
      );

      // O "planeta" (ponto dourado) percorre a roda continuamente —
      // ilustra literalmente o que é um trânsito: um movimento no tempo.
      gsap.to(keyRef.current, {
        duration: 8,
        repeat: -1,
        ease: "none",
        onUpdate: function (this: gsap.core.Tween) {
          const t = this.progress();
          const angle = t * Math.PI * 2 - Math.PI / 2;
          const r = 72;
          const x = 100 + Math.cos(angle) * r;
          const y = 100 + Math.sin(angle) * r;
          keyRef.current?.setAttribute("cx", String(x));
          keyRef.current?.setAttribute("cy", String(y));
        },
      });
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      aria-label="O que são os trânsitos"
      className="relative isolate w-full overflow-hidden bg-background py-14 md:py-24"
    >
      <div
        ref={glowRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 will-change-transform"
        style={{
          background:
            "radial-gradient(48% 40% at 50% 35%, color-mix(in oklab, var(--gold) 14%, transparent) 0%, transparent 72%)",
        }}
      />

      <div className="relative mx-auto grid w-full max-w-4xl gap-10 px-6 md:grid-cols-[1fr_1fr] md:items-center md:gap-14 md:px-10">
        {/* Diagrama: roda fixa (mapa) + ponto dourado em órbita (trânsito) */}
        <div data-reveal className="mx-auto grid place-items-center">
          <svg viewBox="0 0 200 200" className="h-[240px] w-[240px] md:h-[300px] md:w-[300px]" aria-hidden>
            {/* Casas fixas do mapa — não se movem */}
            <circle cx="100" cy="100" r="72" fill="none" stroke="color-mix(in oklab, var(--gold) 24%, transparent)" strokeWidth="0.75" />
            {Array.from({ length: 12 }).map((_, i) => {
              const a = ((i * 30 - 90) * Math.PI) / 180;
              const x1 = 100 + Math.cos(a) * 58;
              const y1 = 100 + Math.sin(a) * 58;
              const x2 = 100 + Math.cos(a) * 72;
              const y2 = 100 + Math.sin(a) * 72;
              return (
                <line
                  key={i}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="color-mix(in oklab, var(--gold) 30%, transparent)"
                  strokeWidth="0.75"
                />
              );
            })}
            <circle cx="100" cy="100" r="58" fill="none" stroke="color-mix(in oklab, var(--gold) 16%, transparent)" strokeWidth="0.5" strokeDasharray="1 4" />

            {/* Ponto dourado em órbita — o "trânsito": o único elemento que se move */}
            <circle
              ref={keyRef}
              cx="172"
              cy="100"
              r="4.5"
              fill="var(--gold)"
              style={{ filter: "drop-shadow(0 0 6px color-mix(in oklab, var(--gold) 70%, transparent))" }}
            />

            <circle cx="100" cy="100" r="3" fill="color-mix(in oklab, var(--gold) 55%, transparent)" />
          </svg>
          <p className="mt-2 text-center text-[10px] uppercase tracking-[0.3em] text-gold/55">
            O mapa fica parado. O céu, não.
          </p>
        </div>

        {/* Texto */}
        <div>
          <p data-reveal className="font-body text-[11px] font-medium uppercase tracking-[0.34em] text-gold">
            Antes de continuar
          </p>
          <h2 data-reveal className="mt-4 font-display text-[2rem] leading-[1.12] text-foreground sm:text-4xl">
            O que são os <em className="italic text-gold">trânsitos</em>
          </h2>

          <p data-reveal className="mt-6 text-base leading-relaxed text-muted-foreground sm:text-lg">
            Seu mapa é uma foto do céu no dia em que você nasceu. Isso nunca muda.
          </p>
          <p data-reveal className="mt-4 text-base leading-relaxed text-muted-foreground sm:text-lg">
            Só que o céu não para. <strong className="font-semibold text-foreground">Trânsito</strong> é
            onde os planetas estão <em className="not-italic text-gold">hoje</em>, comparado a onde
            eles estavam no dia em que você nasceu.
          </p>

          <div data-reveal className="my-7 flex items-center gap-3 rounded-2xl border border-gold/20 bg-gold/[0.04] px-5 py-4">
            <KeyRound className="h-5 w-5 shrink-0 text-gold" />
            <span className="text-sm leading-relaxed text-foreground/85">
              O trânsito é a <span className="font-semibold text-gold">chave</span>.
            </span>
          </div>
          <div data-reveal className="mb-7 flex items-center gap-3 rounded-2xl border border-gold/20 bg-gold/[0.04] px-5 py-4">
            <DoorOpen className="h-5 w-5 shrink-0 text-gold" />
            <span className="text-sm leading-relaxed text-foreground/85">
              A casa do seu mapa é a <span className="font-semibold text-gold">porta</span>.
            </span>
          </div>

          <p data-reveal className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            Quando um planeta toca uma dessas casas, essa área da sua vida{" "}
            <span className="font-semibold text-gold">acorda</span>. A porta se abre. A Bússola
            traduz isso pra você em 3 minutos, sem decorar nada.
          </p>
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 top-0 h-10 bg-gradient-to-b from-background to-transparent md:h-16" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-background to-transparent md:h-16" />
    </section>
  );
}
