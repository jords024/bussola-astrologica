/* ============================================================
   ASTROWAKE · INTERACAO

   O QUE SAIU, E POR QUE

   Lenis: a inercia dele briga com `scroll-behavior:smooth` no
   html. Duas rolagens disputando a mesma pagina travam o
   scroll, e foi o que aconteceu. Em vez de remover o CSS e
   ficar com a dependencia, removi a dependencia: o scroll
   nativo do navegador nunca trava e o ScrollTrigger trabalha
   perfeitamente com ele.

   Secao fixada (pin): prender a tela por 140% da altura e o
   tipo de efeito que, quando o resto ja esta pesado, o visitante
   le como "a pagina travou". Saiu pelo mesmo motivo.

   Ceu de pontos ligados por linhas: parecia diagrama de atomo,
   nao carta celeste. Efeito que lembra outra coisa trabalha
   contra o assunto. Saiu inteiro.

   Fio de ouro descendo o fundo: cortava a pagina sem explicar
   por que estava ali. Saiu.

   Mandala do zodiaco girando: no desktop funcionava, no celular
   nao. Numa tela estreita ela ou invade o texto ou fica um arco
   solto no canto, sem leitura possivel. Saiu tambem.

   FICOU O MOVIMENTO DE SCROLL, que era o pedido: o titulo sobe
   linha por linha na abertura, a foto corre mais devagar que o
   texto, e cada secao entra quando chega na dobra.

   O QUE FICOU: o que serve a leitura, e so.
   ============================================================ */
