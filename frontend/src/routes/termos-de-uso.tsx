import { createFileRoute, Link } from "@tanstack/react-router";
import { FileText, ArrowLeft, ShieldCheck, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/termos-de-uso")({
  head: () => ({
    meta: [
      { title: "Termos de Uso — Bússola Astrológica | Astrowake" },
      {
        name: "description",
        content: "Termos de Uso e Condições Gerais de Aquisição da Bússola Astrológica — Astrowake serviços de astrologia Ltda.",
      },
    ],
  }),
  component: TermosDeUsoPage,
});

export default function TermosDeUsoPage() {
  return (
    <div className="min-h-screen bg-background font-body text-foreground selection:bg-gold selection:text-background">
      {/* Topo / Navegação */}
      <header className="border-b border-border/40 bg-card/40 backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <a
            href="/bussola"
            className="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-gold"
          >
            <ArrowLeft className="h-4 w-4" />
            Voltar para a página principal
          </a>
          <span className="text-xs text-gold uppercase tracking-widest font-semibold">
            Bússola Astrológica
          </span>
        </div>
      </header>

      {/* Conteúdo Principal */}
      <main className="mx-auto max-w-4xl px-6 py-12 sm:py-16">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gold/15 text-gold">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Termos de Uso e Condições Gerais
            </h1>
            <p className="text-xs text-muted-foreground mt-1">
              Astrowake serviços de astrologia Ltda. • CNPJ: 43.066.768/0001-70
            </p>
          </div>
        </div>

        <p className="mt-4 text-xs text-muted-foreground">
          Última atualização: 25 de agosto de 2026
        </p>

        <div className="mt-8 space-y-8 text-[15px] leading-relaxed text-muted-foreground">
          <section className="rounded-2xl border border-gold/20 bg-card/30 p-6 sm:p-8">
            <h2 className="font-display text-xl font-bold text-foreground">1. Aceitação dos Termos</h2>
            <p className="mt-3">
              Ao acessar o site, cadastrar-se ou adquirir qualquer produto digital, curso, guia ou ferramenta da{" "}
              <strong>Bússola Astrológica</strong>, você concorda expressamente em aderir e submeter-se a todos os
              termos, condições e avisos aqui estabelecidos, bem como à nossa Política de Privacidade.
            </p>
            <p className="mt-2">
              Os serviços são disponibilizados pela pessoa jurídica{" "}
              <strong className="text-foreground">Astrowake serviços de astrologia Ltda.</strong>, inscrita no CNPJ sob
              o nº <strong>43.066.768/0001-70</strong>, de titularidade de <strong>Crassus Gobbi</strong>.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">2. Objeto e Natureza do Produto</h2>
            <p>
              A <strong>Bússola Astrológica</strong> é um produto de cunho estritamente educacional, informativo e de
              desenvolvimento pessoal/autoconhecimento, concebido para fornecer orientações práticas sobre astrologia,
              trânsitos e fases pessoais com base no mapa astrológico do usuário.
            </p>
            <p>
              O conteúdo disponibilizado inclui videoaulas, apostilas em PDF, checklists, mapas e ferramentas digitais de
              consulta.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">3. Licença de Uso Individual e Intransferível</h2>
            <p>
              Ao efetuar o pagamento da inscrição, é concedida ao comprador uma licença de acesso pessoal, individual,
              não exclusiva e intransferível ao conteúdo da Bússola Astrológica.
            </p>
            <div className="rounded-xl border border-border/60 bg-card/20 p-4">
              <p className="font-semibold text-foreground">É estritamente proibido:</p>
              <ul className="mt-2 list-disc space-y-1 pl-6">
                <li>Compartilhar dados de acesso (login e senha) com terceiros, amigos ou familiares.</li>
                <li>Praticar compras coletivas, grupos de rateio ou redistribuição em fóruns ou redes sociais.</li>
                <li>Baixar vídeos para fins de revenda, clonagem ou exibição pública comercial.</li>
                <li>Reproduzir integral ou parcialmente os materiais e textos sem autorização prévia por escrito.</li>
              </ul>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">4. Pagamento e Formas de Quitação</h2>
            <p>
              O valor da inscrição na Bússola Astrológica é o indicado no momento da compra na página oficial de
              checkout. As formas aceitas incluem:
            </p>
            <ul className="list-disc space-y-2 pl-6">
              <li><strong>Cartão de crédito:</strong> com parcelamento em até 12x (sujeito às taxas da operadora) e liberação imediata.</li>
              <li><strong>PIX:</strong> com compensação instantânea e liberação de acesso imediata.</li>
              <li><strong>Boleto bancário:</strong> com prazo de compensação bancária de até 72 horas úteis.</li>
            </ul>
          </section>

          <section className="rounded-2xl border border-gold/30 bg-gold/5 p-6 sm:p-8">
            <div className="flex items-center gap-3 text-gold">
              <ShieldCheck className="h-6 w-6 shrink-0" />
              <h2 className="font-display text-xl font-bold text-foreground">5. Garantia Incondicional de 7 Dias</h2>
            </div>
            <p className="mt-3">
              Em total respeito ao Código de Defesa do Consumidor (Art. 49 da Lei nº 8.078/1990) e pelo compromisso com a
              qualidade do método, oferecemos uma <strong>Garantia Incondicional de 7 (sete) dias</strong> a contar da data de
              confirmação do pagamento.
            </p>
            <p className="mt-2">
              Se durante esse período você acessar o conteúdo e julgar que o produto não atendeu às suas expectativas,
              você poderá solicitar o reembolso integral de 100% do valor investido através da plataforma de pagamento ou
              pelo nosso suporte, sem perguntas ou burocracia.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">6. Propriedade Intelectual e Direitos Autorais</h2>
            <p>
              Todos os elementos da Bússola Astrológica — incluindo textos, metodologias, apostilas, ilustrações, marcas,
              logotipos, vídeos, sistemas e identidade visual — são propriedade intelectual exclusiva da{" "}
              <strong>Astrowake serviços de astrologia Ltda.</strong> e de <strong>Crassus Gobbi</strong>, protegidos pela
              Lei de Direitos Autorais (Lei nº 9.610/1998) e pela Lei de Propriedade Industrial (Lei nº 9.279/1996).
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">7. Limitação de Responsabilidade</h2>
            <p>
              A astrologia é uma ferramenta milenar de orientação simbólica, autoconhecimento e interpretação de ciclos. Os
              materiais fornecidos não constituem aconselhamento financeiro, jurídico, médico ou psicológico e não
              substituem a consulta com profissionais devidamente certificados em suas respectivas áreas.
            </p>
            <p>
              A tomada de decisões práticas e os resultados decorrentes de sua aplicação em sua vida pessoal ou
              profissional são de inteira responsabilidade do aluno.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">8. Suporte e Atendimento</h2>
            <p>
              Para dúvidas de acesso, suporte técnico ou questões financeiras, nosso canal oficial de atendimento está
              disponível via WhatsApp e e-mail:
            </p>
            <p className="font-medium text-foreground">
              WhatsApp de Atendimento: +55 (47) 9233-1247
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">9. Legislação Aplicável e Foro</h2>
            <p>
              Estes Termos de Uso são regidos e interpretados de acordo com as leis da República Federativa do Brasil. Para
              dirimir quaisquer controvérsias oriundas deste instrumento, fica eleito o Foro da Comarca da sede da empresa,
              com expressa renúncia a qualquer outro, por mais privilegiado que seja.
            </p>
          </section>
        </div>
      </main>

      {/* Rodapé da Página Legal */}
      <footer className="border-t border-border/40 py-8 text-center text-xs text-muted-foreground">
        <p>Astrowake serviços de astrologia Ltda. — CNPJ: 43.066.768/0001-70</p>
        <p className="mt-1">Todos os direitos reservados © 2026</p>
      </footer>
    </div>
  );
}
