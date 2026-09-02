import { motion } from "framer-motion";
import { X } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = (i = 0) => ({
  initial: { opacity: 0, y: 22 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.25 },
  transition: { duration: 0.7, ease: EASE, delay: i * 0.08 },
});

const PROBLEMAS = [
  {
    title: "O problema do horóscopo genérico",
    body: "Fizeram você acreditar que astrologia é só ler previsões para o seu signo… quando na verdade duas pessoas do mesmo signo podem estar vivendo momentos completamente diferentes. E no fundo você já percebeu isso.",
  },
  {
    title: "A complicação desnecessária",
    body: "A maioria dos conteúdos de astrologia parecem impossíveis de entender. Símbolos, termos técnicos, excesso de misticismo e interpretações que não mostram como aplicar aquilo na vida real.",
  },
  {
    title: "A falta de um método prático",
    body: "Quase ninguém ensina astrologia como uma ferramenta prática de previsões para o dia a dia. Você aprende sobre signos… mas não aprende a interpretar os movimentos acontecendo na SUA vida.",
  },
];

export default function BlocoCulpaNaoESua() {
  return (
    <section
      aria-label="A culpa não é sua"
      className="relative isolate w-full overflow-hidden bg-background py-16 md:py-24"
    >
      <div className="relative mx-auto max-w-4xl px-6">
        <motion.div {...fadeUp(0)} className="mx-auto max-w-xl text-center">
          <h2 className="font-display text-[2rem] leading-[1.1] text-foreground sm:text-4xl">
            A culpa <span className="text-gold">não é sua.</span>
          </h2>
          <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground sm:text-base">
            A astrologia foi transformada em algo genérico, complexo e distante da vida real.
          </p>
        </motion.div>

        <div className="mt-10 grid gap-5 sm:grid-cols-3 md:mt-14">
          {PROBLEMAS.map((p, i) => (
            <motion.div
              key={p.title}
              {...fadeUp(i + 1)}
              className="rounded-[22px] border border-gold/20 p-6"
              style={{
                background:
                  "linear-gradient(168deg, color-mix(in oklab, var(--gold) 5%, var(--background)) 0%, var(--background) 82%)",
              }}
            >
              <span className="grid h-9 w-9 place-items-center rounded-full border border-red-400/30 bg-red-500/10 text-red-400">
                <X className="h-4 w-4" />
              </span>
              <h3 className="mt-4 font-display text-lg font-semibold text-foreground">{p.title}</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">{p.body}</p>
            </motion.div>
          ))}
        </div>

        {/* Ponte: a verdade é que pode ser simples */}
        <motion.div
          {...fadeUp(4)}
          className="relative mx-auto mt-12 max-w-2xl rounded-[24px] border border-gold/25 p-7 text-center md:mt-16 md:p-10"
          style={{
            background:
              "linear-gradient(168deg, color-mix(in oklab, var(--gold) 8%, var(--background)) 0%, var(--background) 78%)",
          }}
        >
          <h3 className="font-display text-[1.6rem] leading-[1.2] text-foreground sm:text-3xl">
            A verdade é que pode ser <span className="text-gold">simples.</span>
          </h3>
          <p className="mt-5 text-[15px] leading-relaxed text-muted-foreground sm:text-base">
            Com o método certo, você lê os trânsitos no seu mapa sem enrolação, mesmo sem saber
            astrologia.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
