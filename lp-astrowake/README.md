# LP Astrowake — encontro ao vivo do dia 15

Página de captação do encontro ao vivo do Crassus Gobbi. Site estático: nenhum
build, nenhuma dependência para instalar. Abrir o `index.html` já é o site.

> Esta pasta é independente das outras do repositório. Nem o `quiz/` (FastAPI)
> nem o `frontend/` (TanStack SSR) a servem automaticamente: para publicar, ou
> se aponta uma hospedagem estática para esta pasta, ou se copia o conteúdo para
> `quiz/publico/`, que o app serve em `/estatico/`.

## Arquivos

| Arquivo | O que é |
| --- | --- |
| `index.html` | A página inteira: conteúdo, CSS e o pop-up de inscrição |
| `interacao.js` | Camada de movimento (GSAP + ScrollTrigger): abertura do título, parallax, entrada das seções e a leitura guiada no celular |
| `inscricao.js` | O pop-up: máscara de telefone, validação, envio para o webhook e redirecionamento |
| `pixel.js` | O pixel da Meta nas duas páginas: `PageView` sempre, `Lead` só para quem veio do formulário |
| `config.js` | **O único arquivo que você precisa editar** |
| `obrigado.html` | Página de obrigado, cujo único trabalho é levar a pessoa para o grupo |
| `hero.webp` | Foto do topo |
| `autor-crassus.webp` | Retrato do final da página |

## O que precisa ser preenchido

Em `config.js`:

- **`WEBHOOK`** — a URL que recebe cada lead (Make, Zapier, n8n, Pabbly ou um
  endpoint próprio). Enquanto estiver vazia, o formulário continua funcionando e
  leva a pessoa até o grupo, mas **nenhum lead é registrado** — ele só aparece
  como aviso no console do navegador.
- **`GRUPO_WHATSAPP`** — o convite do grupo, que é o destino da página de
  obrigado. Já está preenchido.
- **`PIXEL`** — o número do pixel da Meta. Já está preenchido
  (`776532458708522`). Esta é a única cópia desse número no projeto: trocar
  aqui troca nas duas páginas, e nenhum evento sai para a conta errada por
  esquecimento.

## Como o lead chega no webhook

`POST` com corpo JSON:

```json
{
  "evento": "inscricao",
  "event_id": "61468fb6-2829-4917-baf6-a55857711b3a",
  "origem": "lp-astrowake",
  "nome": "Maria",
  "ddi": "55",
  "whatsapp": "+5511988887777",
  "whatsapp_formatado": "+55 (11) 98888-7777",
  "pagina": "https://.../index.html",
  "referrer": null,
  "utm": { "utm_source": "ig", "utm_campaign": "...", "fbclid": "..." },
  "fbp": "fb.1.1762790000000.1234567890",
  "fbc": "fb.1.1762790000000.IwAR...",
  "enviado_em": "2026-11-10T12:00:00.000Z"
}
```

O cabeçalho vai como `text/plain;charset=UTF-8` de propósito: isso mantém a
requisição no formato "simples" e evita a chamada `OPTIONS` de verificação, que
a maioria dos webhooks responde com erro. O corpo continua sendo JSON e Make,
Zapier e n8n leem normalmente. Se o seu endpoint exigir `application/json`,
troque em `inscricao.js` e libere CORS no servidor.

Se o envio falhar, a pessoa pode tentar de novo uma vez; na segunda falha ela é
levada para o grupo mesmo assim, porque segurar alguém na tela de erro não
recupera o lead e ainda perde a inscrição.

## O pixel da Meta

Pixel `776532458708522`, carregado nas duas páginas por `pixel.js`. Cada página
declara na própria tag do script o que dispara:

```html
<script src="pixel.js"></script>                       <!-- index.html: PageView -->
<script src="pixel.js" data-evento="lead"></script>    <!-- obrigado.html: PageView + Lead -->
```

**O `Lead` não dispara só por abrir a página de obrigado.** No envio, o
formulário cria um id aleatório de evento e o passa no endereço
(`obrigado.html?lead=...`); é a presença desse id que autoriza o disparo, e a
página limpa a barra depois de usar. Sem essa trava, cada visita direta — e cada
vez que alguém abrisse um link da página de obrigado compartilhado no grupo —
contaria como inscrição, e a campanha passaria a otimizar para gente que nunca
se cadastrou.

O mesmo id vai no `event_id` do webhook e no `eventID` do pixel. Isso existe
para o dia em que o `Lead` também for enviado pelo servidor (Conversions API):
a Meta reconhece que navegador e servidor falam do mesmo evento, em vez de
contar dois leads para uma pessoa. Os cookies `_fbp` e `_fbc` vão no webhook
pelo mesmo motivo — sem eles, um `Lead` de servidor não se liga ao anúncio.

Um F5 na página de obrigado não vira um segundo lead: o id já usado fica
marcado na sessão, e a Meta também junta eventos de mesmo nome e mesmo `eventID`
por 48h.

Duas coisas que **não** estão aqui, de propósito:

- **Correspondência avançada** (enviar nome e telefone à Meta para casar o lead
  com a conta da pessoa). Melhora atribuição e custa dado pessoal indo para a
  Meta — é decisão de quem assina, não default.
- **O `<noscript>` do snippet padrão da Meta.** Ele obrigaria uma segunda cópia
  do número do pixel, escrita à mão no HTML, e quem trocasse só o `config.js`
  passaria a mandar `PageView` para a conta antiga sem perceber. O que se perde
  é o `PageView` de quem navega sem JavaScript — gente que não consegue abrir o
  pop-up nem virar lead de qualquer forma.

## Rodar local

Precisa de um servidor, e não do arquivo aberto direto do disco — o
`sessionStorage` que carrega o nome até a página de obrigado não funciona em
`file://`:

```
python -m http.server 8791
```

Depois abrir http://localhost:8791

## Decisões que não são óbvias no código

- **O nome viaja em `sessionStorage`, nunca na URL.** Dado pessoal em endereço
  acaba em histórico, em log de servidor e em link compartilhado.
- **Nada de `transition` em CSS sobre as propriedades que o GSAP anima.** Duas
  engines escrevendo no mesmo `transform` dão aquele movimento emborrachado. Foi
  bug real aqui, nos cartões.
- **`fromTo`, nunca `from`.** Um `gsap.from()` anota o valor atual como destino,
  e com o CSS já em `opacity:0` o elemento anima de invisível para invisível.
- **O título dourado usa `background-clip:text` no próprio elemento animado**, e
  não em um ancestral: no Safari, glifo recortado do fundo de um ancestral
  desaparece quando o elemento ganha camada própria de composição.
- **Rede de segurança de 3s na abertura.** A animação de entrada é a única coisa
  que esconde texto; se ela não rodar (aba em segundo plano, aparelho fraco), a
  linha de tempo é levada ao fim na marra. Ninguém vê página em branco.
