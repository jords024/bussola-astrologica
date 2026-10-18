/* SCROLL-LINKED IMAGE SEQUENCE.

   POR QUE SAIU O VIDEO E ENTRARAM QUADROS

   Prender a animacao ao scroll com um <video> nunca funcionou, e nao era
   ajuste fino: `video.currentTime = x` dispara um SEEK, que e assincrono,
   pode esperar rede e deixa `video.seeking` ligado por varios quadros.
   Medido na epoca: com o scroll em 60% do percurso o video estava em 1,07s
   de 10s. Rolar para tras era pior, porque cada mudanca de direcao
   cancelava o seek anterior.

   `ctx.drawImage(quadro)` nao tem nada disso: e sincrono e custa menos de um
   milissegundo. Com a sequencia em memoria, cada pixel de rolagem vira um
   quadro exato, para frente e para tras. E a tecnica que a Apple usa nas
   paginas de produto, e e a unica que entrega scrub de verdade.

   A BORDA
   O recorte da borda e feito DENTRO do canvas, com destination-out: desenha
   o quadro, depois apaga as beiradas com um gradiente radial. Como o
   gradiente usa as mesmas coordenadas do desenho, ele nunca sai de registro
   com a imagem. Foi esse descasamento que fez as tentativas com mask-image
   no CSS falharem: a mascara era calculada sobre a CAIXA do elemento, que
   nem sempre coincidia com a imagem dentro dela.                          */