(() => {
  'use strict';

  const parado = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Sem GSAP ou com movimento reduzido: entrega a pagina inteira,
     visivel e completa. Nunca uma versao capenga. */
  if (parado || typeof window.gsap === 'undefined') {
    document.documentElement.classList.add('sem-movimento');
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

  /* ---------------------------------------------------------
     1. ENTRADA DO HERO
     O titulo sobe linha por linha, cada uma saindo de dentro de
     uma mascara. E o unico momento coreografado da pagina. */
  const abertura = gsap.timeline({ defaults: { ease: 'power3.out' } })
    .to('.hero-foto', { opacity: 1, duration: 1.3 }, 0)
    .to('.linha-i',   { y: '0%', duration: 1, stagger: 0.08 }, 0.12)
    .to('.hero-fade', { opacity: 1, y: 0, duration: 0.85, stagger: 0.08 }, 0.5);

  /* Rede de seguranca: a abertura e a unica coisa que esconde
     texto, entao se por qualquer motivo ela nao rodar (aba em
     segundo plano, aparelho fraco, quadro perdido), o titulo
     fica invisivel. Em 3 segundos a linha de tempo e levada ao
     fim na marra. Ninguem nunca ve uma pagina em branco. */
  setTimeout(() => { if (abertura.progress() < 1) abertura.progress(1); }, 3000);

  /* ---------------------------------------------------------
     2. PARALLAX DO HERO
     A foto sobe mais devagar que o texto. A diferenca de
     velocidade e o que da profundidade, sem efeito aparente. */
  gsap.to('.hero-foto img', {
    yPercent: 9, ease: 'none',
    scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 0.5 }
  });

  /* ---------------------------------------------------------
     3. ENTRADA DAS SECOES
     18px e rapido. Movimento grande em bloco de texto atrasa a
     leitura em vez de enfeitar. */
  /* ATENCAO: os cartoes de "O que voce vai destravar" ficavam
     invisiveis. Eles tinham .sobe (que no CSS zera a opacidade)
     E um gsap.from() proprio. Um gsap.from() anota o valor atual
     como DESTINO, e o valor atual era zero, entao o cartao
     animava de invisivel para invisivel. Agora cada elemento tem
     uma animacao so, e todas sao .to(), que declara o destino em
     vez de adivinhar. */
  gsap.utils.toArray('.sobe:not(.card)').forEach(el => {
    gsap.to(el, {
      opacity: 1, y: 0, duration: 0.8, ease: 'power2.out',
      scrollTrigger: { trigger: el, start: 'top 88%', once: true }
    });
  });

  /* Os tres cartoes entram escalonados, sem prender a tela. */
  gsap.utils.toArray('.tres .card').forEach((c, i) => {
    gsap.to(c, {
      opacity: 1, y: 0, duration: 0.75, ease: 'power2.out', delay: i * 0.1,
      scrollTrigger: { trigger: '.tres', start: 'top 85%', once: true }
    });
  });

  /* Os itens da comunidade, um atras do outro. */
  gsap.utils.toArray('.item').forEach((el, i) => {
    gsap.from(el, {
      opacity: 0, y: 20, duration: 0.65, ease: 'power2.out', delay: (i % 5) * 0.07,
      scrollTrigger: { trigger: el, start: 'top 90%', once: true }
    });
  });

  /* ---------------------------------------------------------
     4. BOTAO MAGNETICO
     Custa pouco e e o detalhe que faz a pagina parecer feita a
     mao. So em ponteiro fino: no toque nao existe hover. */
  if (matchMedia('(pointer:fine)').matches) {

    /* O cartao sobe 5px no hover. Isso era uma CSS transition, e brigava
       com a animacao de entrada pela mesma propriedade. Agora e GSAP, com
       overwrite para que entrada e hover nunca escrevam juntos. */
    document.querySelectorAll('.tres .card').forEach(c => {
      const mover = y => gsap.to(c, { y, duration: 0.45, ease: 'power3.out', overwrite: 'auto' });
      c.addEventListener('pointerenter', () => mover(-5));
      c.addEventListener('pointerleave', () => mover(0));
    });

    /* O botao do formulario fica de fora: botao que foge do dedo
       dentro de um pop-up de cadastro atrapalha em vez de encantar. */
    document.querySelectorAll('.cta:not(.cta-bloco)').forEach(btn => {
      btn.addEventListener('pointermove', e => {
        const r = btn.getBoundingClientRect();
        gsap.to(btn, {
          x: (e.clientX - (r.left + r.width / 2)) * 0.22,
          y: (e.clientY - (r.top + r.height / 2)) * 0.3,
          duration: 0.5, ease: 'power3.out'
        });
      });
      btn.addEventListener('pointerleave', () => {
        gsap.to(btn, { x: 0, y: 0, duration: 0.7, ease: 'elastic.out(1,0.45)' });
      });
    });
  }

  /* ---------------------------------------------------------
     6. A LEITURA NO CELULAR
     So no celular, onde a grade de duas colunas nao cabe e a secao
     vira uma coluna de texto corrido.

     Duas coisas, as duas presas ao scroll (vao e voltam com o dedo,
     nao sao animacao que dispara uma vez e acaba):

     a) o fio do rotulo enche de ouro conforme a secao avanca, entao a
        pessoa sempre sabe onde esta dentro do argumento;
     b) cada paragrafo acende ao entrar na faixa de leitura. Nao e
        enfeite: num texto longo no celular, isso diz ONDE LER. E o que
        separa um texto conduzido de um monte de texto jogado na tela.

     Uso fromTo, e nao from, porque from pega o valor atual como destino
     e ja nos deu um bug assim nos cartoes. fromTo declara as duas pontas.

     O apagado e .5, nao menos: mesmo fora da faixa o texto continua
     legivel. E junto com a claridade vem um passo de 8px para cima, para
     o paragrafo parecer CHEGANDO e nao com defeito de renderizacao: so
     opacidade variando pode ser lido como pagina quebrada.
     Quem pediu menos movimento no sistema nao entra aqui. */
  if (matchMedia('(max-width:900px)').matches) {
    document.querySelectorAll('.manifesto').forEach(secao => {

      const rotulo = secao.querySelector('.sec-rotulo');
      if (rotulo) {
        gsap.fromTo(rotulo, { '--avanco': '0%' }, {
          '--avanco': '100%', ease: 'none',
          scrollTrigger: { trigger: secao, start: 'top 14%', end: 'bottom 72%', scrub: 0.3 }
        });
      }

      gsap.utils.toArray(secao.querySelectorAll('.manifesto-corpo > *')).forEach(el => {
        gsap.fromTo(el, { opacity: 0.5, y: 8 }, {
          opacity: 1, y: 0, ease: 'none',
          scrollTrigger: { trigger: el, start: 'top 96%', end: 'top 62%', scrub: 0.4 }
        });
      });
    });
  }

  /* As fontes mudam a altura do texto depois da montagem, e aí
     todo gatilho preso a uma posicao sai do lugar. */
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => ScrollTrigger.refresh());
  }
  addEventListener('load', () => ScrollTrigger.refresh());
})();
