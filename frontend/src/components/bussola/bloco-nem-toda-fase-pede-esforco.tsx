import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import faseAsset from "../../assets/bussola-nem-toda-fase-pede-esforco.webp";

export default function BlocoNemTodaFasePedeEsforco() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const imageRef = useRef<HTMLDivElement | null>(null);
  const glowRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    gsap.registerPlugin(ScrollTrigger);
    const isMobile = window.matchMedia("(max-width: 767px)").matches;

    let ctx: gsap.Context | undefined;
    const timer = setTimeout(() => {
      ctx = gsap.context(() => {
      gsap
        .timeline({
          scrollTrigger: { trigger: section, start: "top bottom", end: "bottom top", scrub: 0.6 },
        })
        .fromTo(
          imageRef.current,
          { yPercent: isMobile ? 3 : 7, scale: 1.03 },
          { yPercent: isMobile ? -3 : -7, scale: 1, ease: "none" },
          0,
        )
        .fromTo(
          glowRef.current,
          { yPercent: isMobile ? -6 : -12, opacity: 0.3 },
          { yPercent: isMobile ? 6 : 12, opacity: 0.65, ease: "none" },
          0,
        );

      }, section);
    }, 120);

    return () => {
      clearTimeout(timer);
      ctx?.revert();
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      aria-label="Nem toda fase da vida pede mais esforço"
      className="relative isolate w-full overflow-hidden bg-background"
    >
      <div
        ref={glowRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 will-change-transform"
        style={{
          background:
            "radial-gradient(50% 40% at 50% 55%, color-mix(in oklab, var(--gold) 14%, transparent) 0%, transparent 72%)",
        }}
      />

      <div className="relative w-screen max-w-none px-0 md:mx-auto md:w-full md:max-w-lg md:px-6 lg:max-w-xl">
        <div ref={imageRef} className="relative w-full will-change-transform">
          <img
            src={faseAsset}
            alt="Porque você já tem lista de tarefas suficiente. Já ouviu sobre disciplina. Já tentou insistir. Já tentou acordar mais cedo, produzir mais, fazer mais, correr atrás de mais. O que quase ninguém te ensina é que nem toda fase da vida pede mais esforço. Às vezes, o que você precisava não era insistir mais. Era perceber que aquela porta não estava pedindo para ser aberta naquele momento. Uma mulher sentada no chão encostada numa porta escura, olhando para um corredor com um caminho de luz roxa que leva a uma porta aberta ao entardecer."
            className="h-auto w-full min-w-full max-w-none"
            loading="lazy"
            decoding="async"
            sizes="100vw"
            style={{
              maskImage: "radial-gradient(118% 112% at 50% 50%, #000 82%, transparent 97%)",
              WebkitMaskImage: "radial-gradient(118% 112% at 50% 50%, #000 82%, transparent 97%)",
            }}
          />
        </div>
      </div>

      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-8 md:h-10"
        style={{
          backdropFilter: "blur(6px)",
          WebkitBackdropFilter: "blur(6px)",
          maskImage: "linear-gradient(to bottom, black, transparent)",
          WebkitMaskImage: "linear-gradient(to bottom, black, transparent)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-8 md:h-10"
        style={{
          backdropFilter: "blur(6px)",
          WebkitBackdropFilter: "blur(6px)",
          maskImage: "linear-gradient(to top, black, transparent)",
          WebkitMaskImage: "linear-gradient(to top, black, transparent)",
        }}
      />
    </section>
  );
}
