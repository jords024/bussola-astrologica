import { motion } from "framer-motion";
import { BookOpenText, Compass, Target, Eye, Footprints } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = (i = 0) => ({
  initial: { opacity: 0, y: 22 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.25 },
  transition: { duration: 0.65, ease: EASE, delay: i * 0.07 },
});

const PASSOS = [
  {
    Icon: BookOpenText,
    title: "Acesse o guia",
    body: "Depois da compra, você recebe acesso imediato ao conteúdo e já pode começar a usar a Bússola Astrológica.",
  },
  {
    Icon: Compass,
    title: "Abra seu mapa com trânsitos",
    body: "Você vai aprender, passo a passo, como visualizar os trânsitos acontecendo no seu próprio mapa astral.",
  },
  {
    Icon: Target,
    title: "Identifique a área ativada",
    body: "Descubra qual casa/área da sua vida está sendo movimentada naquele período: relacionamentos, trabalho, dinheiro, rotina, autoestima, família, estudos e muito mais.",
  },
  {
    Icon: Eye,
    title: "Interprete a visão",
    body: "Com o guia, você entende qual energia está em jogo, quais oportunidades podem surgir e quais cuidados fazem sentido naquele momento.",
  },
  {
    Icon: Footprints,
    title: "Aplique na vida real",
    body: "Use suas previsões para tomar decisões com mais clareza: quando agir, quando esperar, onde focar energia e como aproveitar melhor cada fase.",
  },
];

export default function BlocoComoFunciona() {
  return (
    <section
      aria-label="Como funciona na prática"
      className="relative isolate w-full overflow-hidden bg-background py-16 md:py-24"
    >
      <div className="relative mx-auto max-w-3xl px-6">
        <motion.h2
          {...fadeUp(0)}
          className="text-center font-display text-[2rem] leading-[1.1] text-foreground sm:text-4xl"
        >
          Como funciona <span className="text-gold">na prática</span>
        </motion.h2>

        <div className="mt-10 space-y-4 md:mt-14">
          {PASSOS.map((p, i) => (
            <motion.div
              key={p.title}
              {...fadeUp(i + 1)}
              className="flex items-start gap-5 rounded-[20px] border border-gold/18 p-5 sm:p-6"
              style={{
                background:
                  "linear-gradient(168deg, color-mix(in oklab, var(--gold) 4%, var(--background)) 0%, var(--background) 100%)",
              }}
            >
              <div className="flex flex-col items-center">
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-gold/30 bg-gold/10 text-gold">
                  <p.Icon className="h-5 w-5" />
                </span>
                <span className="mt-1.5 font-display text-xs text-gold/50">{`0${i + 1}`}</span>
              </div>
              <div className="pt-1">
                <h3 className="font-display text-lg font-semibold text-foreground sm:text-xl">
                  {p.title}
                </h3>
                <p className="mt-2 text-[14.5px] leading-relaxed text-muted-foreground">{p.body}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
