# Header da página Bússola Astrológica

## O que será feito

Criar uma nova página em `/bussola` com um header (hero) inspirado no layout de referência, usando a imagem cósmica enviada como fundo — sem nenhum texto embutido na imagem.

## Layout do header

```
┌───────────────────────────────────────────────────────────┐
│  [ selo dourado ]                                         │
│  BÚSSOLA ASTROLÓGICA            (imagem: roda zodiacal    │
│  Pare de insistir em portas      dourada + planetas,      │
│  fechadas...                     lado direito)            │
│  parágrafo de apoio                                       │
│  linha de micro-benefício                                 │
│  [ QUERO ABRIR MINHAS PORTAS → ]                          │
│  Acesso imediato · 7 dias de garantia · R$67              │
└───────────────────────────────────────────────────────────┘
```

- Sem barra de navegação no topo — só o hero.
- Fundo: a imagem enviada cobrindo toda a seção, com véu em gradiente da esquerda (preto sólido → transparente) para o texto ficar legível e a bússola/planetas continuarem visíveis à direita.
- Coluna de texto alinhada à esquerda, ocupando ~50% no desktop.
- No mobile: imagem posicionada ao topo, texto centralizado abaixo com véu mais forte, CTA em largura total.

## Copy (exata)

- Kicker dourado: **BÚSSOLA ASTROLÓGICA**
- Título: "Pare de insistir em portas fechadas. **Aprenda a identificar quais estão abertas para você agora**, no dinheiro, no amor, na carreira e em outras **9 áreas** da sua vida…" — trechos em destaque dourado, resto em branco.
- Parágrafo: "Em vez de gastar energia tentando fazer acontecer a qualquer custo, descubra o que o seu próprio mapa está sinalizando, e aprenda a agir de acordo com o momento que está vivendo **AGORA** sem misticismo raso e com precisão de um relógio cósmico"
- Linha de apoio com ícone: "Sem precisar se tornar especialista em astrologia ou decorar centenas de símbolos"
- Botão: **QUERO ABRIR MINHAS PORTAS** → https://pay.hotmart.com/Q107238351O
- Rodapé do bloco: "Acesso imediato · 7 dias de garantia · R$67"

## Estilo

Mesmo sistema visual do projeto: preto profundo, dourado (`gold`, `gold-soft`, `text-gold-gradient`), display serifado Cormorant Garamond nos títulos e Manrope no corpo. Entrada suave com fade/slide (framer-motion), sem animações pesadas no mobile.

## Técnico

- Nova rota `src/routes/bussola.tsx` com `head()` próprio (title, description, og:title, og:description, og:type, twitter:card, og:image apontando para a imagem de fundo).
- Imagem enviada publicada via `lovable-assets` como `src/assets/bussola-hero.png.asset.json` e importada pelo pointer.
- Componente do hero em `src/components/bussola/hero-bussola.tsx`.
- CTA dispara os mesmos eventos de Pixel já usados (`InitiateCheckout` + evento custom com origem `hero_bussola`) antes de redirecionar ao checkout.
- Nenhuma alteração em `/`, `/vendas` ou `/obrigado`.