(() => {
  const entrada = document.getElementById('cartaEntrada');
  const conteudo = document.getElementById('cartaConteudo');
  const pista = document.getElementById('motionTrack');
  const fixo = document.getElementById('motionSticky');
  const canvas = document.getElementById('garrafaCanvas');
  const botao = document.getElementById('abrirCarta');
  const dica = document.getElementById('motionHint');
  const secao = document.querySelector('[data-s="7"]');
  const semMovimento = matchMedia('(prefers-reduced-motion: reduce)');
  if (!canvas) return;
  const ctx = canvas.getContext('2d', { alpha: true });

  const TOTAL = 61;                       // f001..f061
  const LARGURA = 340, ALTURA = 544;      // tamanho nativo do quadro
  const CARTA_ENTRA = 0.80;               // a carta comeca a aparecer aqui
  const url = i => `/estatico/img/garrafa-seq/f${String(i + 1).padStart(3, '0')}.webp`;

  const quadros = new Array(TOTAL);
  let carregados = 0, pedido = false, ativo = false, entregue = null, chave = null;
  let laco = 0, alvo = 0, desenhado = -1;

  const limitar = n => Math.max(0, Math.min(1, n));
  const suave = t => t * t * (3 - 2 * t);

  /* ---------------------------------------------------------- carregar */
  function carregar() {
    if (pedido) return;
    pedido = true;
    for (let i = 0; i < TOTAL; i++) {
      const img = new Image();
      img.decoding = 'async';
      img.onload = () => {
        quadros[i] = img;
        carregados++;
        if (i === 0) { desenhado = -1; desenhar(0); }
        atualizarBotao();
      };
      img.onerror = () => { carregados++; atualizarBotao(); };
      img.src = url(i);
    }
  }
  /* Chamada por go() quando a pessoa chega no formulario. A sequencia pesa
     1,5 MB: baixar isso em toda visita, inclusive das que param na primeira
     tela, seria desperdicio. Daqui ate a carta sobram dezenas de segundos. */
  window.ritualCartaCarregar = carregar;

  function prontoBastante() { return carregados >= Math.floor(TOTAL * 0.9); }

  function atualizarBotao() {
    if (ativo) return;
    const ok = prontoBastante() || semMovimento.matches;
    botao.disabled = !ok;
    botao.textContent = ok ? 'Abrir a garrafa' : 'Preparando...';
  }
  /* Rede ruim nao prende ninguem num botao cinza. */
  setTimeout(() => { if (botao.disabled) { botao.disabled = false;
    botao.textContent = 'Abrir a garrafa'; } }, 12000);

  /* ----------------------------------------------------------- desenhar */
  function desenhar(p) {
    const i = Math.min(TOTAL - 1, Math.max(0, Math.round(p * (TOTAL - 1))));
    if (i === desenhado) return;
    const img = quadros[i] || quadros[desenhado] || quadros[0];
    if (!img) return;
    desenhado = i;

    ctx.clearRect(0, 0, LARGURA, ALTURA);
    ctx.globalCompositeOperation = 'source-over';
    ctx.drawImage(img, 0, 0, LARGURA, ALTURA);

    /* O RECORTE DA BORDA, UM GRADIENTE POR EIXO.

       A versao anterior usava UM gradiente radial com raio tirado da altura.
       Num quadro alto e estreito isso nunca funcionava: a meia-largura caia
       em 28% do raio, antes do primeiro ponto de fade, e as laterais ficavam
       100% opacas. Eram elas as duas arestas verticais do "quadrado preto".

       Dois gradientes lineares resolvem sem nenhuma matematica escondida:
       um apaga esquerda e direita, o outro apaga topo e pe. Onde os dois se
       cruzam, nos cantos, a erosao soma, e sai a vinheta de graca.

       As paradas so sao possiveis porque o enquadramento tem folga: o quadro
       guarda 27% de margem escura de cada lado da garrafa (medido). Com o
       corte anterior, colado no objeto, qualquer fade comia o vidro. */
    ctx.globalCompositeOperation = 'destination-out';

    const hx = ctx.createLinearGradient(0, 0, LARGURA, 0);
    hx.addColorStop(0,    'rgba(0,0,0,1)');
    hx.addColorStop(0.19, 'rgba(0,0,0,0)');
    hx.addColorStop(0.81, 'rgba(0,0,0,0)');
    hx.addColorStop(1,    'rgba(0,0,0,1)');
    ctx.fillStyle = hx;
    ctx.fillRect(0, 0, LARGURA, ALTURA);

    const vy = ctx.createLinearGradient(0, 0, 0, ALTURA);
    vy.addColorStop(0,    'rgba(0,0,0,1)');
    vy.addColorStop(0.09, 'rgba(0,0,0,0)');
    vy.addColorStop(0.80, 'rgba(0,0,0,0)');
    vy.addColorStop(1,    'rgba(0,0,0,1)');
    ctx.fillStyle = vy;
    ctx.fillRect(0, 0, LARGURA, ALTURA);

    ctx.globalCompositeOperation = 'source-over';
  }

  /* ------------------------------------------------------------- scroll */
  function progresso() {
    const percurso = Math.max(1, pista.offsetHeight - fixo.offsetHeight - 40);
    return limitar((48 - pista.getBoundingClientRect().top) / percurso);
  }

  function quadro() {
    if (!ativo) return;
    desenhar(alvo);

    /* A carta entra junto com o fim do percurso, e SAI se a pessoa voltar:
       o gesto e reversivel inteiro, inclusive a revelacao. */
    const entra = suave(limitar((alvo - CARTA_ENTRA) / (1 - CARTA_ENTRA)));
    if (entra > 0) {
      conteudo.hidden = false;
      conteudo.style.opacity = String(entra);
      conteudo.style.transform = `translateY(${(1 - entra) * 22}px)`;
    } else if (!conteudo.classList.contains('revelada')) {
      conteudo.hidden = true;
      conteudo.style.opacity = '';
      conteudo.style.transform = '';
    }
    canvas.style.opacity = String(1 - entra * 0.9);

    dica.textContent = alvo < 0.25 ? 'Continue descendo. A rolha está saindo.'
                     : alvo < 0.8  ? 'A sua carta está subindo pelo gargalo.'
                                   : 'Role mais um pouco para receber.';
  }

  /* O DESENHO ACONTECE DIRETO NO EVENTO DE SCROLL, SEM requestAnimationFrame.

     Parece ir contra a receita, mas rAF aqui era risco sem beneficio:
     ele NAO dispara em pagina que nao esta sendo pintada (aba em segundo
     plano, janela atras de outra), e entao o quadro simplesmente nunca era
     redesenhado. O navegador ja limita o evento de scroll a um por frame, e
     o trabalho de cada passada e um drawImage mais dois gradientes: menos de
     um milissegundo. Nao ha o que coalescer. */
  function aoRolar() {
    if (!ativo || !secao.classList.contains('on')) return;
    alvo = progresso();
    if (alvo >= 0.999) { entregar(); return; }
    quadro();
  }
  addEventListener('scroll', aoRolar, { passive: true });
  addEventListener('resize', () => { desenhado = -1; aoRolar(); }, { passive: true });

  /* ----------------------------------------------------------- entregar */
  function entregar() {
    ativo = false;
    cancelAnimationFrame(laco); laco = 0;
    entregue = chave;
    entrada.hidden = true;
    conteudo.hidden = false;
    conteudo.style.opacity = '';
    conteudo.style.transform = '';
    conteudo.classList.add('revelada');
    pista.classList.remove('motion-active');
    botao.setAttribute('aria-expanded', 'true');
    dica.textContent = '';
    document.getElementById('readTitle').focus({ preventScroll: true });
    secao.scrollIntoView({ block: 'start', behavior: 'instant' });
  }

  botao.addEventListener('click', () => {
    if (semMovimento.matches) { entregar(); return; }
    if (ativo) { entregar(); return; }      /* 2o toque entrega na hora */
    ativo = true;
    pista.classList.add('motion-active');
    botao.textContent = 'Abrir a carta agora';
    botao.setAttribute('aria-expanded', 'true');
    dica.textContent = 'Agora desça devagar.';
    /* NADA DE MOVER A TELA AQUI.

       Antes o clique dava um scrollTo suave ate o inicio do percurso, para
       garantir que a animacao comecasse no quadro zero. Na pratica a pessoa
       clicava e a pagina descia sozinha, o que e desagradavel e tira dela o
       controle que o gesto inteiro promete. O clique agora so arma: quem
       move a tela e ela. */
    alvo = progresso(); desenhado = -1; quadro();
  });

  /* ---------------------------------------------------------- preparar */
  window.ritualCartaPreparar = (novaChave, nome) => {
    ativo = false;
    cancelAnimationFrame(laco); laco = 0;
    chave = novaChave;
    pista.classList.remove('motion-active');
    const jaAberta = entregue === novaChave && novaChave != null;
    entrada.hidden = jaAberta;
    conteudo.hidden = !jaAberta;
    conteudo.classList.toggle('revelada', jaAberta);
    conteudo.style.opacity = ''; conteudo.style.transform = '';
    canvas.style.opacity = '';
    document.getElementById('cartaDestinatario').textContent =
      nome ? `Para ${nome}` : 'Uma mensagem para você';
    botao.setAttribute('aria-expanded', String(jaAberta));
    dica.textContent = '';
    alvo = 0; desenhado = -1;
    carregar();
    if (quadros[0]) desenhar(0);
    atualizarBotao();
  };

  new MutationObserver(() => {
    if (!secao.classList.contains('on')) {
      ativo = false; cancelAnimationFrame(laco); laco = 0;
      pista.classList.remove('motion-active');
    }
  }).observe(secao, { attributes: true, attributeFilter: ['class'] });
})();
