import { motion } from "framer-motion";
import { ArrowRight, Brain, Heart, Lock, Wallet } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.15, margin: "0px 0px -10% 0px" },
  transition: { duration: 0.6, ease: EASE },
};

const PILARES = [
  {
    n: "01",
    icon: Wallet,
    tag: "O Dinheiro e a Carreira",
    title: "A Exaustão de Trabalhar no Escuro",
    body: [
      "Olha para a sua relação com o seu trabalho e com o seu dinheiro hoje.",
      "Você passa o mês inteiro com o pescoço duro de tensão, apagando incêndio e resolvendo problemas. Mas quando chega a hora da colheita, parece que o dinheiro escapa por entre os seus dedos.",
      "Toda vez que você consegue juntar um pouco de paz financeira, surge um imprevisto bizarro que drena as suas reservas.",
      "Você vê pessoas que não têm metade da sua dedicação, do seu caráter ou do seu talento sendo promovidas, fechando negócios e prosperando com uma facilidade que chega a dar raiva.",
    ],
    listLabel: "Enquanto isso, você continua presa na dúvida:",
    list: [
      "Devo mudar de área ou insistir no que estou fazendo?",
      "Vale a pena arriscar meu dinheiro agora ou devo segurar?",
      "Por que eu sinto que estou trocando a minha saúde por um salário que mal paga os remédios que eu tomo para aguentar a pressão?",
    ],
    close:
      "O problema nunca foi a sua capacidade de trabalho. O problema é que você está tentando plantar no inverno e colher na tempestade, porque nunca te ensinaram a enxergar as suas janelas reais de oportunidade.",
  },
  {
    n: "02",
    icon: Heart,
    tag: "O Amor e os Relacionamentos",
    title: "A Solidão Acompanhada",
    body: [
      "Essa talvez seja a dor mais pesada que você carrega, porque é a que você mais tenta esconder do mundo.",
      "Não existe nada mais solitário do que deitar na mesma cama com alguém e se sentir a quilômetros de distância.",
      "O silêncio na hora do jantar. As conversas que viraram apenas cobrança de contas, rotina da casa ou desculpas para não olhar nos olhos.",
      "Você se acostumou tanto a cuidar de tudo que acabou virando a mãe do seu parceiro, enquanto a admiração, o carinho e o respeito foram morrendo aos poucos.",
      "Ou, se você está solteira, você conhece alguém novo, cria esperança, se entrega de peito aberto e, depois de alguns meses, percebe que caiu exatamente na mesma armadilha: uma pessoa imatura, indisponível ou que te exige tudo sem te dar nada em troca.",
      "Você já chegou a pensar que o problema era você. Que você tinha o tal do dedo podre ou que não nasceu para ser feliz no amor.",
    ],
    close:
      "A verdade é que você foi ensinada a amar se anulando. Você atrai essas situações porque a sua estrutura emocional foi programada para salvar os outros em vez de se proteger.",
  },
  {
    n: "03",
    icon: Brain,
    tag: "A Sua Paz de Espírito",
    title: "A Lixeira Emocional dos Outros",
    body: [
      "Quantas vezes você disse sim para a sua família, para os seus amigos ou no trabalho querendo gritar não com todas as forças da sua alma?",
      "Você virou a pessoa forte da família. O porto seguro de todo mundo. Aquela que escuta os desabafos, que empresta o dinheiro, que resolve as crises e que nunca pode demonstrar fraqueza.",
      "E quando é você que precisa de um ombro para chorar? Todo mundo some.",
      "Você vive pagando um pedágio emocional diário para ser aceita. E o pior: se em um dia qualquer você decide colocar um limite e pensar em você pela primeira vez, eles se juntam para te fazer sentir a pessoa mais egoísta e ingrata do mundo.",
    ],
    close:
      "O resultado disso é um cansaço que não passa com oito horas de sono. É uma queimação no peito, uma falta de ar de domingo à noite e a sensação de estar vivendo uma vida emprestada.",
  },
];

