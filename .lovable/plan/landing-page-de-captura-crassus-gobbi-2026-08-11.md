# Landing page de captura — Crassus Gobbi

Página de captura em português, estética preta e dourada, luxuosa e minimalista, com a foto enviada como fundo do hero.

## O que será construído

**Rota `/` (substitui a página placeholder)**

1. **Hero + formulário**
   - Fundo: a imagem enviada (retrato cósmico), com camadas de parallax suave no scroll e gradiente escuro para legibilidade.
   - Conteúdo: badge "EVENTO AO VIVO E 100% GRATUITO • QUINTA-FEIRA ÀS 20H", headline com "limpeza energética" em dourado, subheadline, barra de data/horário e checklist de 3 benefícios.
   - Botão dourado "QUERO GARANTIR MINHA VAGA" que abre um modal (pop-up): card em vidro (glassmorphism) com Nome, E-mail e WhatsApp, botão de envio com estado de carregamento e selo de segurança.
   - Ao enviar, redireciona para `/obrigado`.

2. **Seção de autoridade "Quem é Crassus Gobbi"**
   - Retrato com legenda (nome + "Criador do Método Astrowake • +5.000 Atendimentos").
   - Título "Quem vai te guiar" seguido do texto de narrativa completo fornecido, com o parágrafo final destacado.
   - Três números no rodapé da seção: "+5.000 Atendimentos de consultório", "45+ Anos de tradição familiar", "100% Prático e sem decoreba".

3. **Rota `/obrigado`** — página de agradecimento simples no mesmo estilo, confirmando a inscrição e orientando sobre o link da sala.

## Estilo

- Tokens no design system: fundo quase preto, dourado/âmbar como cor primária, textos em tons quentes de cinza.
- Tipografia: display serifada elegante para títulos + sans limpa para o corpo, carregada via `<link>` no root.
- Nada de roxo/gradientes genéricos; contraste alto, muito respiro, detalhes dourados finos.

## Detalhes técnicos

- Instalar `gsap` e `lenis` (o pacote `@studio-freight/lenis` foi renomeado para `lenis`); `lucide-react` já vem no template.
- GSAP ScrollTrigger + Lenis inicializados em `useEffect`, com cleanup; animação desativada quando o usuário prefere movimento reduzido.
- A imagem enviada entra como asset via CDN e é usada no hero e na seção de autoridade.
- O formulário é apenas frontend nesta etapa: valida os campos e redireciona para `/obrigado`, sem salvar os leads em lugar nenhum.
- SEO por rota: `head()` próprio em `/` e `/obrigado` com título, descrição e tags og/twitter.

## Ponto em aberto

Se você quiser **guardar os leads** (nome, e-mail, WhatsApp) num banco, ou enviá-los para uma ferramenta externa, é só dizer — nesse caso eu ativo o Lovable Cloud e salvo cada inscrição antes do redirecionamento.
