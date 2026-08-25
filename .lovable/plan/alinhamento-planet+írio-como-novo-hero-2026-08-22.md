# Alinhamento planetário como novo hero

O topo da página de vendas passa a ser o alinhamento de planetas: sol estourado no alto, planetas entrando desalinhados e convergindo para a coluna vertical conforme o scroll — com a copy "ASTROWAKE / O despertar de um conhecimento ancestral...." por cima. A cena 3D (montanhas, estrelas, sol Three.js) sai.

## Como fica

1. **Hero em 3 fases preservadas**: continua a mesma narrativa de scroll com os títulos e subtítulos atuais (ASTROWAKE → LABIRINTO → RUMO) e o indicador "Desça para acessar as instruções da sua alma".
2. **Fundo**: preto profundo com o sol dourado no topo (puro CSS, sem imagem pesada), e a coluna de planetas ocupando o eixo central da tela.
3. **Movimento por scroll**: no início da página os planetas estão espalhados lateralmente, rotacionados e opacos; conforme o usuário desce eles se alinham em cascata, ganham nitidez e a linha dourada de conexão cresce do sol até o último planeta.
4. **Copy legível**: véu escuro suave atrás do texto para o título não competir com os planetas; no mobile, planetas menores e mais concentrados nas bordas para deixar o centro livre.
5. **Seção duplicada removida**: a seção "Quando tudo se alinha, a vida para de parecer um acaso" (depois do Bloco 2) sai da página; o efeito passa a existir só no topo.

## Otimização mobile

- Somente `transform`/`opacity` num único listener de scroll com `requestAnimationFrame`; sem WebGL, sem `filter` animado, sem `backdrop-blur`.
- Planetas em WebP leves já hospedados, `decoding="async"`.
- `prefers-reduced-motion`: tudo já alinhado, estático.
- Remoção do Three.js do hero reduz bastante o custo de scroll em celulares fracos.

## Detalhes técnicos

- Novo `src/components/vendas/hero-alinhamento.tsx`: reaproveita a lógica de progresso e os sprites de `alinhamento-planetario.tsx`, mas com camada fixa (`fixed inset-0`) + seções de altura `100svh` para dirigir o scroll, no mesmo modelo do `horizon-hero-section.tsx` (títulos por fase, indicador, pontos de progresso).
- `src/routes/vendas.tsx`: substitui o `lazy(HorizonHero)` pelo novo hero e remove `<AlinhamentoPlanetario />`.
- `src/components/ui/horizon-hero-section.tsx` e `src/components/vendas/alinhamento-planetario.tsx` deixam de ser usados e são removidos; o pacote `three` sai do bundle se não houver outro uso.
- Sem mudanças em copy dos demais blocos, tracking, formulário ou backend. Cores só por tokens (`--gold`, `--gold-soft`, `--gold-deep`, `--background`).
