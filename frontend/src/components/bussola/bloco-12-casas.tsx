import { useEffect, useRef, useState, useCallback } from "react";
import {
  User,
  Coins,
  MessageCircle,
  Home,
  Heart,
  Activity,
  Users,
  Flame,
  Plane,
  Mountain,
  UsersRound,
  Moon,
  Sparkles,
  ArrowUpRight,
  type LucideIcon,
} from "lucide-react";

export type House = {
  n: number;
  r: string;
  name: string;
  Icon: LucideIcon;
  teaser: string;
  body: string;
  tags: string[];
};

export const HOUSES: House[] = [
  {
    n: 1,
    r: "I",
    name: "Você",
    Icon: User,
    teaser: "Quem você é e como você começa as coisas.",
    body: "É a porta da sua identidade. Fala do corpo, da aparência, da autoestima e, principalmente, da forma como você se lança nas coisas. Quando essa área se move, mexe em recomeço, em vontade de mudar o visual, em iniciativa.",
    tags: ["Identidade", "Corpo", "Autoestima", "Iniciativa", "Recomeços"],
  },
  {
    n: 2,
    r: "II",
    name: "Dinheiro",
    Icon: Coins,
    teaser: "O que entra, o que fica e o que você considera valioso.",
    body: "Renda, recursos, segurança material e gastos. Também fala dos seus talentos — aquilo que você sabe fazer e pode transformar em dinheiro — e do que você considera valioso o suficiente para guardar.",
    tags: ["Renda", "Recursos", "Segurança", "Gastos", "Talentos"],
  },
  {
    n: 3,
    r: "III",
    name: "Comunicação",
    Icon: MessageCircle,
    teaser: "Conversas, decisões do dia e o que você assina.",
    body: "Tudo o que passa pela palavra: conversas, estudos, documentos, contratos rápidos. Também governa os deslocamentos do dia a dia e a relação com quem está perto — irmãos, vizinhos, colegas.",
    tags: ["Conversas", "Estudos", "Documentos", "Deslocamentos", "Pessoas próximas"],
  },
  {
    n: 4,
    r: "IV",
    name: "Casa e família",
    Icon: Home,
    teaser: "Raízes, lar e o lugar onde você descansa.",
    body: "O chão de onde você veio e o lugar onde você se recolhe. Família, pertencimento, vida íntima. Quando essa área se move, costuma aparecer mudança de casa, reforma, ou assunto de família batendo à porta.",
    tags: ["Lar", "Família", "Raízes", "Pertencimento", "Mudanças"],
  },
  {
    n: 5,
    r: "V",
    name: "Amor e criação",
    Icon: Heart,
    teaser: "Romance, prazer e aquilo que só você poderia criar.",
    body: "A porta do prazer. Romance, paquera, hobbies, filhos e projetos autorais. É onde a sua expressão pessoal aparece sem filtro — o que você faz porque quer, não porque precisa.",
    tags: ["Romance", "Prazer", "Criatividade", "Filhos", "Expressão"],
  },
  {
    n: 6,
    r: "VI",
    name: "Rotina e corpo",
    Icon: Activity,
    teaser: "Hábitos, disciplina e o corpo que te carrega.",
    body: "O trabalho de todo dia, a organização, a agenda. E o corpo: saúde, alimentação, autocuidado. É a área que mostra se a sua rotina está te sustentando ou te consumindo.",
    tags: ["Hábitos", "Organização", "Trabalho", "Disciplina", "Autocuidado"],
  },
  {
    n: 7,
    r: "VII",
    name: "Relacionamentos",
    Icon: Users,
    teaser: "O outro: namoro, sociedade, acordo.",
    body: "Toda relação de um pra um. Namoro, casamento, sócio, contrato. É a porta que fala de acordo — o que você combina com alguém e o quanto isso está equilibrado.",
    tags: ["Namoro", "Casamento", "Sociedades", "Contratos", "Acordos"],
  },
  {
    n: 8,
    r: "VIII",
    name: "Transformação",
    Icon: Flame,
    teaser: "Intimidade, crise e o que renasce depois.",
    body: "A área mais profunda do mapa. Intimidade, sexualidade, crises, perdas e renascimentos. Também governa dinheiro que não é só seu: recursos compartilhados, dívidas, heranças, o dinheiro do casal.",
    tags: ["Intimidade", "Crises", "Renascimento", "Dívidas", "Heranças"],
  },
  {
    n: 9,
    r: "IX",
    name: "Expansão",
    Icon: Plane,
    teaser: "Viagem, estudo e novas formas de enxergar.",
    body: "Onde a sua vida fica maior. Viagens longas, estudo superior, espiritualidade, filosofia. É a porta que abre quando você começa a acreditar em coisas que não cabiam na sua visão antiga.",
    tags: ["Viagens", "Estudos", "Espiritualidade", "Filosofia", "Crenças"],
  },
  {
    n: 10,
    r: "X",
    name: "Carreira",
    Icon: Mountain,
    teaser: "Profissão, autoridade e o que te torna reconhecida.",
    body: "O topo do mapa e o topo da sua vida pública. Profissão, vocação, reputação, visibilidade. É a porta dos grandes objetivos — e de ser vista pelo que você faz.",
    tags: ["Profissão", "Vocação", "Autoridade", "Reputação", "Visibilidade"],
  },
  {
    n: 11,
    r: "XI",
    name: "Futuro e conexões",
    Icon: UsersRound,
    teaser: "Amizade, comunidade e o que você planeja.",
    body: "As pessoas que caminham do seu lado: amizades, grupos, comunidade, audiência. E o futuro que você desenha com elas — projetos coletivos, sonhos, planos de longo prazo.",
    tags: ["Amizades", "Grupos", "Comunidade", "Audiência", "Planos"],
  },
  {
    n: 12,
    r: "XII",
    name: "Recolhimento",
    Icon: Moon,
    teaser: "Descanso, bastidor e fim de ciclo.",
    body: "A porta do silêncio. Descanso, solidão escolhida, inconsciente, padrões que agem sem você perceber. É onde os ciclos se encerram — e onde o próximo começa a ser preparado nos bastidores.",
    tags: ["Descanso", "Solitude", "Inconsciente", "Bastidores", "Encerramentos"],
  },
];

