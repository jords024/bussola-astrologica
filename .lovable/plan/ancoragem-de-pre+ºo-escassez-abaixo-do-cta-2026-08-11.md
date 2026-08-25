# Ancoragem de preço + escassez abaixo do CTA

## O que será feito

Adicionar, abaixo do botão "QUERO PARTICIPAR" no hero (`src/routes/index.tsx`), um bloco de percepção de valor com ancoragem de preço e escassez de vagas.

### Layout do bloco (hero, centralizado à esquerda)

```
R$197,00        →        R$0,00
(riscado, cinza)          (dourado, destaque)

Ingresso ao vivo • Vagas limitadas: máximo 400 pessoas
```

- A linha de preço mostra **R$197,00 riscado** (valor âncora) ao lado do **R$0,00 em dourado** (valor real).
- Logo abaixo, a frase de escassez: **"Ingresso ao vivo • Máximo 400 pessoas"**, reforçando exclusividade e urgência.
- Estilo consistente com o tema: riscado em `text-muted-foreground/70`, o "R$0,00" em `text-gold` com peso extrabold, e um pequeno rótulo "VALOR DO EVENTO" opcional acima para dar contexto ao número riscado.

## Análise — a ideia é boa para essa audiência?

**Ponto importante (esclarecido):** R$197 é o **preço real do ingresso** do evento — não um número inventado para riscar. Nesta edição ao vivo, o ingresso é liberado por R$0. Ou seja, a "ancoragem" aqui é uma **oferta verdadeira**: o usuário recebe, grátis, algo que normalmente custaria R$197. Isso muda tudo: não há manipulação, há valor real sendo entregue de graça.

### Por que funciona (e funciona bem nesse público)
- **Âncora real, não fabricada:** o "R$197 → R$0" deixa de ser um truque e vira comunicação honesta de valor. Audiência com consciência alta rejeita preço fake, mas **responde bem a uma oferta real** — "o ingresso vale R$197 e você recebe de graça hoje" é um fato, não uma pegadinha. Isso constrói confiança em vez de desgastá-la.
- **Percepção de valor concreta:** o número dá dimensão material ao conteúdo (o "manual" de astrologia aplicada), que de outra forma ficaria abstrato. O cético entende o que está ganhando antes do clique.
- **Escassez credível:** "máximo 400 pessoas" é um limite plausível de capacidade de sala ao vivo (não um "só 3 vagas restantes" que soa falso). Limite real de sala é aceito com naturalidade por públicos alertas.
- **Baixa fricção:** "grátis + vaga limitada" convida a garantir o lugar sem custo. Decisão fácil, risco percebido zero.

### O que ainda merece cuidado (execução)
- **Contraste com a voz da página:** a promessa do hero é "sem misticismo, sem decoreba, 100% prático". O bloco de preço deve manter o tom de luxo discreto (dourado + serifado suave), sem apelar para urgência gritada (sem vermelho, sem "ÚLTIMAS VAGAS"). Valor e exclusividade, não pressa.
- **Escassez honesta:** "máximo 400 pessoas" é credível e suficiente. Evitar contadores dinâmicos de "restam N" que pareçam truque.

### Conclusão
Como o R$197 é o preço real do ingresso e o evento é gratuito, a âncora **fortalece** a percepção de valor e a conversão sem ferir a confiança — é uma oferta genuína apresentada com clareza. Esse é exatamente o tipo de âncora que funciona em audiência consciente: verdadeira, concreta e com escassez real.

## Técnico

- Alteração restrita a `src/routes/index.tsx`, no bloco do hero (após o botão, antes da linha do cadeado).
- Sem novas dependências; reutiliza tokens existentes (`text-gold`, `text-muted-foreground`, `font-display`, `font-body`).
- Classes de riscado: `line-through text-muted-foreground/70`; destaque `text-gold font-extrabold`.
