/* ============================================================
   ASTROWAKE · CAPTURA DE LEAD

   O caminho inteiro: a pessoa clica em qualquer botao da pagina,
   abre o pop-up, preenche nome e WhatsApp, os dados vao para o
   webhook e ela cai na pagina de obrigado, que so tem um trabalho,
   que e colocar ela dentro do grupo.

   Tudo que voce precisa editar esta em config.js.
   ============================================================ */
(() => {
  'use strict';

  const CFG = window.ASTROWAKE || {};
  const modal   = document.getElementById('modal-inscricao');
  const form    = document.getElementById('form-inscricao');
  if (!modal || !form) return;

  const campoNome = document.getElementById('in-nome');
  const campoDdi  = document.getElementById('in-ddi');
  const campoZap  = document.getElementById('in-whatsapp');
  const botao     = document.getElementById('btn-enviar');
  const aviso     = document.getElementById('form-aviso');

  let quemAbriu = null;   // para devolver o foco ao fechar
  let enviando  = false;
  let falhas    = 0;

  /* ---------------------------------------------------------
     ABRIR E FECHAR

     Todo botao .cta da pagina passa a abrir o pop-up. Antes eles
     apontavam para #inscricao, uma ancora que nao existia: clicar
     nao fazia absolutamente nada. */
  document.querySelectorAll('.cta:not(.cta-bloco)').forEach(btn => {
    btn.addEventListener('click', e => { e.preventDefault(); abrir(btn); });
  });

  function abrir(origem) {
    quemAbriu = origem || null;
    modal.dataset.aberto = '1';
    travarFundo(true);
    /* O foco espera a transicao comecar, senao o navegador rola a pagina
       atras do pop-up para "mostrar" o input. Timer e nao quadro de
       animacao: quadro nao roda em aba em segundo plano, e ai o foco
       nunca chegaria no campo. */
    setTimeout(() => campoNome.focus({ preventScroll: true }), 60);
  }

  function fechar() {
    if (enviando) return;            // no meio do envio, nao some com a tela
    modal.dataset.aberto = '0';
    travarFundo(false);
    if (quemAbriu) quemAbriu.focus({ preventScroll: true });
  }

  /* O body desta pagina tem overflow:hidden auto. Guardo o valor e
     devolvo depois, em vez de chutar um padrao e quebrar o scroll. */
  let overflowAnterior = null;
  function travarFundo(travar) {
    if (travar) {
      overflowAnterior = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = overflowAnterior || '';
    }
  }

  modal.querySelectorAll('[data-fechar]').forEach(el => {
    el.addEventListener('click', fechar);
  });

  document.addEventListener('keydown', e => {
    if (modal.dataset.aberto !== '1') return;
    if (e.key === 'Escape') { fechar(); return; }
    if (e.key === 'Tab') prenderFoco(e);
  });

  /* Com o pop-up aberto, o Tab nao pode passear pela pagina atras
     dele: quem usa teclado ou leitor de tela ficaria perdido. */
  function prenderFoco(e) {
    const focaveis = modal.querySelectorAll(
      'button, input, [href], select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (!focaveis.length) return;
    const primeiro = focaveis[0], ultimo = focaveis[focaveis.length - 1];
    if (e.shiftKey && document.activeElement === primeiro) {
      e.preventDefault(); ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault(); primeiro.focus();
    }
  }

  /* ---------------------------------------------------------
     O CAMPO DE WHATSAPP

     Mascara brasileira ou internacional conforme o DDI. */
  function mascara(valor) {
    const d = valor.replace(/\D/g, '').slice(0, 11);
    if (!d.length) return '';
    if (d.length <= 2)  return '(' + d;
    if (d.length <= 6)  return '(' + d.slice(0, 2) + ') ' + d.slice(2);
    if (d.length <= 10) return '(' + d.slice(0, 2) + ') ' + d.slice(2, 6) + '-' + d.slice(6);
    return '(' + d.slice(0, 2) + ') ' + d.slice(2, 7) + '-' + d.slice(7);
  }

  function mascaraInternacional(valor) {
    const d = valor.replace(/\D/g, '').slice(0, 15);
    if (!d.length) return '';
    if (d.length <= 4) return d;
    if (d.length <= 8) return d.slice(0, 4) + ' ' + d.slice(4);
    if (d.length <= 12) return d.slice(0, 4) + ' ' + d.slice(4, 8) + ' ' + d.slice(8);
    return d.slice(0, 4) + ' ' + d.slice(4, 8) + ' ' + d.slice(8, 12) + ' ' + d.slice(12);
  }

  if (campoDdi) {
    campoDdi.addEventListener('change', () => {
      const isBr = campoDdi.value === '55';
      if (isBr) {
        campoZap.placeholder = '(00) 00000-0000';
        campoZap.maxLength = 16;
        campoZap.value = mascara(campoZap.value);
      } else {
        campoZap.placeholder = 'Número do WhatsApp';
        campoZap.maxLength = 19;
        campoZap.value = mascaraInternacional(campoZap.value);
      }
      limparErro('whatsapp');
    });
  }

  campoZap.addEventListener('input', () => {
    const isBr = !campoDdi || campoDdi.value === '55';
    const naPonta = campoZap.selectionStart === campoZap.value.length;
    campoZap.value = isBr ? mascara(campoZap.value) : mascaraInternacional(campoZap.value);
    if (naPonta) campoZap.setSelectionRange(campoZap.value.length, campoZap.value.length);
    limparErro('whatsapp');
  });
  campoNome.addEventListener('input', () => limparErro('nome'));

  /* ---------------------------------------------------------
     VALIDACAO
     Mensagem sempre diz O QUE fazer, nunca so "invalido". */
  function digitos(v) { return v.replace(/\D/g, ''); }

  function validar() {
    let ok = true;

    const nome = campoNome.value.trim();
    if (nome.length < 2) {
      marcarErro('nome', 'Escreva o seu nome para eu saber como te chamar.');
      ok = false;
    }

    const ddi = campoDdi ? campoDdi.value : '55';
    const d = digitos(campoZap.value);

    if (ddi === '55') {
      if (d.length < 10) {
        marcarErro('whatsapp', 'Faltam números. Use DDD mais o número, como (11) 98888-7777.');
        ok = false;
      } else if (Number(d.slice(0, 2)) < 11) {
        marcarErro('whatsapp', 'Esse DDD não existe. Confira os dois primeiros números.');
        ok = false;
      } else if (d.length === 11 && d[2] !== '9') {
        marcarErro('whatsapp', 'Celular com 11 números começa com 9 depois do DDD.');
        ok = false;
      }
    } else {
      if (d.length < 6) {
        marcarErro('whatsapp', 'Número incompleto. Digite o número com o código de área.');
        ok = false;
      }
    }

    /* O foco vai para o primeiro campo com problema, senao a pessoa
       precisa cacar sozinha o que deu errado. */
    if (!ok) {
      const primeiro = form.querySelector('.campo[data-erro] input');
      if (primeiro) primeiro.focus();
    }
    return ok;
  }

  function marcarErro(qual, texto) {
    const campo = form.querySelector('.campo[data-campo="' + qual + '"]');
    if (!campo) return;
    campo.setAttribute('data-erro', '');
    campo.querySelector('.campo-erro').textContent = texto;
  }

  function limparErro(qual) {
    const campo = form.querySelector('.campo[data-campo="' + qual + '"]');
    if (!campo) return;
    campo.removeAttribute('data-erro');
    campo.querySelector('.campo-erro').textContent = '';
  }

  /* ---------------------------------------------------------
     DE ONDE VEIO ESSA PESSOA
     Vai junto no webhook. Sem isso, rodando anuncio, nao da para
     saber qual criativo trouxe qual lead. */
  function origemDaVisita() {
    const p = new URLSearchParams(location.search);
    const utm = {};
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'fbclid', 'gclid']
      .forEach(k => { const v = p.get(k); if (v) utm[k] = v; });
    return utm;
  }

  /* ---------------------------------------------------------
     ENVIO */
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (enviando) return;
    esconderAviso();
    if (!validar()) return;

    const nomeLimpo = campoNome.value.trim();
    const ddi = campoDdi ? campoDdi.value : '55';
    const d = digitos(campoZap.value);
    const numeroE164 = '+' + ddi + d;
    const formatado = ddi === '55' ? ('+55 ' + campoZap.value) : ('+' + ddi + ' ' + campoZap.value);

    const dados = {
      evento: 'inscricao',
      event: 'inscricao',
      event_type: 'inscricao',
      origem: CFG.ORIGEM || 'lp-astrowake',
      nome: nomeLimpo,
      name: nomeLimpo,
      first_name: nomeLimpo.split(' ')[0],
      ddi: ddi,
      whatsapp: numeroE164,              // formato internacional padrao E.164
      phone: numeroE164,
      whatsapp_formatado: formatado,
      pagina: location.origin + location.pathname,
      referrer: document.referrer || null,
      utm: origemDaVisita(),
      enviado_em: new Date().toISOString()
    };

    marcarEnviando(true);

    const deuCerto = await mandarParaWebhook(dados);

    if (deuCerto) {
      concluir(dados.nome);
      return;
    }

    /* Falhou. Primeira vez: deixa tentar de novo, porque a maioria das
       falhas e oscilacao de rede e some na segunda. Segunda vez: para
       de insistir e abre a porta, porque segurar a pessoa aqui nao
       recupera o lead e ainda perde a inscricao. */
    falhas++;
    marcarEnviando(false);
    if (falhas < 2) {
      mostrarAviso('Não consegui registrar agora. Toque no botão para tentar de novo.');
    } else {
      mostrarAviso('A conexão falhou duas vezes. Vou te levar para o grupo mesmo assim.');
      setTimeout(() => concluir(dados.nome), 1800);
    }
  });

  async function mandarParaWebhook(dados) {
    /* Sem webhook configurado o fluxo continua inteiro, so que sem
       enviar nada. Assim da para testar tudo antes de ter o endpoint. */
    if (!CFG.WEBHOOK) {
      console.warn('[Astrowake] WEBHOOK vazio em config.js. O lead NAO foi enviado:', dados);
      return true;
    }

    const corta = new AbortController();
    const relogio = setTimeout(() => corta.abort(), CFG.TIMEOUT_MS || 8000);

    try {
      const r = await fetch(CFG.WEBHOOK, {
        method: 'POST',
        mode: 'no-cors',
        /* text/plain de proposito: deixa a requisicao no formato
           "simples", sem a chamada OPTIONS de verificacao que a maioria
           dos webhooks responde com erro. O corpo continua sendo JSON e
           Make, Zapier, n8n e ZapVoice leem normalmente. */
        headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        body: JSON.stringify(dados),
        signal: corta.signal
      });
      clearTimeout(relogio);
      // Em modo no-cors o navegador retorna r.type === 'opaque' (sem bloqueio de CORS),
      // garantindo que a requisicao foi enviada ao servidor com sucesso.
      return r.ok || r.type === 'opaque';
    } catch (err) {
      clearTimeout(relogio);
      console.error('[Astrowake] falha ao enviar o lead:', err);
      return false;
    }
  }

  function concluir(nome) {
    /* O nome viaja na sessao, nao na URL: dado pessoal em endereco
       acaba em historico, em log de servidor e em link compartilhado. */
    try { sessionStorage.setItem('astrowake_nome', nome); } catch (e) {}
    location.href = CFG.DESTINO || 'obrigado.html';
  }

  function marcarEnviando(estado) {
    enviando = estado;
    botao.disabled = estado;
    modal.dataset.enviando = estado ? '1' : '0';
    botao.querySelector('.btn-texto').textContent =
      estado ? 'Enviando' : 'Quero garantir minha vaga';
  }

  function mostrarAviso(texto) { aviso.textContent = texto; aviso.hidden = false; }
  function esconderAviso()     { aviso.textContent = '';    aviso.hidden = true;  }
})();
