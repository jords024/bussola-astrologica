import { motion } from "framer-motion";
import { BookOpen, Sparkles, Gift, MonitorPlay, Clock, DoorOpen } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = {
  initial: { opacity: 0, y: 22 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.7, ease: EASE },
};

const MOMENTOS = [
  "ter aquela conversa",
  "mandar a proposta",
  "se expor",
  "mudar de casa",
  "começar aquilo que você vem adiando",
  "se recolher sem se sentir culpada por isso",
];

const BONUS = [
  {
    icon: DoorOpen,
    title: "Super Guia das Casas Astrológicas",
    body: "O que é cada uma das 12 portas da sua vida, de verdade. Porque a porta do dinheiro não é só salário, a do amor não é só namoro e a da casa não é só o imóvel onde você mora.",
  },
  {
    icon: BookOpen,
    title: "E-book: A Linguagem Astrológica",
    body: "A lógica por trás de tudo isso, sem misticismo e sem decoreba. É o material que te dá argumento pra explicar o que você tá fazendo, pra amiga, pro marido, pro cético que sempre aparece.",
  },
];

export default function BlocoOfertaConteudo() {
  return (
    <section
      aria-label="Tudo que você vai receber"
      className="relative isolate w-full overflow-hidden bg-background pb-20 md:pb-28"
    >
      <div className="relative mx-auto max-w-3xl px-6">
        {/* Card principal */}
        <motion.div
          {...fadeUp}
          className="relative overflow-hidden rounded-[28px] border border-gold/25 bg-card/70 p-7 shadow-[0_30px_90px_-50px_color-mix(in_oklab,var(--gold)_55%,transparent)] backdrop-blur-sm sm:p-10"
        >
          <div
            aria-hidden
            className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full"
            style={{
              background:
                "radial-gradient(closest-side, color-mix(in oklab, var(--gold) 22%, transparent), transparent 75%)",
            }}
          />

          <div className="relative flex items-center gap-4">
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-gold/30 bg-gold/10 text-2xl">
              📕
            </span>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-gold-soft/80">
                O guia principal
              </p>
              <h3 className="font-display text-2xl font-semibold text-foreground sm:text-3xl">
                Bússola Astrológica
              </h3>
            </div>
          </div>

          <p className="relative mt-6 text-[15.5px] leading-relaxed text-muted-foreground sm:text-base">
            O guia que te ensina a abrir o seu mapa e enxergar, com os seus próprios olhos, quais
            portas da sua vida estão abertas neste momento, e quais não vão abrir por mais que você
            empurre.
          </p>

          {/* 60 interpretações */}
          <div className="relative mt-8 rounded-2xl border border-gold/15 bg-background/40 p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <Sparkles className="h-5 w-5 shrink-0 text-gold" />
                <h4 className="font-display text-lg font-semibold text-foreground sm:text-xl">
                  60 interpretações práticas de trânsitos
                </h4>
              </div>
              <span className="whitespace-nowrap rounded-full border border-gold/25 bg-gold/10 px-3 py-1 text-[11px] font-semibold text-gold-soft">
                5 planetas × 12 casas
              </span>
            </div>
            <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground">
              São as 60 leituras das suas 12 portas: cada planeta em cada área da sua vida, com o
              que abre, o que trava, onde vale a pena colocar força e onde é melhor você guardar a
              sua.{" "}
              <span className="font-semibold text-foreground">
                Você não lê isso de capa a capa.
              </span>{" "}
              Você acha a sua porta, lê três linhas e fecha.
            </p>

            <p className="mt-5 text-sm font-semibold text-foreground">
              Você vai saber a hora certa de:
            </p>
            <ul className="mt-3 grid gap-2.5 sm:grid-cols-2">
              {MOMENTOS.map((m) => (
                <li key={m} className="flex items-start gap-2.5 text-[14px] text-muted-foreground">
                  <span className="mt-2 h-1 w-1 shrink-0 rotate-45 bg-gold" />
                  <span>{m}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Aulas práticas */}
          <div className="relative mt-5 flex items-start gap-3.5 rounded-2xl border border-gold/15 bg-background/40 p-5 sm:p-6">
            <MonitorPlay className="mt-0.5 h-5 w-5 shrink-0 text-gold" />
            <div>
              <h4 className="font-display text-lg font-semibold text-foreground">
                Aulas práticas e objetivas
              </h4>
              <p className="mt-2 text-[14.5px] leading-relaxed text-muted-foreground">
                Eu te mostro na tela onde clicar, onde olhar e como ler. Passo a passo, do começo ao
                fim, sem decorar nada.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Bônus */}
        <div className="relative mt-8 grid gap-5 sm:grid-cols-2">
          {BONUS.map((b, i) => {
            const Icon = b.icon;
            return (
              <motion.div
                key={b.title}
                {...fadeUp}
                transition={{ ...fadeUp.transition, delay: 0.1 + i * 0.08 }}
                className="relative overflow-hidden rounded-3xl border border-gold/20 bg-card/50 p-6"
              >
                <span className="inline-flex items-center gap-1.5 rounded-full border border-gold/30 bg-gold/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-gold-soft">
                  <Gift className="h-3 w-3" />
                  Bônus grátis
                </span>
                <div className="mt-4 flex items-center gap-3">
                  <Icon className="h-5 w-5 shrink-0 text-gold" />
                  <h4 className="font-display text-lg font-semibold leading-tight text-foreground">
                    {b.title}
                  </h4>
                </div>
                <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">{b.body}</p>
              </motion.div>
            );
          })}
        </div>

        <motion.p
          {...fadeUp}
          className="mt-8 flex items-center justify-center gap-2 text-center text-xs text-muted-foreground/80"
        >
          <Clock className="h-3.5 w-3.5 text-gold" />
          Acesso imediato após a confirmação, sem espera.
        </motion.p>
      </div>
    </section>
  );
}
