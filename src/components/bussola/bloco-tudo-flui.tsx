import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import fluiAsset from "../../assets/bussola-tudo-flui.png.asset.json";
import fluiMobileAsset from "../../assets/bussola-tudo-flui-mobile.png.asset.json";

export default function BlocoTudoFlui() {
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
          { yPercent: isMobile ? 6 : 12, scale: 1.06 },
          { yPercent: isMobile ? -6 : -12, scale: 1, ease: "none" },
          0,
        )
        .fromTo(
          glowRef.current,
          { yPercent: isMobile ? -8 : -18, opacity: 0.35 },
          { yPercent: isMobile ? 8 : 18, opacity: 0.75, ease: "none" },
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
      aria-label="Tem semana que tudo flui"
      className="relative isolate w-full overflow-hidden bg-background py-14 md:py-24"
    >
      {/* Halo dourado ao fundo */}
      <div
        ref={glowRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 will-change-transform"
        style={{
          background:
            "radial-gradient(55% 45% at 50% 45%, color-mix(in oklab, var(--gold) 22%, transparent) 0%, transparent 70%)",
        }}
      />

      <div className="relative w-screen max-w-none px-0 sm:mx-auto sm:w-full sm:max-w-6xl sm:px-6">
        <div ref={imageRef} className="relative will-change-transform">
          <picture>
            <source media="(max-width: 767px)" srcSet={fluiMobileAsset.url} />
            <img
              src={fluiAsset.url}
              alt="Tem semana que tudo flui: você resolve tudo antes das 10h, responde todo mundo, destrava aquele negócio parado há meses e ainda sobra disposição para sair à noite"
              className="h-auto w-full min-w-full max-w-none sm:rounded-2xl"
              loading="lazy"
              decoding="async"
              sizes="100vw"
              style={{
                maskImage:
                  "radial-gradient(115% 110% at 50% 50%, #000 40%, transparent 82%)",
                WebkitMaskImage:
                  "radial-gradient(115% 110% at 50% 50%, #000 40%, transparent 82%)",
              }}
            />
          </picture>
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-background to-transparent md:h-24" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-background to-transparent md:h-24" />
    </section>
  );
}
