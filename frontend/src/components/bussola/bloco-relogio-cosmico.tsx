import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export default function BlocoRelogioCosmico() {
  const sectionRef = useRef<HTMLElement | null>(null);
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
          { yPercent: isMobile ? -6 : -14, opacity: 0.3 },
          {
            yPercent: isMobile ? 6 : 14,
            opacity: 0.7,
            ease: "none",
            scrollTrigger: {
              trigger: section,
              start: "top bottom",
              end: "bottom top",
              scrub: 0.6,
            },
          },
        );

        gsap.to("[data-star]", {
          rotate: 360,
          duration: 40,
          repeat: -1,
          ease: "none",
          transformOrigin: "50% 50%",
        });
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
      aria-label="E o que você faz?"
      className="relative isolate -mt-4 w-full overflow-hidden bg-background py-12 md:py-20"
    >
      <div
        ref={glowRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 will-change-transform"
        style={{
          background:
            "radial-gradient(45% 38% at 50% 40%, color-mix(in oklab, var(--gold) 16%, transparent) 0%, transparent 72%)",
        }}
      />

      <div className="relative mx-auto w-full max-w-2xl px-5 text-center sm:px-6">
        <h2
          data-reveal
          className="font-body text-xs font-semibold uppercase tracking-[0.35em] text-gold sm:text-sm"
        >
          E o que você faz?
        </h2>

        <p data-reveal className="mt-8 text-lg leading-relaxed text-foreground/85 sm:text-xl">
          Chama a primeira semana de{" "}
          <span className="font-semibold text-gold">sorte e super produtiva.</span>
        </p>

        <p data-reveal className="mt-5 text-lg leading-relaxed text-foreground/85 sm:text-xl">
          E a segunda de{" "}
          <span className="font-semibold text-muted-foreground">
            preguiça, falta de disciplina ou desmotivação.
          </span>
        </p>

        <div
          data-reveal
          aria-hidden
          className="mx-auto my-10 flex items-center justify-center gap-3"
        >
          <span className="h-px w-20 bg-gradient-to-r from-transparent to-gold/50" />
          <span className="h-1 w-1 rotate-45 bg-gold/70" />
          <span className="h-px w-20 bg-gradient-to-l from-transparent to-gold/50" />
        </div>

        <p data-reveal className="text-lg leading-relaxed text-foreground/85 sm:text-xl">
          Só que existe uma <span className="font-semibold text-gold">terceira possibilidade</span>{" "}
          que quase ninguém considera:
        </p>

        <div data-reveal aria-hidden className="my-10 flex justify-center">
          <svg
            data-star
            width="46"
            height="46"
            viewBox="0 0 100 100"
            className="text-gold drop-shadow-[0_0_18px_color-mix(in_oklab,var(--gold)_55%,transparent)]"
          >
            <path d="M50 2 L57 43 L98 50 L57 57 L50 98 L43 57 L2 50 L43 43 Z" fill="currentColor" />
          </svg>
        </div>

        <p
          data-reveal
          className="font-display text-3xl leading-snug text-foreground sm:text-4xl md:text-[2.75rem]"
        >
          Você vive em constante movimento. A vida acontece em ciclos através de um{" "}
          <span className="text-gold-gradient">“Relógio cósmico”</span> só seu, por isso, você nunca
          vive exatamente o mesmo momento duas vezes…
        </p>

        <p data-reveal className="mt-10 text-base leading-relaxed text-foreground/75 sm:text-lg">
          E quando você não entende isso, pode passar anos tentando{" "}
          <span className="font-semibold text-gold">
            forçar portas que naquele momento não estavam abertas!
          </span>
        </p>
      </div>

      <div className="pointer-events-none absolute inset-x-0 top-0 h-10 bg-gradient-to-b from-background to-transparent md:h-16" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-background to-transparent md:h-16" />
    </section>
  );
}
