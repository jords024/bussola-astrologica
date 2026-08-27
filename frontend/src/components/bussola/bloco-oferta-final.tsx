import { motion } from "framer-motion";
import { ArrowRight, Lock, ShieldCheck, Zap, Infinity as InfinityIcon } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = {
  initial: { opacity: 0, y: 22 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.7, ease: EASE },
};

const ITENS = [
  { nome: "Bússola Astrológica — Guia de Previsões Diárias", preco: "R$197" },
  { nome: "Apostila com 60 Interpretações dos Trânsitos", preco: "R$67" },
  { nome: "Checklist Prático de Previsões Astrológicas", preco: "R$47" },
  { nome: "Super Guia das Casas Astrológicas", preco: "R$47" },
  { nome: "E-book: A Linguagem Astrológica", preco: "R$47" },
];

type Props = {
  onCheckout: () => void;
};

export default function BlocoOfertaFinal({ onCheckout }: Props) {
  return (
    <section
      aria-label="Oferta especial de inscrição"
      className="relative isolate w-full overflow-hidden bg-background py-6 md:py-10"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 45% at 50% 40%, color-mix(in oklab, var(--gold) 14%, transparent) 0%, transparent 72%)",
        }}
      />

      <div className="relative mx-auto max-w-3xl px-6">
        {/* Empilhado de valor */}
        <motion.div {...fadeUp} className="text-center">
          <p className="text-[11px] font-bold uppercase tracking-[0.28em] text-gold-soft/80">
            Tudo que você vai receber adquirindo agora
          </p>
        </motion.div>

        <motion.div
          {...fadeUp}
          className="mt-7 overflow-hidden rounded-3xl border border-gold/20 bg-card/50"
        >
          {ITENS.map((item, i) => (
            <div
              key={item.nome}
              className={`flex items-center justify-between gap-4 px-5 py-4 sm:px-7 ${
                i !== ITENS.length - 1 ? "border-b border-border/60" : ""
              }`}
            >
              <span className="text-[14px] leading-snug text-foreground/90 sm:text-[15px]">
                {item.nome}
              </span>
              <span className="shrink-0 whitespace-nowrap text-[14px] font-semibold text-muted-foreground sm:text-[15px]">
                {item.preco}
              </span>
            </div>
          ))}

          <div className="flex items-center justify-between gap-4 border-t border-gold/25 bg-gold/[0.06] px-5 py-5 sm:px-7">
            <span className="text-xs font-bold uppercase tracking-[0.14em] text-foreground/90 sm:text-sm">
              Valor total real
            </span>
            <span className="text-lg font-bold text-muted-foreground line-through decoration-2 sm:text-xl">
              R$405,00
            </span>
          </div>
        </motion.div>

        <motion.p
          {...fadeUp}
          className="mx-auto mt-6 max-w-xl text-center text-[15px] leading-relaxed text-muted-foreground sm:text-base"
        >
          Tudo isso somaria facilmente mais de R$405. Mas a ideia da Bússola Astrológica nunca foi
          criar um curso caro ou complicado.
        </motion.p>

        <motion.div
          {...fadeUp}
          className="mx-auto mt-6 max-w-xl rounded-2xl border border-gold/15 bg-background/40 p-5 text-center sm:p-6"
        >
          <p className="text-[15px] leading-relaxed text-muted-foreground sm:text-base">
            Uma consulta comigo custa{" "}
            <span className="font-semibold text-foreground">R$600</span>. Aqui você adquire uma
            ferramenta e ela responde a pergunta que você tiver, quantas vezes você quiser, pelo
            resto da vida.
          </p>
          <p className="mt-3 text-[15px] leading-relaxed text-gold-soft sm:text-base">
            Se eu acredito mesmo que astrologia de verdade tem que chegar no maior número de gente
            possível, não faz sentido nenhum eu cobrar absurdos por isso.
          </p>
        </motion.div>

        {/* Card de oferta final */}
        <motion.div
          {...fadeUp}
          className="relative mx-auto mt-10 max-w-xl overflow-hidden rounded-[28px] border border-gold/40 bg-card/80 p-1 shadow-[0_30px_100px_-40px_color-mix(in_oklab,var(--gold)_60%,transparent)] backdrop-blur-sm"
        >
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 top-0 h-40"
            style={{
              background:
                "radial-gradient(60% 100% at 50% 0%, color-mix(in oklab, var(--gold) 30%, transparent), transparent 75%)",
            }}
          />
          <div className="relative rounded-[24px] p-6 text-center sm:p-9">
            <span className="inline-flex items-center gap-2 rounded-full border border-gold/40 bg-gold/10 px-4 py-1.5 text-[10.5px] font-bold uppercase tracking-[0.2em] text-gold-soft">
              Oferta especial de inscrição
            </span>

            <h3 className="mt-5 font-display text-3xl font-semibold text-foreground sm:text-4xl">
              Bússola Astrológica
            </h3>
            <p className="mt-2 text-sm text-muted-foreground sm:text-base">
              Todo o conteúdo completo + todos os bônus por:
            </p>

            <div className="mt-6 flex flex-col items-center">
              <span className="font-display text-4xl font-bold text-gold-gradient sm:text-5xl">
                12x de R$6,93
              </span>
              <span className="mt-2 text-sm text-muted-foreground">
                ou <span className="font-semibold text-foreground">R$67</span> à vista
              </span>
            </div>

            <button
              type="button"
              onClick={onCheckout}
              className="group mt-8 flex w-full items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-gold-deep via-gold to-gold-soft px-8 py-5 text-sm font-black uppercase tracking-[0.14em] text-background shadow-[var(--shadow-gold)] transition-transform duration-300 hover:scale-[1.02] active:scale-[0.99] sm:text-base"
            >
              Quero abrir minhas portas
              <ArrowRight className="h-5 w-5 shrink-0 transition-transform duration-300 group-hover:translate-x-1" />
            </button>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-gold" /> Acesso imediato
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-gold" /> Garantia incondicional de 7 dias
              </span>
              <span className="flex items-center gap-1.5">
                <InfinityIcon className="h-3.5 w-3.5 text-gold" /> Acesso vitalício
              </span>
            </div>

            <p className="mt-5 flex items-center justify-center gap-2 text-[11px] text-muted-foreground/70">
              <Lock className="h-3 w-3 text-gold" />
              Pagamento seguro. Seus dados estão 100% protegidos.
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
