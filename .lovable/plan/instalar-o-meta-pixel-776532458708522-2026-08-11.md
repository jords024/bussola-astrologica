# Instalar o Meta Pixel (776532458708522)

## O que será feito

1. **Carregar o pixel no site inteiro**
   - Inserir o script base do Meta Pixel no layout raiz, com o ID `776532458708522`.
   - Inclui também o `<noscript>` com a imagem de fallback.
   - O PageView padrão é disparado automaticamente no carregamento.

2. **PageView na página de captura (`/`)**
   - Garantir o disparo do `PageView` ao abrir a landing page (inclusive em navegação interna, já que o app é SPA).

3. **Evento `Lead` na página de obrigado (`/obrigado`)**
   - Disparar `fbq('track', 'Lead')` uma única vez quando a página de obrigado é carregada.
   - Proteção contra disparo duplicado em re-render.

## Detalhes técnicos

- Script base adicionado em `src/routes/__root.tsx` via a opção `scripts` do `head()` (roda no HTML inicial, antes da hidratação).
- Um helper pequeno (`src/lib/fbq.ts`) expõe `track(event, params)` com verificação de `window.fbq` para evitar erros no SSR.
- Em `src/routes/obrigado.tsx`: `useEffect` com ref de controle disparando `Lead`.
- Em `src/routes/index.tsx`: `useEffect` disparando `PageView` em montagem (evita PageView faltando quando o usuário volta pela navegação SPA).

## Validação

- Verificar no navegador que `window.fbq` existe e que as requisições para `facebook.com/tr` aparecem com `ev=PageView` na home e `ev=Lead` em `/obrigado`.
- Confirmação final pelo Meta Pixel Helper / Gerenciador de Eventos (do seu lado).
