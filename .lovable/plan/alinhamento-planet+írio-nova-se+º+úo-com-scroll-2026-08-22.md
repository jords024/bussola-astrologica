# Alinhamento Planetário — nova seção com scroll

Nova seção na página de vendas (`/vendas`), abaixo do Bloco 2, com a mesma linguagem do efeito de scroll atual: os planetas entram desalinhados e vão se **alinhando verticalmente** conforme o usuário desce, com o sol laranja estourado no topo, exatamente no clima da imagem de referência.

## Como funciona

1. **Sol no topo**: arco de luz quente (laranja/dourado) com halo suave, fixo no topo da seção, sem imagem pesada — puro CSS/gradiente, custo zero de rede.
2. **Planetas**: recortados da imagem enviada, cada um virando um sprite próprio (Mercúrio → Netuno, incluindo Terra+Lua, Júpiter e Saturno com anel). Ficam hospedados no CDN de assets.
3. **Animação de alinhamento**: no início da seção cada planeta está deslocado lateralmente (uns à esquerda, outros à direita), com rotação leve, escala menor e opacidade parcial. Conforme o scroll avança dentro da seção, todos convergem para o eixo central vertical, ganham escala e nitidez até formarem a coluna perfeita da referência.
4. **Linha de conexão**: um fio luminoso vertical (dourado, bem discreto) que "cresce" de cima para baixo conforme o alinhamento acontece, ligando o sol ao último planeta — a conexão entre eles.
5. **Copy mínima**: um título curto e uma linha de apoio ao lado do alinhamento (texto definido junto com você depois; por padrão fica apenas o visual, sem poluir).

## Otimização mobile (prioridade)

- Animação dirigida por um único listener de scroll com `requestAnimationFrame` e `transform`/`opacity` apenas (sem layout/reflow, sem `filter` animado).
- Sem `backdrop-blur` e sem sombras pesadas no mobile.
- Planetas em WebP com tamanhos reduzidos, `loading="lazy"` e `decoding="async"`.
- Deslocamentos e rotações menores no mobile, transição mais curta; `prefers-reduced-motion` mostra tudo já alinhado, estático.
- Observer que desliga o cálculo quando a seção sai da viewport.

## Detalhes técnicos

- Recorte dos planetas da imagem enviada com PIL, exportando PNGs com transparência e subindo via `lovable-assets` (pointers em `src/assets/planetas/*.asset.json`).
- Novo componente `src/components/vendas/alinhamento-planetario.tsx`, com hook local de progresso (`0→1`) baseado em `getBoundingClientRect()` da seção.
- Integração em `src/routes/vendas.tsx` após `<BlocoCustoInvisivel />`.
- Tokens existentes (gold/background) — nada de cor hardcoded. Nenhuma mudança em backend, tracking ou copy existente.
