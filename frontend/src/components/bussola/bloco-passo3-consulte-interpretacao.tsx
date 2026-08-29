import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import passo3Asset from "../../assets/bussola-passo3-consulte-interpretacao.webp";

export default function BlocoPasso3ConsulteInterpretacao() {
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
      aria-label="Passo 3: Consulte a interpretação"
      className="relative isolate w-full overflow-hidden bg-background"
    >
      <div
        ref={glowRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 will-change-transform"
        style={{
          background:
            "radial-gradient(50% 40% at 50% 45%, color-mix(in oklab, var(--gold) 18%, transparent) 0%, transparent 72%)",
        }}
      />

      <div className="relative w-screen max-w-none px-0 md:mx-auto md:w-full md:max-w-lg md:px-6 lg:max-w-xl">
        <div ref={imageRef} className="relative w-full will-change-transform">
          <img
            src={passo3Asset}
            alt="Passo 3: Consulte a interpretação. A Bússola traduz o que você está vendo no mapa para a vida real. Print de aplicativo mostrando interpretação do trânsito: Casa 10, Carreira, área da sua vida em foco, Júpiter em Gêmeos sobre a Casa 10. O que está sendo movimentado: expansão, visibilidade e novas oportunidades na carreira. Onde vale colocar energia: mostrar seu trabalho, se posicionar, fazer networking. O que merece atenção: evitar prometer mais do que pode entregar. O que pode esperar: um período fértil para avançar na carreira. Informação cósmica. Direção prática. Clareza para decidir com confiança."
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
