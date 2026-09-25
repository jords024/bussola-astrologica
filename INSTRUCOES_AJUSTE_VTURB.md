# Diagnóstico e Instruções para Correção do Player VSL (turb-front.aryaraj.shop)

Este documento contém todo o contexto do problema e o checklist exato do que você deve enviar para o agente/ferramenta responsável pelo projeto **Projeto - Vturb** (clone do VTurb hospedado em `turb-front.aryaraj.shop` / `turb-back.aryaraj.shop`).

---

## 📌 Contexto do Problema

No projeto da **Bússola Astrológica** (quiz), na etapa final de oferta (tela 10), estamos exibindo o player de VSL via `iframe` apontando para o seu player personalizado:

```html
<iframe 
  id="ofertaVsl" 
  src="https://turb-front.aryaraj.shop/?embed=c6818306-fbe3-4919-b404-2f5b99424bc1"
  allow="autoplay *; fullscreen *; encrypted-media *" 
  allowfullscreen>
</iframe>
```

### O que está acontecendo:
1. O iframe carrega, mas fica com a **tela totalmente branca**, sem renderizar o vídeo.
2. Como o vídeo não roda, ele não emite o evento de pitch e a oferta abaixo (preço e botão de compra da Hotmart) não é revelada para o usuário.

---

## 📋 Mensagem / Prompt para copiar e colar para o agente do Projeto VTurb

> **Copie o texto entre as linhas abaixo e cole na conversa com a outra ferramenta:**

***

Olá! Estou integrando o player do nosso Clone VTurb (`turb-front.aryaraj.shop`) através de um `iframe` embed na landing page do nosso funil:
`https://turb-front.aryaraj.shop/?embed=c6818306-fbe3-4919-b404-2f5b99424bc1`

No entanto, o iframe está ficando com a **tela branca** e não está iniciando o vídeo. Preciso que você resolva os seguintes pontos críticos no frontend e backend do VTurb:

### 1. Fundo Branco no Embed (`html, body`)
No arquivo `frontend/src/index.css`, o `html, body` está estilizado com `background-color: #f8fafc;` (branco). 
- Quando o player entra em modo embed ou está carregando, ele projeta essa tela branca dentro do iframe do site parceiro.
- **Ação:** Deixar o fundo como `background: #000;` ou transparente quando estiver em modo embed (`?embed=...`), evitando qualquer flash ou caixa branca.

### 2. Investigar erro de renderização do `EmbedPlayer.tsx`
Ao acessar `https://turb-front.aryaraj.shop/?embed=c6818306-fbe3-4919-b404-2f5b99424bc1`:
- O backend responde com os dados do vídeo com sucesso em `https://turb-back.aryaraj.shop/videos/c6818306-fbe3-4919-b404-2f5b99424bc1`.
- Porém, o frontend não renderiza o componente `<video>` nem o overlay de play/autoplay.
- **Ação:** Verificar o console e o ciclo de vida do `EmbedPlayer.tsx`:
  - Garantir que não há erros de JavaScript quebrando a árvore React (ex: hooks chamados condicionalmente, erro ao acessar propriedades nulas de `player_settings`, ou erro ao instanciar listeners de eventos).
  - Tratar o estado de loading e erro para que sempre mostre uma interface preta com botão de play/fallback visível, em vez de tela em branco.

### 3. Comunicação via `postMessage` com a página mãe (Funil/Quiz)
A página mãe (onde o iframe está embutido) precisa saber quando o vídeo atinge o pitch para liberar os botões de compra.
- O site parceiro espera o seguinte evento:
  ```javascript
  window.parent?.postMessage({ type: 'VTURB_PITCH_REACHED' }, '*');
  ```
- Além disso, para tracking de analytics:
  ```javascript
  window.parent?.postMessage({ 
    type: 'VTURB_PIXEL_TRACK', 
    eventName: 'Video_Pitch', // ou Video_Play, Video_25, Video_50, etc.
    videoId: videoId 
  }, '*');
  ```
- E ao receber a interação de clique da página mãe para liberar áudio:
  ```javascript
  window.addEventListener('message', (e) => {
    if (e.data?.type === 'VTURB_PARENT_INTERACTION') {
      // Destravar áudio do player se estava mudo por autoplay
    }
  });
  ```
- **Ação:** Confirmar se esses eventos estão sendo disparados no momento em que o vídeo atinge o tempo de pitch configurado no painel.

### 4. Build e Atualização em Produção
- Após ajustar o código, gerar novo build e atualizar o contêiner do `turb-front.aryaraj.shop` para que as correções entrem no ar.

***

## 💡 O que verificar localmente se o problema persistir:
- No navegador, abra o DevTools (**F12**), vá na aba **Console** e veja se há algum erro como:
  - `Blocked a frame with origin...` (CSP ou X-Frame-Options)
  - `Uncaught TypeError...`
- Se for erro de CORS ou X-Frame-Options, o servidor web / Traefik / Nginx do `turb-front` precisa permitir ser incorporado em iframes (`frame-ancestors *` ou sem cabeçalho `X-Frame-Options: DENY`).
