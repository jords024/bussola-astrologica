import { motion } from "framer-motion";
import { Quote } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = (i: number) => ({
  initial: { opacity: 0, y: 22 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.3 },
  transition: { duration: 0.7, ease: EASE, delay: i * 0.08 },
});

const PERGUNTAS = [
  "Por que tem períodos em que tudo parece fluir… e outros em que nada vai pra frente?",
  "Por que tem dias em que eu acordo cheio de energia e motivação… e outros em que eu simplesmente quero me recolher?",
  "Será que eu estou insistindo nas coisas no momento errado?",
  "Quando é o momento mais favorável para conhecer alguém, pedir um aumento, mudar o visual ou começar um projeto pessoal?",
];

export default function BlocoVoceJaSePegouPensando() {
  return (
    <section
      aria-label="Você já se pegou pensando..."
      className="relative isolate w-full overflow-hidden bg-background py-16 md:py-24"
    >
      <div className="relative mx-auto max-w-2xl px-6 text-center">
        <motion.h2
          {...fadeUp(0)}
          className="font-display text-[1.9rem] leading-[1.15] text-foreground sm:text-4xl"
        >
          Você já se pegou pensando<span className="text-gold">...</span>
        </motion.h2>

        <div className="mt-11 space-y-7 md:mt-14 md:space-y-9">
          {PERGUNTAS.map((p, i) => (
            <motion.div key={p} {...fadeUp(i + 1)} className="flex items-start justify-center gap-3.5">
              <Quote className="mt-1 h-4 w-4 shrink-0 -scale-x-100 text-gold/70" />
              <p className="text-left font-display text-[1.15rem] leading-[1.5] text-foreground/90 sm:text-[1.4rem]">
                {p}
              </p>
            </motion.div>
          ))}
        </div>

        <motion.p
          {...fadeUp(PERGUNTAS.length + 1)}
          className="mx-auto mt-12 max-w-md text-base leading-relaxed text-muted-foreground sm:mt-16 sm:text-lg"
        >
          Se alguma dessas te tocou, não é falta de sorte nem de esforço. É que ninguém te ensinou
          a olhar pro céu do jeito certo.
        </motion.p>
      </div>
    </section>
  );
}
