export const DADOS_EMPRESA = {
  cnpj: "43.066.768/0001-70",
  razaoSocial: "Astrowake serviços de astrologia Ltda.",
  autor: "Crassus Gobbi",
  ano: new Date().getFullYear(),
};

export default function RodapeBussola() {
  return (
    <footer
      aria-label="Informações legais e rodapé"
      className="relative border-t border-border/40 bg-[oklch(0.06_0.02_265)] pb-24 pt-12 text-center text-xs text-muted-foreground sm:pb-28"
    >
      <div className="relative mx-auto max-w-4xl px-6">
        <div className="flex flex-col items-center gap-4">
          {/* Links legais que abrem páginas dedicadas em nova aba */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm font-medium">
            <a
              href="/politicas-de-privacidade"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-gold"
            >
              Políticas de Privacidade
            </a>
            <span className="text-border" aria-hidden>
              •
            </span>
            <a
              href="/termos-de-uso"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-gold"
            >
              Termos de Uso
            </a>
          </div>

          {/* Informações da Empresa / CNPJ / Razão Social */}
          <div className="mt-2 flex flex-col items-center gap-1.5 leading-relaxed text-muted-foreground/80">
            <p className="font-semibold text-foreground/90">{DADOS_EMPRESA.razaoSocial}</p>
            <p>CNPJ: {DADOS_EMPRESA.cnpj}</p>
            <p>
              {DADOS_EMPRESA.autor} — Todos os direitos reservados © {DADOS_EMPRESA.ano}
            </p>
          </div>

          {/* Aviso legal e de segurança */}
          <p className="mt-2 max-w-2xl text-[11px] leading-relaxed text-muted-foreground/60">
            Este produto não garante a obtenção de resultados financeiros ou pessoais milagrosos.
            Qualquer referência ao desempenho passado ou potencial de decisões com base em
            astrologia não é garantia de resultados futuros. Seus dados estão 100% seguros e
            protegidos.
          </p>
        </div>
      </div>
    </footer>
  );
}
