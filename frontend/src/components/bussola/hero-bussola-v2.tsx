import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck, Zap, Tag } from "lucide-react";
import heroAsset from "../../assets/bussola-hero.png.asset.json";
import heroMobileAsset from "../../assets/bussola-hero-mobile.png.asset.json";
import logoAsset from "../../assets/bussola-logo.png.asset.json";

const EASE = [0.16, 1, 0.3, 1] as const;

type Props = {
  onCheckout: () => void;
};

export default function HeroBussolaV2({ onCheckout }: Props) {
  return (
    <header className="relative isolate flex min-h-[100svh] w-full items-end justify-center overflow-hidden bg-[oklch(0.09_0.03_265)] md:items-center">
      {/* Fundo cósmico: claro em cima (a roda aparece inteira), escurece
          progressivamente pra baixo, onde o texto fica */}
      <picture className="pointer-events-none absolute inset-0 h-full w-full">
        <source media="(max-width: 767px)" srcSet={heroMobileAsset.url} />
        <img
          src={heroAsset.url}
          alt="Roda zodiacal dourada com planetas em um céu estrelado"
          className="h-full w-full object-cover object-top opacity-65 md:object-center"
          loading="eager"
          fetchPriority="high"
        />
      </picture>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-[oklch(0.08_0.02_265/0.35)] via-[oklch(0.08_0.02_265/0.7)] to-[oklch(0.07_0.02_265/0.97)]" />

      <div className="relative z-10 mx-auto flex w-full max-w-2xl flex-col items-center px-6 pb-14 pt-8 text-center md:py-24">
        <motion.img
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: EASE }}
          src={logoAsset.url}
          alt="Bússola Astrológica"
          className="h-16 w-auto md:h-20"
          loading="eager"
        />

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.15, ease: EASE }}
        >
          <h1 className="mt-8 font-display text-[1.7rem] font-semibold leading-[1.2] tracking-tight text-foreground sm:text-4xl md:mt-10 md:text-[2.6rem]">
            Destrave o mesmo conhecimento astrológico que{" "}
            <span className="text-gold-gradient">Reis e Rainhas usavam</span> para saber quando
            seu dinheiro vai fluir, quando os relacionamentos ficam perfeitos e quando sua
            carreira pode destravar...
          </h1>

          <p className="mx-auto mt-6 max-w-lg text-[0.95rem] leading-relaxed text-muted-foreground sm:text-lg">
            Seu mapa mostra quais portas estão abertas pra você agora, e você só precisa
            aprender a ler, sem precisar se tornar especialista em astrologia.
          </p>

          <div className="mx-auto mt-8 max-w-sm md:mt-10">
            <button
              type="button"
              onClick={onCheckout}
              className="group flex w-full cursor-pointer items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-gold-deep via-gold-soft to-gold px-6 py-4 text-xs font-black uppercase tracking-[0.16em] text-background shadow-[0_18px_50px_-12px_color-mix(in_oklab,var(--gold)_45%,transparent)] transition-all hover:brightness-110 active:scale-[0.99] sm:px-8 sm:py-5 sm:text-sm"
            >
              <span>Quero abrir minhas portas</span>
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </button>

            <div className="mt-5 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-[0.7rem] text-muted-foreground sm:text-xs">
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
        </motion.div>
      </div>
    </header>
  );
}
