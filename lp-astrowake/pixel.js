/* ============================================================
   ASTROWAKE · PIXEL DA META

   Um arquivo para as duas paginas. Cada pagina declara, na propria
   tag do script, o que ela dispara:

     <script src="pixel.js"></script>
       -> so PageView. E a pagina de captura.

     <script src="pixel.js" data-evento="lead"></script>
       -> PageView e Lead. E a pagina de obrigado.

   O numero do pixel fica em config.js. Nao existe outra copia dele
   no projeto, nem aqui dentro: trocar o numero la troca em tudo, e
   nenhum evento sai para o pixel errado por esquecimento.
   ============================================================ */
(() => {
  'use strict';

  const CFG = window.ASTROWAKE || {};
  const ID  = String(CFG.PIXEL || '').trim();

  /* Lido AGORA, enquanto o script executa: document.currentScript so
     existe durante a execucao sincrona, e some depois. */
  const DISPARA_LEAD = !!(document.currentScript &&
                          document.currentScript.dataset.evento === 'lead');

  if (!ID) {
    console.warn('[Astrowake] PIXEL vazio em config.js. Nenhum evento sera enviado.');
    return;
  }

  /* ---------------------------------------------------------
     O CARREGADOR

     Snippet oficial da Meta. Ele cria a fila fbq() na hora e baixa o
     fbevents.js de forma assincrona (t.async), entao os eventos abaixo
     podem ser chamados imediatamente, ficam na fila, e saem quando a
     biblioteca chega. O pixel nunca atrasa a primeira pintura. */
  !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
  n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}
  (window,document,'script','https://connect.facebook.net/en_US/fbevents.js');

  fbq('init', ID);
  fbq('track', 'PageView');

  if (!DISPARA_LEAD) return;

  /* ---------------------------------------------------------
     O LEAD

     Dispara so para quem chegou pelo formulario. O formulario cria um
     id de evento no momento do envio e o passa no endereco (?lead=...),
     e e a presenca desse id que autoriza o disparo.

     Sem essa trava, qualquer visita direta a pagina de obrigado contaria
     como inscricao - inclusive cada vez que alguem abrisse um link dela
     compartilhado no grupo. A campanha passaria a otimizar para gente
     que nunca se cadastrou, que e o jeito mais caro de errar.

     O id nao e dado pessoal: e um numero aleatorio, criado no envio. Ele
     existe para a Meta reconhecer o MESMO evento caso um dia o webhook
     tambem mande o Lead pelo servidor (Conversions API) - o payload do
     webhook ja leva esse id no campo event_id. Sem ele seriam dois
     leads para uma pessoa. */
  const id = new URLSearchParams(location.search).get('lead');
  if (!id) return;

  /* F5 nao vira um segundo lead. A Meta ja junta eventos de mesmo nome
     com mesmo eventID por 48h, e esta trava evita ate a ida. */
  let jaFoi = false;
  try { jaFoi = sessionStorage.getItem('astrowake_lead_enviado') === id; } catch (e) {}
  if (jaFoi) return;

  fbq('track', 'Lead',
      { content_name: 'Encontro ao vivo do dia 15' },
      { eventID: id });

  try { sessionStorage.setItem('astrowake_lead_enviado', id); } catch (e) {}

  /* Tira o id da barra depois de usar, para que o endereco que a pessoa
     copiar nao carregue o evento dela junto. */
  try {
    history.replaceState(null, '', location.pathname + location.hash);
  } catch (e) {}
})();