export default function BlocoCustoInvisivel({ onCheckout }: { onCheckout: () => void }) {
  return (
    <section className="relative z-30 overflow-hidden border-t border-gold/10 bg-background py-20 md:py-28">
      {/* vinheta dourada discreta */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-[60vh] opacity-[0.10]"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 0%, color-mix(in oklab, var(--gold) 60%, transparent), transparent 70%)",
        }}
      />

      <div className="relative mx-auto max-w-3xl px-6">
        {/* ---------------- Abertura ---------------- */}
        <motion.div {...fadeUp} className="text-center">
          <span className="text-[0.7rem] font-bold uppercase tracking-[0.28em] text-gold-soft/80">
            O diagnóstico
          </span>
          <h2 className="mt-5 font-display text-3xl font-black leading-[1.12] tracking-tight text-foreground sm:text-4xl md:text-5xl">
            O Custo Invisível de Passar a Vida Inteira{" "}
            <span className="text-gold-gradient">Tentando Adivinhar o Caminho Certo</span>
          </h2>
          <p className="mx-auto mt-6 text-base leading-relaxed text-muted-foreground sm:text-lg">
            Se você olhar para trás agora, vai perceber um padrão: você não parou de lutar um único
            dia. Você trabalhou, cuidou de todo mundo, engoliu desaforos e fez tudo o que disseram
            que era o certo.
          </p>
          <p className="mx-auto mt-5 font-display text-xl italic leading-snug text-gold-soft sm:text-2xl">
            A pergunta que não quer calar é: por que a sua vida continua travando sempre nos mesmos
            lugares?
          </p>
        </motion.div>

        {/* ---------------- A Ilusão do Esforço ---------------- */}
        <motion.div {...fadeUp} className="mt-16 border-l-2 border-gold/40 pl-5 sm:mt-20 sm:pl-7">
          <h3 className="font-display text-2xl font-bold leading-tight text-foreground sm:text-3xl">
            A Ilusão do Esforço:{" "}
            <span className="text-gold">Por que a Força Bruta Não Está Funcionando</span>
          </h3>
        </motion.div>

        <motion.div {...fadeUp} className="mt-8 space-y-6">
          <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            A sociedade te vendeu a maior mentira de todas: a de que bastava você se esforçar mais
            para tudo dar certo.
          </p>
          <p className="text-lg font-bold leading-snug text-foreground sm:text-xl">
            Então você dobrou a aposta.
          </p>
          <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            Acordou mais cedo, assumiu mais responsabilidades, tentou ter mais paciência com quem
            não te respeita e guardou as suas dores no fundo do peito para não incomodar ninguém.
          </p>
        </motion.div>

        <motion.blockquote
          {...fadeUp}
          className="mt-10 rounded-r-2xl border-l-4 border-gold bg-card/70 px-6 py-6 md:shadow-[0_20px_60px_-30px_color-mix(in_oklab,var(--gold)_50%,transparent)] sm:px-8"
        >
          <p className="font-display text-xl leading-snug text-foreground sm:text-2xl">
            Só que ninguém te avisou que se você estiver caminhando na direção errada,{" "}
            <span className="text-gold">
              correr mais rápido só vai te levar mais depressa para o abismo.
            </span>
          </p>
        </motion.blockquote>

        {/* separador ornamental */}
        <motion.div {...fadeUp} className="mt-14 flex items-center justify-center gap-4">
          <span className="h-px w-16 bg-gradient-to-r from-transparent to-gold/50" />
          <span className="h-1.5 w-1.5 rotate-45 bg-gold" />
          <span className="h-px w-16 bg-gradient-to-l from-transparent to-gold/50" />
        </motion.div>

        <motion.p
          {...fadeUp}
          className="mx-auto mt-8 max-w-2xl text-center text-base leading-relaxed text-muted-foreground sm:text-lg"
        >
          Quando você não conhece o seu próprio funcionamento, a sua vida entra em um ciclo de
          repetição silencioso que corrói{" "}
          <span className="font-semibold text-foreground">
            os três pilares mais importantes da sua existência
          </span>
          .
        </motion.p>
      </div>

      {/* ---------------- Os 3 Pilares ---------------- */}
      <div className="relative mx-auto mt-14 max-w-3xl space-y-8 px-6 sm:mt-16">
        {PILARES.map((p) => {
          const Icon = p.icon;
          return (
            <motion.article
              key={p.n}
              {...fadeUp}
              className="relative overflow-hidden rounded-3xl border border-gold/15 bg-card/60 p-6 md:shadow-[0_30px_80px_-50px_color-mix(in_oklab,var(--gold)_60%,transparent)] md:backdrop-blur-sm sm:p-9"
            >
              <span
                aria-hidden
                className="pointer-events-none absolute -right-6 -top-8 select-none font-display text-[7rem] font-black leading-none text-gold/[0.07] sm:text-[9rem]"
              >
                {p.n}
              </span>

              <div className="relative flex items-center gap-4">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-gold/30 bg-gold/10">
                  <Icon className="h-5 w-5 text-gold" />
                </span>
                <div>
                  <p className="text-[0.65rem] font-bold uppercase tracking-[0.22em] text-gold-soft/80">
                    Pilar {p.n}
                  </p>
                  <p className="font-display text-lg font-bold leading-tight text-foreground sm:text-xl">
                    {p.tag}
                  </p>
                </div>
              </div>

              <h4 className="relative mt-6 font-display text-2xl font-black leading-tight text-gold-gradient sm:text-3xl">
                {p.title}
              </h4>

              <div className="relative mt-5 space-y-4">
                {p.body.map((t) => (
                  <p
                    key={t.slice(0, 24)}
                    className="text-base leading-relaxed text-muted-foreground"
                  >
                    {t}
                  </p>
                ))}
              </div>

              {p.list && (
                <div className="relative mt-6">
                  <p className="text-base font-semibold text-foreground">{p.listLabel}</p>
                  <ul className="mt-4 space-y-3">
                    {p.list.map((q) => (
                      <li key={q.slice(0, 24)} className="flex gap-3">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rotate-45 bg-gold" />
                        <span className="text-base leading-relaxed text-muted-foreground">{q}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <p className="relative mt-7 border-t border-gold/15 pt-6 text-base font-medium leading-relaxed text-foreground sm:text-lg">
                {p.close}
              </p>
            </motion.article>
          );
        })}
      </div>

      {/* ---------------- O Confronto Final ---------------- */}
      <div className="relative mx-auto mt-20 max-w-3xl px-6 md:mt-24">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10 opacity-[0.12]"
          style={{
            background:
              "radial-gradient(50% 45% at 50% 40%, color-mix(in oklab, var(--gold) 70%, transparent), transparent 72%)",
          }}
        />

        <motion.h3
          {...fadeUp}
          className="text-center font-display text-3xl font-black leading-[1.15] tracking-tight text-foreground sm:text-4xl md:text-5xl"
        >
          O Confronto Final:{" "}
          <span className="text-gold-gradient">Até Quando Você Vai Aguentar Viver Assim?</span>
        </motion.h3>

        <motion.div {...fadeUp} className="mt-8 space-y-6 text-center">
          <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            Pensa com sinceridade: quantos anos mais você aguenta sustentar esse personagem?
          </p>
          <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            O seu corpo já começou a te mandar os sinais: a insônia de madrugada, a memória
            falhando, as dores musculares e aquela tristeza repentina que aparece do nada quando
            você fica em silêncio.
          </p>
          <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            Continuar tentando resolver esses três pilares na força bruta não vai funcionar. Você já
            tentou isso nos últimos anos e o resultado foi apenas mais cansaço.
          </p>
        </motion.div>

        <motion.div
          {...fadeUp}
          className="mx-auto mt-10 max-w-2xl rounded-3xl border border-gold/25 bg-card/70 px-6 py-8 text-center md:backdrop-blur-sm sm:px-10"
        >
          <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            Para estancar esse sangramento, você precisa de uma única coisa:
          </p>
          <p className="mt-3 font-display text-3xl font-black leading-tight text-gold-gradient sm:text-4xl">
            você precisa de um mapa.
          </p>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground sm:text-lg">
            Um guia que te mostre onde está a raiz de cada um desses nós e qual é a saída exata para
            você retomar o controle da sua vida.
          </p>
        </motion.div>

        <motion.div {...fadeUp} className="mt-10 space-y-5 text-center">
          <p className="font-display text-xl font-bold leading-snug text-gold sm:text-2xl">
            É exatamente aqui que entra a virada de chave do Astrowake.
          </p>
          <p className="mx-auto max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            Você não precisa de mais teorias complicadas. Você só precisa entender as três perguntas
            simples que destravam a sua clareza no dia a dia.
          </p>
        </motion.div>

        {/* ---------------- CTA ---------------- */}
        <motion.div {...fadeUp} className="mx-auto mt-10 max-w-xl">
          <button
            onClick={onCheckout}
            className="group flex w-full cursor-pointer items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-gold via-gold-soft to-gold px-6 py-5 text-center text-sm font-black uppercase leading-tight tracking-wider text-background shadow-[0_18px_50px_-12px_color-mix(in_oklab,var(--gold)_45%,transparent)] transition-all hover:brightness-110 active:scale-[0.99] sm:text-base"
          >
            <span>Chega de viver no escuro • Quero destravar minha vida</span>
            <ArrowRight className="h-5 w-5 shrink-0 transition-transform group-hover:translate-x-1" />
          </button>
          <p className="mt-3 flex items-center justify-center gap-2 text-center text-xs text-muted-foreground">
            <Lock className="h-3.5 w-3.5 shrink-0" />
            <span>Acesso Completo ao Método Astrowake • 7 Dias de Garantia Incondicional</span>
          </p>
        </motion.div>
      </div>
    </section>
  );
}
