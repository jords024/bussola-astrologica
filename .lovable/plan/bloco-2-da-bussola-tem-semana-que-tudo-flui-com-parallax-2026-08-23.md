# Bloco 2 da /bussola — "Tem semana que tudo flui" com parallax

Novo bloco logo abaixo do header da página `/bussola`, usando a imagem enviada como peça central, com o mesmo efeito de scroll suave (parallax GSAP + Lenis) já usado na landing page inicial.

## O que será feito

1. **Seção full-width** abaixo do `<HeroBussola />`, fundo preto profundo com leve halo dourado nas bordas para a imagem "derreter" no fundo (sem cortes duros).
2. **Imagem enviada** publicada no CDN de assets e exibida como peça visual central da seção, com máscara/gradiente nas bordas para integrar ao fundo preto.
3. **Parallax no scroll**: a imagem se move mais devagar que a página (deslocamento vertical suave + leve escala), enquanto o brilho dourado de fundo se move em velocidade diferente — cria profundidade e sofisticação, igual ao efeito da página de captura.
4. **Entrada elegante**: fade + subida suave quando a seção entra na viewport, com pequena defasagem entre o brilho e a imagem.

## Mobile

- Parallax com amplitude reduzida e apenas `transform`/`opacity` (sem reflow, sem blur pesado).
- Imagem responsiva, `loading="lazy"` e `decoding="async"`.
- `prefers-reduced-motion`: tudo estático, sem movimento.

## Detalhes técnicos

- Novo componente `src/components/bussola/bloco-tudo-flui.tsx`, integrado em `src/routes/bussola.tsx` depois do hero.
- Efeito via GSAP + ScrollTrigger (já instalados no projeto), com cleanup no unmount; mesma linguagem do parallax de `src/routes/index.tsx`.
- Imagem enviada vira `src/assets/bussola-tudo-flui.png.asset.json` via `lovable-assets` e é importada pelo pointer.
- Somente tokens existentes (gold, background) — nada de cor hardcoded. Sem mudanças em backend, tracking ou nas outras páginas.

## Ponto em aberto

A imagem já traz o texto embutido ("TEM SEMANA QUE TUDO FLUI" e os 4 cards). Vou usá-la como está. Se preferir, posso depois recriar esse texto em HTML por cima de uma versão limpa, para ficar nítido em qualquer tela e melhor para SEO.
