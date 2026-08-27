import { useState } from "react";
import { ChevronRight } from "lucide-react";

export interface FaqItem {
  pergunta: string;
  resposta: string;
}

export const FAQ_ITEMS: FaqItem[] = [
  {
    pergunta: "Como vou receber o acesso?",
    resposta:
      "Assim que a compra for confirmada, você recebe acesso imediato à plataforma e já pode começar a usar a Bússola Astrológica no mesmo dia.",
  },
  {
    pergunta: "Preciso saber astrologia para conseguir usar?",
    resposta:
      "Não. A Bússola Astrológica foi criada justamente para simplificar a astrologia e transformar previsões em algo prático e aplicável na vida real.",
  },
  {
    pergunta: "Por quanto tempo terei acesso?",
    resposta:
      "O acesso é vitalício. Você poderá acessar o conteúdo e os bônus quando quiser.",
  },
  {
    pergunta: "Isso funciona mesmo para quem nunca conseguiu entender astrologia?",
    resposta:
      "Sim. O método foi criado para pessoas que querem aprender previsões astrológicas de forma simples, sem decoreba e sem linguagem complicada.",
  },
  {
    pergunta: "Posso pagar por PIX ou boleto?",
    resposta:
      "Sim. Você poderá escolher entre cartão de crédito, Pix ou boleto bancário na hora da compra.",
  },
  {
    pergunta: "Tem garantia?",
    resposta:
      "Sim. Você tem 7 dias de garantia incondicional para acessar o conteúdo e decidir com tranquilidade.",
  },
];

export default function BlocoFAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleItem = (index: number) => {
    setOpenIndex((prev) => (prev === index ? null : index));
  };

  return (
    <section
      aria-label="Perguntas Frequentes"
      className="relative isolate w-full overflow-hidden bg-background py-16 md:py-24"
    >
      {/* Brilho de fundo sutil */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(50% 40% at 50% 20%, color-mix(in oklab, var(--gold) 10%, transparent) 0%, transparent 75%)",
        }}
      />

      <div className="relative mx-auto max-w-6xl px-6">
        {/* Cabeçalho centralizado */}
        <div className="text-center">
          <h2 className="font-display text-3xl tracking-wide text-foreground sm:text-4xl md:text-5xl">
            PERGUNTAS <span className="text-gold-gradient font-semibold">FREQUENTES</span>
          </h2>
        </div>

        {/* Grade responsiva: texto explicativo à esquerda no desktop e sanfona à direita */}
        <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_2fr] lg:gap-14">
          <div className="text-left">
            <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
              Tudo o que você precisa saber sobre o{" "}
              <strong className="font-semibold text-foreground">Bússola Astrológica</strong>
            </p>
          </div>

          {/* Lista de acordeões */}
          <div className="flex flex-col gap-3.5">
            {FAQ_ITEMS.map((item, index) => {
              const isOpen = openIndex === index;
              const itemId = `faq-item-${index}`;
              const buttonId = `faq-btn-${index}`;

              return (
                <div
                  key={item.pergunta}
                  className={`overflow-hidden rounded-2xl border transition-all duration-300 ${
                    isOpen
                      ? "border-gold/40 bg-[oklch(0.12_0.04_265/0.85)] shadow-[0_0_20px_rgba(234,179,8,0.06)]"
                      : "border-border/60 bg-[oklch(0.09_0.03_265/0.7)] hover:border-gold/25 hover:bg-[oklch(0.11_0.03_265/0.8)]"
                  }`}
                >
                  <button
                    id={buttonId}
                    type="button"
                    onClick={() => toggleItem(index)}
                    aria-expanded={isOpen}
                    aria-controls={itemId}
                    className="flex w-full items-center justify-between gap-4 p-5 text-left transition-colors sm:p-6"
                  >
                    <span className="font-medium text-foreground text-[15px] sm:text-base md:text-lg">
                      {item.pergunta}
                    </span>
                    <span
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-transform duration-300 ${
                        isOpen ? "rotate-90 text-gold" : "text-gold"
                      }`}
                    >
                      <ChevronRight className="h-5 w-5" />
                    </span>
                  </button>

                  <div
                    id={itemId}
                    role="region"
                    aria-labelledby={buttonId}
                    className={`grid transition-all duration-300 ease-in-out ${
                      isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                    }`}
                  >
                    <div className="overflow-hidden">
                      <div className="border-t border-border/40 px-5 pb-6 pt-4 sm:px-6 sm:pb-7">
                        <p className="text-[14.5px] leading-relaxed text-muted-foreground sm:text-[15.5px]">
                          {item.resposta}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