const pos = (i: number, radius: number) => {
  const a = ((i * 30 - 90) * Math.PI) / 180;
  return { x: 100 + Math.cos(a) * radius, y: 100 + Math.sin(a) * radius };
};

export default function Bloco12Casas() {
  const railRef = useRef<HTMLDivElement | null>(null);
  const [live, setLive] = useState(0);
  const [open, setOpen] = useState<number | null>(null);

  const onScroll = useCallback(() => {
    const rail = railRef.current;
    if (!rail) return;
    const mid = rail.scrollLeft + rail.clientWidth / 2;
    let best = 0;
    let gap = Infinity;
    Array.from(rail.children).forEach((child, k) => {
      const c = child as HTMLElement;
      const g = Math.abs(c.offsetLeft + c.offsetWidth / 2 - mid);
      if (g < gap) {
        gap = g;
        best = k;
      }
    });
    setLive((prev) => (prev === best ? prev : best));
  }, []);

  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    let raf = 0;
    const handler = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(onScroll);
    };
    rail.addEventListener("scroll", handler, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      rail.removeEventListener("scroll", handler);
    };
  }, [onScroll]);

  useEffect(() => {
    if (open === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(null);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  // Avisa a barra de CTA fixa pra se esconder enquanto esse modal em tela
  // cheia estiver aberto, evitando sobreposição no rodapé.
  useEffect(() => {
    window.dispatchEvent(new CustomEvent("bussola:casas-modal", { detail: open !== null }));
    return () => {
      window.dispatchEvent(new CustomEvent("bussola:casas-modal", { detail: false }));
    };
  }, [open]);

  const halo = pos(live, 84);
  const detail = open !== null ? HOUSES[open] : null;

  return (
    <section
      aria-label="As 12 áreas do seu mapa"
      className="relative isolate w-full overflow-hidden bg-background py-14 md:py-20"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(50% 40% at 50% 30%, color-mix(in oklab, var(--gold) 12%, transparent) 0%, transparent 70%)",
        }}
      />

      <header className="relative mx-auto max-w-xl px-6 text-center">
        <p className="font-body text-[11px] font-medium uppercase tracking-[0.34em] text-gold">
          Bússola Astrológica
        </p>
        <h2 className="mt-4 font-display text-[2.25rem] leading-[1.08] text-foreground sm:text-5xl">
          Seu mapa fala sobre <em className="italic text-gold">12 áreas</em> da sua vida
        </h2>
        <div aria-hidden className="my-5 flex items-center justify-center gap-3">
          <span className="h-px w-14 bg-gradient-to-r from-transparent to-gold/40" />
          <Sparkles className="h-3.5 w-3.5 text-gold" />
          <span className="h-px w-14 bg-gradient-to-l from-transparent to-gold/40" />
        </div>
        <p className="mx-auto max-w-[34ch] text-sm leading-relaxed text-muted-foreground">
          Cada uma tem um momento próprio. Toque em uma área para ver o que ela governa.
        </p>
      </header>

      {/* Roda das casas */}
      <div className="relative mt-8 grid h-[186px] place-items-center">
        <svg viewBox="0 0 200 200" aria-hidden className="h-[186px] w-[186px] overflow-visible">
          <circle
            cx="100"
            cy="100"
            r="84"
            fill="none"
            stroke="color-mix(in oklab, var(--gold) 22%, transparent)"
            strokeWidth="0.75"
          />
          <circle
            cx="100"
            cy="100"
            r="70"
            fill="none"
            stroke="color-mix(in oklab, var(--gold) 22%, transparent)"
            strokeWidth="0.75"
            strokeDasharray="1 5"
          />
          {HOUSES.map((h, i) => {
            const outer = pos(i, 84);
            const inner = pos(i, 77);
            const on = i === live;
            return (
              <g key={h.n}>
                <line
                  x1={inner.x}
                  y1={inner.y}
                  x2={outer.x}
                  y2={outer.y}
                  stroke="color-mix(in oklab, var(--gold) 30%, transparent)"
                  strokeWidth="0.75"
                />
                <circle
                  cx={outer.x}
                  cy={outer.y}
                  r={on ? 3.6 : 2}
                  fill={on ? "var(--gold)" : "color-mix(in oklab, var(--gold) 35%, transparent)"}
                  style={{ transition: "r .45s cubic-bezier(.2,.8,.2,1), fill .45s" }}
                />
              </g>
            );
          })}
          <circle
            cx={halo.x}
            cy={halo.y}
            r="10"
            fill="none"
            stroke="var(--gold)"
            strokeWidth="1"
            opacity="0.55"
            style={{
              transition: "cx .5s cubic-bezier(.2,.8,.2,1), cy .5s cubic-bezier(.2,.8,.2,1)",
            }}
          />
        </svg>
        <div className="absolute text-center">
          <div className="font-display text-[46px] leading-none text-gold">{HOUSES[live]?.n}</div>
          <div className="mt-1.5 text-[9.5px] uppercase tracking-[0.3em] text-gold/60">
            Casa {HOUSES[live]?.n}
          </div>
        </div>
      </div>

      {/* Carrossel */}
      <div
        ref={railRef}
        className="relative flex snap-x snap-mandatory gap-4 overflow-x-auto px-7 pb-6 pt-3.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      >
        {HOUSES.map((h, i) => {
          const on = i === live;
          return (
            <article
              key={h.n}
              className="flex min-h-[322px] w-[268px] flex-none snap-center flex-col rounded-[20px] border p-6 pt-6 transition-[transform,opacity,border-color] duration-500"
              style={{
                background:
                  "linear-gradient(168deg, color-mix(in oklab, var(--gold) 6%, var(--background)) 0%, var(--background) 100%)",
                borderColor: on
                  ? "color-mix(in oklab, var(--gold) 50%, transparent)"
                  : "color-mix(in oklab, var(--gold) 22%, transparent)",
                opacity: on ? 1 : 0.55,
                transform: on ? "scale(1)" : "scale(.95)",
              }}
            >
              <div className="mb-5 flex items-center justify-between">
                <span className="font-display text-[34px] leading-none text-gold">{h.n}</span>
                <span className="grid h-[42px] w-[42px] place-items-center rounded-full border border-gold/25 text-gold">
                  <h.Icon className="h-[19px] w-[19px]" />
                </span>
              </div>
              <h3 className="mb-3 font-body text-[12.5px] uppercase tracking-[0.24em] text-foreground">
                {h.name}
              </h3>
              <p className="flex-1 font-display text-xl leading-[1.42] text-muted-foreground">
                {h.teaser}
              </p>
              <button
                type="button"
                onClick={() => setOpen(i)}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-full border border-gold/25 py-3.5 text-[10.5px] uppercase tracking-[0.22em] text-gold transition-colors hover:border-gold/55 hover:bg-gold/10"
              >
                Saber mais <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </article>
          );
        })}
      </div>

      <div className="flex justify-center gap-1.5 pb-2">
        {HOUSES.map((h, i) => (
          <span
            key={h.n}
            className="h-1 rounded-full transition-all duration-300"
            style={{
              width: i === live ? 16 : 4,
              background:
                i === live ? "var(--gold)" : "color-mix(in oklab, var(--gold) 28%, transparent)",
            }}
          />
        ))}
      </div>

      <p className="pt-4 text-center text-[10px] uppercase tracking-[0.26em] text-gold/60">
        Arraste para o lado
      </p>

      {/* Transição para o próximo bloco */}
      <div className="relative mx-auto mt-14 max-w-3xl px-6 md:mt-20">
        <div
          className="rounded-[24px] border border-gold/20 p-7 md:p-10"
          style={{
            background:
              "linear-gradient(168deg, color-mix(in oklab, var(--gold) 5%, var(--background)) 0%, var(--background) 70%)",
          }}
        >
          <div className="mb-5 flex items-center gap-3">
            <span className="h-px flex-1 bg-gradient-to-r from-transparent via-gold/40 to-transparent" />
            <Sparkles className="h-4 w-4 text-gold" />
            <span className="h-px flex-1 bg-gradient-to-r from-transparent via-gold/40 to-transparent" />
          </div>
          <p className="text-center font-body text-sm font-medium uppercase tracking-[0.22em] text-gold/80">
            O que você aprende na prática
          </p>
          <p className="mt-6 text-center font-display text-[1.35rem] leading-[1.45] text-foreground md:text-[1.75rem]">
            Você aprende a reconhecer os sinais desses ciclos e transformar essa leitura em algo
            simples e prático:
          </p>
          <p className="mt-5 text-center font-display text-[1.15rem] leading-[1.55] text-muted-foreground md:text-[1.35rem]">
            onde colocar sua energia, o que observar e quais portas podem estar abertas para você
            com base no seu <em className="not-italic text-gold">MOMENTO ATUAL</em>
          </p>
          <div className="my-7 flex items-center justify-center gap-3">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-gold" />
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-gold/60" />
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-gold/30" />
          </div>
          <p className="text-center text-[15px] leading-[1.8] text-muted-foreground md:text-base">
            Tudo isso sem precisar virar especialista em astrologia, apenas entender os conceitos
            arquetípicos dos planetas e das casas do seu mapa astral.
          </p>
        </div>
      </div>

      {/* Painel de detalhe */}
      {detail && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-background/85 backdrop-blur-md"
          onClick={(e) => {
            if (e.target === e.currentTarget) setOpen(null);
          }}
          role="dialog"
          aria-modal="true"
          aria-label={`Casa ${detail.n} — ${detail.name}`}
        >
          <div
            className="max-h-[88vh] w-full max-w-[430px] overflow-y-auto rounded-t-[26px] border-t border-gold/40 px-7 pb-10 pt-3.5"
            style={{
              background:
                "linear-gradient(180deg, color-mix(in oklab, var(--gold) 7%, var(--background)) 0%, var(--background) 100%)",
              animation: "none",
            }}
          >
            <div className="mx-auto mb-6 h-[3px] w-9 rounded-full bg-gold/30" />
            <div className="mb-4 flex items-center gap-2.5">
              <detail.Icon className="h-4 w-4 text-gold" />
              <span className="text-[10px] uppercase tracking-[0.3em] text-gold/60">
                Casa {detail.n}
              </span>
            </div>
            <h3 className="font-display text-[34px] leading-[1.12] text-foreground">
              {detail.name}
            </h3>
            <p className="mb-5 mt-1 font-display text-[15px] italic text-gold">{detail.r}</p>
            <p className="mb-6 text-[15px] leading-[1.8] text-muted-foreground">{detail.body}</p>
            <div className="mb-7 flex flex-wrap gap-2">
              {detail.tags.map((t) => (
                <span
                  key={t}
                  className="rounded-full border border-gold/25 px-3 py-1.5 text-[11px] tracking-wide text-gold"
                >
                  {t}
                </span>
              ))}
            </div>
            <button
              type="button"
              onClick={() => setOpen(null)}
              className="w-full rounded-full bg-gold py-4 text-[11px] font-medium uppercase tracking-[0.22em] text-background"
            >
              Voltar às áreas
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
