/* ============================================================
   ASTROWAKE · CONFIGURACAO

   AS TRES UNICAS COISAS QUE VOCE PRECISA PREENCHER.
   Elas valem para a pagina de inscricao e para a de obrigado,
   entao mexa so aqui. Nenhum outro arquivo precisa ser tocado.
   ============================================================ */
window.ASTROWAKE = {

  /* 1. O WEBHOOK que recebe cada lead.
        Cole a URL entre as aspas. Serve qualquer um que aceite POST:
        Make, Zapier, n8n, Pabbly, ou um endpoint seu.

        Enquanto estiver vazio, o formulario continua funcionando e
        leva a pessoa para a pagina de obrigado, so que sem enviar
        nada e avisando no console. Da para testar o fluxo inteiro
        antes de ter o webhook pronto. */
  WEBHOOK: 'https://zapvoicecrassos.aryaraj.shop/api/webhooks/blazkfriday-astrowake-landingpage',

  /* 2. O PIXEL da Meta (Facebook/Instagram). So o numero.

        Vale para as duas paginas: a de captura dispara PageView e a de
        obrigado dispara PageView e Lead. Esta e a UNICA copia desse
        numero no projeto: trocar aqui troca em tudo.

        Vazio: nenhum evento e enviado, e o console avisa. */
  PIXEL: '776532458708522',

  /* 3. O LINK DO GRUPO de WhatsApp, que e o destino da pagina de
        obrigado. Aquele endereco chat.whatsapp.com/XXXX do convite. */
  GRUPO_WHATSAPP: 'https://chat.whatsapp.com/Cx8cg7EFczY69kc0dwKjdC?s=sh&p=a&iam=2',


  /* --------------------------------------------------------
     Daqui para baixo quase nunca muda. */

  /* Para onde a pessoa vai depois de se inscrever. */
  DESTINO: 'obrigado.html',

  /* Identifica de onde veio o lead, caso um dia exista mais de uma
     pagina mandando para o mesmo webhook. */
  ORIGEM: 'lp-astrowake',

  /* Quanto tempo esperar o webhook antes de considerar que falhou.
     Oito segundos: acima disso a pessoa acha que travou. */
  TIMEOUT_MS: 8000
};
