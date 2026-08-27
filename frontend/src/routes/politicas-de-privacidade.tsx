import { createFileRoute, Link } from "@tanstack/react-router";
import { ShieldCheck, ArrowLeft, Lock, Mail } from "lucide-react";

export const Route = createFileRoute("/politicas-de-privacidade")({
  head: () => ({
    meta: [
      { title: "Políticas de Privacidade — Bússola Astrológica | Astrowake" },
      {
        name: "description",
        content: "Políticas de Privacidade e Termos de Proteção de Dados da Astrowake serviços de astrologia Ltda.",
      },
    ],
  }),
  component: PoliticasDePrivacidadePage,
});

export default function PoliticasDePrivacidadePage() {
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
            <Lock className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Políticas de Privacidade
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
            <h2 className="font-display text-xl font-bold text-foreground">1. Informações Gerais e Controlador</h2>
            <p className="mt-3">
              A presente Política de Privacidade contém informações sobre coleta, uso, armazenamento, tratamento e
              proteção dos dados pessoais dos usuários e visitantes da <strong>Bússola Astrológica</strong>, com a
              finalidade de demonstrar absoluta transparência e segurança, em total conformidade com a Lei Geral de
              Proteção de Dados Pessoais (LGPD - Lei nº 13.709/2018) e o Marco Civil da Internet (Lei nº 12.965/2014).
            </p>
            <p className="mt-2">
              O presente site e serviço são operados pela empresa controladora de dados:{" "}
              <strong className="text-foreground">Astrowake serviços de astrologia Ltda.</strong>, pessoa jurídica de
              direito privado, inscrita no CNPJ sob o nº <strong>43.066.768/0001-70</strong>, sob responsabilidade de{" "}
              <strong>Crassus Gobbi</strong>.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">2. Dados Pessoais Coletados</h2>
            <p>Os dados pessoais coletados pela plataforma podem incluir:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>
                <strong>Dados cadastrais e de contato:</strong> Nome completo, endereço de e-mail, número de telefone /
                WhatsApp, CPF e endereço para emissão de nota fiscal.
              </li>
              <li>
                <strong>Dados de transação e pagamento:</strong> Informações de faturamento processadas de forma segura e
                criptografada pelos gateways oficiais parceiros (como Hotmart, Mercado Pago ou similares). A Astrowake
                não armazena números de cartão de crédito em seus servidores.
              </li>
              <li>
                <strong>Dados de navegação e conexão:</strong> Endereço IP, tipo de navegador, páginas visualizadas,
                horários de acesso e registros de cookies para melhoria da experiência de uso e prevenção a fraudes.
              </li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">3. Finalidades do Tratamento de Dados</h2>
            <p>Seus dados são coletados e tratados com as seguintes finalidades legítimas:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Liberação e envio imediato dos dados de acesso à plataforma da Bússola Astrológica.</li>
              <li>Comunicação sobre atualizações de conteúdo, suporte ao cliente e resolução de dúvidas.</li>
              <li>Emissão de notas fiscais e cumprimento de obrigações tributárias e fiscais.</li>
              <li>Prevenção a fraudes, segurança do ambiente digital e proteção contra cópia não autorizada.</li>
              <li>Envio de comunicações informativas e ofertas relevantes, sempre com opção de descadastro (opt-out) a qualquer momento.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">4. Base Legal para o Tratamento (LGPD)</h2>
            <p>O tratamento dos seus dados pessoais é realizado estritamente sob as seguintes bases legais previstas no art. 7º da LGPD:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li><strong>Execução de contrato:</strong> Para disponibilizar o produto adquirido e prestar o suporte correspondente (art. 7º, V).</li>
              <li><strong>Cumprimento de obrigação legal:</strong> Para emissão de documentos fiscais e registros de conexão (art. 7º, II).</li>
              <li><strong>Legítimo interesse:</strong> Para aprimoramento contínuo dos serviços e segurança (art. 7º, IX).</li>
              <li><strong>Consentimento do titular:</strong> Quando fornecido explicitamente para recebimento de comunicações (art. 7º, I).</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">5. Compartilhamento Seguro com Terceiros</h2>
            <p>
              A Astrowake não vende, aluga ou comercializa seus dados pessoais em hipótese alguma. O compartilhamento ocorre
              exclusivamente com provedores de infraestrutura essenciais para a operação, tais como:
            </p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Plataformas de pagamento e gestão de assinaturas (ex.: Hotmart).</li>
              <li>Provedores de hospedagem em nuvem e servidores de alta segurança.</li>
              <li>Ferramentas de disparo de e-mail transacional e atendimento via WhatsApp.</li>
              <li>Autoridades judiciais ou governamentais, exclusivamente mediante ordem judicial ou exigência legal.</li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">6. Cookies e Tecnologias de Monitoramento</h2>
            <p>
              Utilizamos cookies e identificadores anônimos para entender o comportamento de navegação, personalizar a
              experiência e mensurar a eficácia de nossas campanhas. Você pode configurar seu navegador para recusar
              cookies a qualquer momento, embora algumas funcionalidades do site possam ser limitadas.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className="font-display text-xl font-bold text-foreground">7. Direitos do Titular dos Dados</h2>
            <p>Conforme o art. 18 da LGPD, você possui o direito de solicitar a qualquer momento:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Confirmação da existência de tratamento dos seus dados.</li>
              <li>Acesso aos dados coletados.</li>
              <li>Correção de dados incompletos, inexatos ou desatualizados.</li>
              <li>Anonimização, bloqueio ou eliminação de dados desnecessários.</li>
              <li>Revogação do consentimento para recebimento de comunicações.</li>
            </ul>
          </section>

          <section className="rounded-2xl border border-border/60 bg-card/20 p-6 sm:p-8">
            <h2 className="font-display text-xl font-bold text-foreground">8. Canal de Contato e Encarregado (DPO)</h2>
            <p className="mt-3">
              Para exercer qualquer um dos seus direitos ou tirar dúvidas sobre o tratamento de seus dados, entre em
              contato diretamente com a nossa equipe de suporte e encarregado de proteção de dados através do e-mail oficial
              ou canal de atendimento no WhatsApp:
            </p>
            <div className="mt-4 flex flex-col gap-2 font-medium text-foreground">
              <p>Astrowake serviços de astrologia Ltda. — CNPJ: 43.066.768/0001-70</p>
              <p>WhatsApp de Suporte: +55 (47) 9233-1247</p>
            </div>
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
