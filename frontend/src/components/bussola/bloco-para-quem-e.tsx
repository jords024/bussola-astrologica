import { motion } from "framer-motion";
import { Check, X } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = (i = 0) => ({
  initial: { opacity: 0, y: 22 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.25 },
  transition: { duration: 0.7, ease: EASE, delay: i * 0.08 },
});

const PARA_VOCE = [
  "Quer entender os próprios ciclos e parar de viver no automático.",
  "Já percebeu que horóscopo de signo é genérico demais para falar da sua vida real.",
  "Quer aprender a fazer previsões personalizadas no seu próprio mapa astral.",
  "Quer entender os melhores momentos para agir, começar algo, se expor, se recolher ou focar energia em determinada área da vida.",
  "Busca uma forma simples, prática e aplicável de usar astrologia no dia a dia.",
  "Quer entender por que existem fases em que tudo flui... e outras em que parece que nada anda.",
];

const NAO_E_PRA_VOCE = [
  "Quer só consumir previsões prontas sem aprender a interpretar o próprio mapa.",
  "Procura astrologia cheia de misticismo, termos complexos e decoreba.",
  "Não tem interesse em aplicar o conhecimento na vida real.",
];

export default function BlocoParaQuemE() {
  return (
    <section
      aria-label="Para quem é a Bússola Astrológica"
      className="relative isolate w-full overflow-hidden bg-background py-16 md:py-24"
    >
      <div className="relative mx-auto max-w-4xl px-6">
        <motion.h2
          {...fadeUp(0)}
          className="text-center font-display text-[2rem] leading-[1.1] text-foreground sm:text-4xl"
        >
          Para quem é a <span className="text-gold">Bússola Astrológica</span>
        </motion.h2>

        <div className="mt-10 grid gap-5 md:mt-14 md:grid-cols-2">
          <motion.div
            {...fadeUp(1)}
            className="rounded-[22px] border border-gold/22 p-6 sm:p-8"
            style={{
              background:
                "linear-gradient(168deg, color-mix(in oklab, var(--gold) 6%, var(--background)) 0%, var(--background) 100%)",
            }}
          >
            <h3 className="font-body text-sm font-semibold uppercase tracking-[0.2em] text-gold">
              Isso é pra você que...
            </h3>
            <ul className="mt-5 space-y-3.5">
              {PARA_VOCE.map((t) => (
                <li key={t} className="flex items-start gap-3 text-[14.5px] leading-relaxed text-foreground/85">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-gold" />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            {...fadeUp(2)}
            className="rounded-[22px] border border-white/10 bg-background/60 p-6 sm:p-8"
          >
            <h3 className="font-body text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Isso não é pra você que...
            </h3>
            <ul className="mt-5 space-y-3.5">
              {NAO_E_PRA_VOCE.map((t) => (
                <li key={t} className="flex items-start gap-3 text-[14.5px] leading-relaxed text-muted-foreground">
                  <X className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground/70" />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
