# Ajustes no Hero

## 1. Copy nova
- Selo: "EVENTO AO VIVO E 100% GRATUITO • QUINTA ÀS 20H"
- Título em duas linhas: "ASTROWAKE:" (branco) / "Hackeando a Realidade" (dourado)
- Parágrafo: "Um encontro ao vivo para você acessar as instruções da sua alma através de uma tecnologia milenar e nunca mais jogar a vida no **Modo Difícil**." + "Entenda suas emoções e tome decisões com total **CONSCIÊNCIA**, sem misticismo raso e sem decoreba."
- Barra de data: "Nesta quinta-feira" • "20h • Horário de Brasília"
- Checklist com os 3 novos itens (Carreira & Escolhas / Relações Pessoais / Direção de Vida), cada um com título em negrito + descrição
- Botão: "QUERO PARTICIPAR"

## 2. Tipografia do título
Trocar a fonte display serifada por sans-serif pesada (Manrope/Archivo, peso 800, tracking negativo, line-height apertado), como na referência: "ASTROWAKE:" em caixa alta branca e "Hackeando a Realidade" em dourado sólido (sem itálico, sem gradiente).

## 3. Imagem do Crassus mais visível
- Reduzir o escurecimento: substituir o gradiente `from-background via-background/85 to-background/30` por um véu lateral mais curto (preto forte só até ~40% da largura, transparente do centro para a direita), mantendo legibilidade do texto.
- Tirar/atenuar o gradiente vertical de topo/base e o glow radial dourado que lavam a foto.
- Posicionar a imagem à direita (`object-right`) com altura total, deixando o rosto e o fundo cósmico aparentes como na referência; texto ocupando ~50% à esquerda.
- Ajustar o padding vertical para o hero ocupar a tela cheia (min-h-screen) com o enquadramento da referência.

## 4. Mobile
No mobile a foto fica atrás do texto com um véu preto mais forte para garantir contraste.

## Técnico
Alterações restritas a `src/routes/index.tsx` (markup/classes do hero) e, se necessário, um token de fonte em `src/styles.css` para o peso extra-bold do título.
