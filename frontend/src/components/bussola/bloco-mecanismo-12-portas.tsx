import { motion } from "framer-motion";
import { Lock, DoorOpen, Coins, Heart, Mountain, Moon } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = (i = 0) => ({
  initial: { opacity: 0, y: 22 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.7, ease: EASE, delay: i * 0.06 },
});

const PORTAS = [
  {
    Icon: Coins,
    nome: "A porta do dinheiro",
    casa: "Casa 2",
    fechada:
      "Você manda a proposta e ela emperra. Pede o reajuste e ouve “vamos ver”. Cada real que entra já tem destino antes de cair na conta.",
    aberta:
      "Um cliente que sumiu há meses volta com uma oferta melhor. Você tem coragem de cobrar o que vale e ninguém questiona. Dinheiro aparece de lugares que você nem lembrava.",
  },
  {
    Icon: Heart,
    nome: "A porta do amor",
    casa: "Casas 5 e 7",
    fechada:
      "As conversas emperram antes de virar encontro. Vocês parecem falar línguas diferentes. Ou, pior: nada nem aparece.",
    aberta:
      "Alguém te procura sem você precisar se esforçar. Uma conversa parada destrava do nada. Você se sente à vontade pra ser vista, e isso muda tudo.",
  },
  {
    Icon: Mountain,
    nome: "A porta da carreira",
    casa: "Casa 10",
    fechada:
      "Você entrega o seu melhor e ninguém parece notar. Currículo enviado, silêncio. Começa a achar que o problema é competência.",
    aberta:
      "Seu nome é lembrado numa reunião que você nem estava. Um convite chega sem você correr atrás. As pessoas certas finalmente enxergam o que você faz.",
  },
  {
    Icon: Moon,
    nome: "A porta do recolhimento",
    casa: "Casa 12",
    fechada:
      "Você tenta ser produtiva e trava. Cada tarefa simples vira um esforço enorme. Vem a culpa por estar cansada sem motivo aparente.",
    aberta:
      "Essa porta não pede ação, pede pausa. Quando você respeita o momento, o cansaço passa rápido e a clareza volta sozinha, sem culpa.",
  },
];

export default function BlocoMecanismo12Portas() {
  return (
    <section
      aria-label="O mecanismo das 12 portas"
      className="relative isolate w-full overflow-hidden bg-background py-16 md:py-24"
    >
      <div className="relative mx-auto max-w-3xl px-6">
        <motion.div {...fadeUp(0)} className="text-center">
          <h2 className="mx-auto max-w-xl font-display text-[1.9rem] leading-[1.15] text-foreground sm:text-4xl">
            Você tem 12 portas. Agora mesmo,{" "}
            <span className="text-gold">algumas estão abertas</span>, e você nem sabe quais.
          </h2>
          <p className="mx-auto mt-6 max-w-lg text-[15px] leading-relaxed text-muted-foreground sm:text-base">
            Isso não é força de vontade. Não é sorte. Não é "vibração". O seu mapa tem 12 áreas,
            12 portas, e o céu, se movendo todos os dias, abre e fecha cada uma delas em
            momentos diferentes da sua vida. Quando você empurra uma porta fechada, trava, cansa,
            desiste achando que é falta de esforço. Quando você age numa porta aberta, a mesma
            tarefa que antes parecia impossível simplesmente acontece.
          </p>
        </motion.div>

        <div className="mt-12 space-y-5 md:mt-16">
          {PORTAS.map((p, i) => (
            <motion.div
              key={p.nome}
              {...fadeUp(i + 1)}
              className="overflow-hidden rounded-[22px] border border-gold/20"
              style={{
                background:
                  "linear-gradient(168deg, color-mix(in oklab, var(--gold) 5%, var(--background)) 0%, var(--background) 85%)",
              }}
            >
              <div className="flex items-center gap-3 border-b border-gold/12 px-6 py-4 sm:px-7">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-gold/30 bg-gold/10 text-gold">
                  <p.Icon className="h-4.5 w-4.5" />
                </span>
                <h3 className="font-display text-lg font-semibold text-foreground sm:text-xl">
                  {p.nome}
                </h3>
                <span className="ml-auto whitespace-nowrap rounded-full border border-gold/20 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-gold/70">
                  {p.casa}
                </span>
              </div>

              <div className="grid gap-px sm:grid-cols-2" style={{ background: "color-mix(in oklab, var(--gold) 10%, transparent)" }}>
                <div className="bg-background/80 px-6 py-5 sm:px-7">
                  <div className="mb-2.5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground/70">
                    <Lock className="h-3.5 w-3.5" /> Porta fechada
                  </div>
                  <p className="text-[14px] leading-relaxed text-muted-foreground">{p.fechada}</p>
                </div>
                <div className="bg-background/80 px-6 py-5 sm:px-7">
                  <div className="mb-2.5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-gold">
                    <DoorOpen className="h-3.5 w-3.5" /> Porta aberta
                  </div>
                  <p className="text-[14px] leading-relaxed text-foreground/85">{p.aberta}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div {...fadeUp(5)} className="mx-auto mt-14 max-w-xl text-center md:mt-18">
          <p className="text-[15.5px] leading-[1.85] text-muted-foreground sm:text-base">
            O problema nunca foi a sua disciplina, a sua sorte ou o seu valor. O problema é que
            ninguém te disse: existem 12 portas, elas abrem e fecham o tempo todo, e agir na hora
            certa importa mais do que agir com mais força.
          </p>
          <p className="mt-6 font-display text-[1.3rem] leading-[1.4] text-foreground sm:text-[1.5rem]">
            A Bússola existe pra te mostrar exatamente isso:{" "}
            <span className="text-gold">quais das suas 12 portas estão abertas essa semana</span>,
            pra você parar de empurrar o que está fechado.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
