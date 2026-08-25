# Bloco 2 — O Custo Invisível

Novo bloco na página de vendas (`/vendas`), logo abaixo do Bloco 1, com o texto completo organizado em camadas visuais para não virar "parede de texto".

## Estrutura visual

1. **Abertura**
   - Título: "O Custo Invisível de Passar a Vida Inteira Tentando Adivinhar o Caminho Certo" (display, dourado no trecho-chave).
   - Parágrafo do "padrão" + pergunta final destacada em itálico dourado suave.

2. **A Ilusão do Esforço**
   - Subtítulo com filete dourado à esquerda.
   - Frases curtas ("Então você dobrou a aposta.") isoladas, com respiro maior — ritmo de leitura.
   - A frase do "abismo" em bloco de citação: borda dourada à esquerda, fundo levemente elevado.
   - Frase-ponte introduzindo os três pilares, centralizada, com separador ornamental (linha + ponto dourado).

3. **Os 3 Pilares** — três cards em coluna (empilhados, largura de leitura), cada um com:
   - Etiqueta "PILAR 01/02/03" + ícone (carteira / coração / mente) em círculo dourado.
   - Título do pilar e subtítulo.
   - Corpo em parágrafos curtos.
   - Pilar 1 inclui a lista de 3 perguntas com marcador dourado (removendo a linha duplicada "Devo mudar de área…" que aparece repetida no texto).
   - Fecho de cada pilar em destaque (texto realçado com fundo sutil / borda superior fina).
   - Cards com fundo `card`, borda dourada de baixa opacidade, cantos arredondados e leve glow.

4. **O Confronto Final**
   - Seção mais dramática: fundo com vinheta radial dourada bem discreta.
   - Título, parágrafos, e a frase "você precisa de um mapa" em destaque grande.
   - Fecho: "É exatamente aqui que entra a virada de chave do Astrowake." em dourado.

5. **CTA**
   - Botão dourado full-width (mesmo estilo do Bloco 1): "CHEGA DE VIVER NO ESCURO • QUERO DESTRAVAR MINHA VIDA".
   - Abaixo, com cadeado: "Acesso Completo ao Método Astrowake • 7 Dias de Garantia Incondicional".
   - Dispara os mesmos eventos de pixel do CTA existente, com origem `bloco2_custo_invisivel`.

## Notas de conteúdo

O texto enviado tem dois trechos duplicados (o parágrafo "Quando você não conhece o seu próprio funcionamento…" e a pergunta "Devo mudar de área…", além do parágrafo do "silêncio na hora do jantar"). Vou manter apenas uma ocorrência de cada.

## Técnico

- Arquivo novo `src/components/vendas/bloco-custo-invisivel.tsx`, importado em `src/routes/vendas.tsx` abaixo do Bloco 1.
- `framer-motion` com `whileInView` (reveal em cascata), respeitando o `EASE` já usado.
- Ícones do `lucide-react`; apenas tokens do design system (gold, card, muted-foreground) — sem cores hardcoded.
- Responsivo: tipografia escalonada, cards com padding menor no mobile.
