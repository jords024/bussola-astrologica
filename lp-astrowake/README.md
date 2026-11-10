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

## Como o lead chega no webhook

`POST` com corpo JSON:

```json
{
  "evento": "inscricao",
  "origem": "lp-astrowake",
  "nome": "Maria",
  "whatsapp": "+5511988887777",
  "whatsapp_formatado": "(11) 98888-7777",
  "pagina": "https://.../index.html",
  "referrer": null,
  "utm": { "utm_source": "ig", "utm_campaign": "..." },
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
