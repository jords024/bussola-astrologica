import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import semanaAsset from "../../assets/bussola-semana-seguinte.png.asset.json";

export default function BlocoSemanaSeguinte() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const imageRef = useRef<HTMLDivElement | null>(null);
  const glowRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    gsap.registerPlugin(ScrollTrigger);
    const isMobile = window.matchMedia("(max-width: 767px)").matches;

    const ctx = gsap.context(() => {
      gsap.timeline({
        scrollTrigger: { trigger: section, start: "top bottom", end: "bottom top", scrub: 0.6 },
      })
        .fromTo(
          imageRef.current,
          { yPercent: isMobile ? 4 : 8, scale: 1.04 },
          { yPercent: isMobile ? -4 : -8, scale: 1, ease: "none" },
          0,
        )
        .fromTo(
          glowRef.current,
          { yPercent: isMobile ? -6 : -12, opacity: 0.25 },
          { yPercent: isMobile ? 6 : 12, opacity: 0.6, ease: "none" },
          0,
        );

      gsap.from(imageRef.current, {
        opacity: 0,
        y: 40,
        duration: 1,
        ease: "power3.out",
        scrollTrigger: { trigger: section, start: "top 80%", once: true },
      });
    }, section);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      aria-label="Aí chega a semana seguinte e nada anda"
      className="relative isolate -mt-2 w-full overflow-hidden bg-background py-2 md:py-4"
    >
      {/* Brilho sutil ao fundo — tom frio/azulado contido na paleta dourada */}
      <div
        ref={glowRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 will-change-transform"
        style={{
          background:
            "radial-gradient(50% 40% at 50% 45%, color-mix(in oklab, var(--gold) 14%, transparent) 0%, transparent 70%)",
        }}
      />

      <div className="relative w-screen max-w-none px-0 md:mx-auto md:w-full md:max-w-4xl md:px-6 lg:max-w-5xl">
        <div ref={imageRef} className="relative will-change-transform">
          <img
            src={semanaAsset.url}
            alt="Aí chega a semana seguinte e nada anda: as mesmas tarefas, a mesma rotina, e a sensação de que nada flui."
            className="h-auto w-full min-w-full max-w-none"
            loading="lazy"
            decoding="async"
            sizes="100vw"
            style={{
              maskImage:
                "radial-gradient(120% 115% at 50% 50%, #000 35%, transparent 78%)",
              WebkitMaskImage:
                "radial-gradient(120% 115% at 50% 50%, #000 35%, transparent 78%)",
            }}
          />
        </div>
      </div>

      {/* Véus suaves para derreter a imagem no fundo preto e esconder a transição entre blocos */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-background to-transparent md:h-12" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-background to-transparent md:h-12" />
    </section>
  );
}
