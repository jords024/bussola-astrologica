import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import retrato from "../../assets/crassus-retrato.png.asset.json";

const PARAGRAFOS = [
  "Minha mãe é astróloga há quase 50 anos, então eu cresci ouvindo esses nomes na mesa de jantar do mesmo jeito que outras famílias falam de futebol. E olha só a ironia: eu passei metade da vida fugindo disso…",
  "Fui empresário. Tive vários negócios. Ganhei dinheiro. Por um certo tempo me parecia o verdadeiro sucesso: jovem, bem-sucedido, aquela história toda de “sonho americano da Shopee”…",
  "Acontece que eu chegava na minha própria empresa contando as horas pra ir embora. Começava a segunda-feira torcendo pra sexta chegar logo — e não era pra descansar. Era pra parar de fazer o que eu tava fazendo…",
];

export default function BlocoHistoriaCrassus() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const glowRef = useRef<HTMLDivElement | null>(null);
  const fotoRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    gsap.registerPlugin(ScrollTrigger);
    const isMobile = window.matchMedia("(max-width: 767px)").matches;

    let ctx: gsap.Context | undefined;
    const timer = setTimeout(() => {
      ctx = gsap.context(() => {
        gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el) => {
          gsap.from(el, {
            opacity: 0,
            y: 26,
            duration: 0.9,
            ease: "power3.out",
            scrollTrigger: { trigger: el, start: "top 88%", once: true },
          });
        });

        gsap.fromTo(
          fotoRef.current,
          { yPercent: isMobile ? -3 : -7 },
          {
            yPercent: isMobile ? 3 : 7,
            ease: "none",
            scrollTrigger: { trigger: section, start: "top bottom", end: "bottom top", scrub: 0.6 },
          },
        );

        gsap.fromTo(
          glowRef.current,
          { opacity: 0.25, yPercent: -8 },
          {
            opacity: 0.6,
            yPercent: 8,
            ease: "none",
            scrollTrigger: { trigger: section, start: "top bottom", end: "bottom top", scrub: 0.6 },
          },
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
      aria-label="Quem é Crassus Gobbi"
      className="relative isolate w-full overflow-hidden bg-background py-16 md:py-24"
    >
      <div
        ref={glowRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 will-change-transform"
        style={{
          background:
            "radial-gradient(42% 34% at 22% 24%, color-mix(in oklab, var(--gold) 14%, transparent) 0%, transparent 70%)",
        }}
      />

      <div className="relative mx-auto max-w-5xl px-6">
        {/* Apresentação + retrato */}
        <div className="grid items-center gap-9 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] md:gap-12">
          <div data-reveal className="relative mx-auto w-full max-w-[320px] md:max-w-none">
            <div
              aria-hidden
              className="pointer-events-none absolute -inset-3 rounded-[26px]"
              style={{
                background:
                  "radial-gradient(60% 60% at 50% 40%, color-mix(in oklab, var(--gold) 22%, transparent) 0%, transparent 75%)",
              }}
            />
            <div
              ref={fotoRef}
              className="relative overflow-hidden rounded-[22px] border border-gold/25 will-change-transform"
            >
              <img
                src={retrato.url}
                alt="Crassus Gobbi, astrólogo, com as mãos apoiadas sob o queixo"
                loading="eager"
                decoding="async"
                width={560}
                height={560}
                className="block h-full w-full object-cover"
              />
              <div
                aria-hidden
                className="pointer-events-none absolute inset-0"
                style={{
                  background:
                    "linear-gradient(180deg, transparent 45%, color-mix(in oklab, var(--background) 78%, transparent) 100%)",
                }}
              />
            </div>
          </div>

          <div>
            <p
              data-reveal
              className="font-body text-[11px] font-medium uppercase tracking-[0.34em] text-gold"
            >
              Quem vai te guiar
            </p>
            <h2
              data-reveal
              className="mt-4 font-display text-[2.4rem] leading-[1.05] text-foreground sm:text-5xl"
            >
              Meu nome é <em className="italic text-gold">Crassus Gobbi</em>.
            </h2>
            <div aria-hidden data-reveal className="mt-6 h-px w-24 bg-gradient-to-r from-gold/70 to-transparent" />
            {PARAGRAFOS.map((p) => (
              <p
                key={p.slice(0, 24)}
                data-reveal
                className="mt-5 text-[15.5px] leading-[1.85] text-muted-foreground md:text-base"
              >
                {p}
              </p>
            ))}
          </div>
        </div>

        {/* O espelho */}
        <div className="mt-14 md:mt-20">
          <div
            data-reveal
            className="relative mx-auto max-w-3xl rounded-[24px] border border-gold/20 p-7 md:p-10"
            style={{
              background:
                "linear-gradient(168deg, color-mix(in oklab, var(--gold) 5%, var(--background)) 0%, var(--background) 72%)",
            }}
          >
            <p className="text-[15.5px] leading-[1.85] text-muted-foreground md:text-base">
              Um dia eu tava me arrumando pra mais um desses dias. Verão em Porto Alegre, uns quarenta
              graus lá fora, e eu de blazer, camisa, calça e sapato.
            </p>
            <blockquote className="mt-7 border-l border-gold/40 pl-5 md:pl-7">
              <p className="font-display text-[1.6rem] leading-[1.35] text-foreground md:text-[2.1rem]">
                Me olhei no espelho e pensei:{" "}
                <em className="italic text-gold">o que é que eu tô fazendo comigo?</em>
              </p>
            </blockquote>
          </div>
        </div>

        {/* A culpa */}
        <div className="mt-12 md:mt-16">
          <p
            data-reveal
            className="mx-auto max-w-3xl text-[15.5px] leading-[1.85] text-muted-foreground md:text-base"
          >
            Eu tinha todas as condições do mundo pra dar certo. Mas parecia que eu tava empurrando
            uma parede há dez anos. Foi aí que eu parei de fugir e fui entender o que a astrologia
            tinha pra me dizer sobre o momento que eu tava vivendo.
          </p>
        </div>
      </div>
    </section>
  );
}
