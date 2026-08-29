import { motion } from "framer-motion";
import { ArrowRight, Sparkles, ShieldCheck, Zap, Tag } from "lucide-react";
import heroAsset from "../../assets/bussola-hero.png.asset.json";
import heroMobileAsset from "../../assets/bussola-hero-mobile.png.asset.json";

const EASE = [0.16, 1, 0.3, 1] as const;

type Props = {
  onCtaClick?: () => void;
  onCheckout?: () => void;
};

export default function HeroBussola({ onCtaClick, onCheckout }: Props) {
  const handleCta = onCtaClick || onCheckout;
  return (
    <header className="relative isolate flex min-h-[100svh] w-full items-end justify-start overflow-hidden bg-[oklch(0.09_0.03_265)] md:items-center">
      {/* Fundo cósmico — mobile: bússola no topo, texto na parte escura inferior; desktop: mandala à direita */}
      <picture className="pointer-events-none absolute inset-0 h-full w-full">
        <source media="(max-width: 767px)" srcSet={heroMobileAsset.url} />
        <img
          src={heroAsset.url}
          alt="Roda zodiacal dourada com planetas em um céu estrelado"
          className="h-full w-full object-cover object-top md:object-[68%_center] lg:object-[60%_center]"
          loading="eager"
          fetchPriority="high"
          width={1200}
          height={800}
        />
      </picture>

      {/* Brilho azul da galáxia no lado esquerdo (desktop) */}
      <div className="pointer-events-none absolute inset-0 hidden bg-[radial-gradient(55%_65%_at_12%_45%,oklch(0.42_0.13_265/0.55),transparent_70%)] md:block" />

      {/* Véu: mobile — escurece a parte inferior para legibilidade do texto; desktop — preserva mandala à direita */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-[oklch(0.07_0.02_265/0.2)] via-[oklch(0.07_0.02_265/0.75)] to-[oklch(0.07_0.02_265/0.95)] md:bg-[linear-gradient(90deg,oklch(0.07_0.02_265/0.95)_0%,oklch(0.07_0.02_265/0.82)_28%,oklch(0.07_0.02_265/0.35)_46%,transparent_58%)]" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-[oklch(0.07_0.02_265)] to-transparent md:h-32" />

      <div className="relative z-10 w-full px-6 pb-10 pt-[55vh] md:py-16 md:pl-10 md:pr-6 md:pt-0 lg:pl-16 xl:pl-24">
        <div className="max-w-2xl text-left md:max-w-xl lg:max-w-2xl animate-fade-in">
          <h1 className="mt-3 max-w-xl font-display text-[1.75rem] leading-[1.12] tracking-tight text-foreground sm:text-4xl md:mt-5 md:text-[2.9rem] md:leading-[1.1]">
            Pare de insistir em portas fechadas.{" "}
            <span className="text-gold-gradient font-semibold">
              Aprenda a identificar quais estão abertas para você agora
            </span>
            , no dinheiro, no amor, na carreira e em outras{" "}
            <span className="text-gold">9 áreas</span> da sua vida…
          </h1>

          <p className="mt-4 max-w-xl text-[0.95rem] leading-relaxed text-muted-foreground sm:text-lg md:mt-6">
            Em vez de gastar energia tentando fazer acontecer a qualquer custo, descubra o que o seu
            próprio mapa está sinalizando, e aprenda a agir de acordo com o momento que está vivendo{" "}
            <strong className="font-semibold text-foreground">AGORA</strong> sem misticismo raso e
            com precisão de um relógio cósmico
          </p>

          <p className="mt-4 flex items-start gap-2 text-sm text-muted-foreground md:mt-5">
            <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-gold" />
            <span>
              Sem precisar se tornar especialista em astrologia ou decorar centenas de símbolos
            </span>
          </p>

          <div className="mt-7 max-w-md md:mt-9">
            <button
              type="button"
              onClick={handleCta}
              className="group flex w-full cursor-pointer items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-gold-deep via-gold-soft to-gold px-6 py-4 text-xs font-black uppercase tracking-[0.16em] text-background shadow-[0_18px_50px_-12px_color-mix(in_oklab,var(--gold)_45%,transparent)] transition-all hover:brightness-110 active:scale-[0.99] sm:px-8 sm:py-5 sm:text-sm md:text-base"
            >
              <span>Quero abrir minhas portas</span>
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </button>

            <div className="mt-4 flex flex-wrap items-center justify-start gap-x-4 gap-y-2 text-[0.7rem] text-muted-foreground sm:text-xs">
              <span className="flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-gold" /> Acesso imediato
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-gold" /> 7 dias de garantia
              </span>
              <span className="flex items-center gap-1.5">
                <Tag className="h-3.5 w-3.5 text-gold" /> R$67
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
