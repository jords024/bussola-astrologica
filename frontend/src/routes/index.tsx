import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, type FormEvent } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import {
  ArrowRight,
  CheckCircle2,
  Calendar,
  Clock,
  Lock,
  X,
  ShieldCheck,
} from "lucide-react";


import { fbqTrack, fbqTrackCustom, trackPageView } from "../lib/fbq";
import { submitLead } from "../lib/leads.functions";
import crassusAsset from "../assets/crassus-cosmico.png.asset.json";
import crassusMobileAsset from "../assets/crassus-mobile.png.asset.json";


export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Astrowake — Hackeando a Realidade" },
      {
        name: "description",
        content:
          "Aprenda a fazer a sua limpeza energética e alinhar o seu campo. Evento ao vivo, gratuito, nesta quinta-feira às 20h com Crassus Gobbi.",
      },
      { property: "og:title", content: "Astrowake — Hackeando a Realidade" },
      {
        property: "og:description",
        content:
          "Aprenda a fazer a sua limpeza energética e alinhar o seu campo. Evento ao vivo, gratuito, nesta quinta-feira às 20h com Crassus Gobbi.",
      },
      { property: "og:type", content: "website" },
      { property: "og:image", content: crassusAsset.url },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: crassusAsset.url },
    ],
  }),
  component: Index,
});

function Index() {
  const parallaxRef = useRef<HTMLDivElement>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({ nome: "", email: "", whatsapp: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submittedRef = useRef(false);
  const origemRef = useRef<string>("hero");

  const openModal = (origem: string) => {
    submittedRef.current = false;
    origemRef.current = origem;
    setModalOpen(true);
    // Lead abriu o formulário (chegou até esse ponto)
    fbqTrack("InitiateCheckout", { content_name: "Formulario Astrowake", origem });
    fbqTrackCustom("AbriuFormulario", { origem });
  };

  const closeModal = () => {
    setModalOpen(false);
    if (!submittedRef.current) {
      // Abriu o formulário e desistiu sem enviar
      fbqTrackCustom("AbandonouFormulario", {
        preencheu_nome: Boolean(formData.nome),
        preencheu_email: Boolean(formData.email),
        preencheu_whatsapp: Boolean(formData.whatsapp),
      });
    }
  };

  useEffect(() => {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) return;

    gsap.registerPlugin(ScrollTrigger);

    const heroEl = parallaxRef.current?.querySelector("[data-parallax-layers]");
    if (heroEl) {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: heroEl,
          start: "top top",
          end: "bottom top",
          scrub: 0,
        },
      });
      tl.to(
        heroEl.querySelectorAll('[data-parallax-layer="1"]'),
        { yPercent: 40, ease: "none" },
        0
      );
      tl.to(
        heroEl.querySelectorAll('[data-parallax-layer="2"]'),
        { yPercent: 18, ease: "none" },
        0
      );
    }

    const lenis = new Lenis({ autoRaf: false });
    lenis.on("scroll", ScrollTrigger.update);
    const raf = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(raf);
    gsap.ticker.lagSmoothing(0);

    // Gentle reveal
    gsap.fromTo(
      "[data-reveal]",
      { opacity: 0, y: 24 },
      { opacity: 1, y: 0, duration: 0.9, ease: "power2.out", stagger: 0.12 }
    );

    return () => {
      ScrollTrigger.getAll().forEach((st) => st.kill());
      gsap.ticker.remove(raf);
      lenis.destroy();
    };
  }, []);

  const pixelFired = useRef(false);
  useEffect(() => {
    if (pixelFired.current) return;
    pixelFired.current = true;
    trackPageView();
  }, []);


  useEffect(() => {
    document.body.style.overflow = modalOpen ? "hidden" : "";

    return () => {
      document.body.style.overflow = "";
    };
  }, [modalOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    submittedRef.current = true;
    setIsSubmitting(true);
    fbqTrackCustom("EnviouFormulario");
    try {
      const params = new URLSearchParams(window.location.search);
      await submitLead({
        data: {
          nome: formData.nome,
          email: formData.email,
          whatsapp: formData.whatsapp,
          origem: origemRef.current,
          referrer: document.referrer,
          utm_source: params.get("utm_source") ?? undefined,
          utm_medium: params.get("utm_medium") ?? undefined,
          utm_campaign: params.get("utm_campaign") ?? undefined,
        },
      });
    } catch {
      // não bloqueia o lead: segue para a página de obrigado
    }
    window.location.href = "/obrigado";
  };


  const setField =
    (key: keyof typeof formData) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setFormData({ ...formData, [key]: e.target.value });

  return (
    <div className="min-h-screen bg-background text-foreground antialiased">
      {/* ==================== HERO ==================== */}
      <section ref={parallaxRef} className="relative min-h-screen overflow-hidden">
        {/* Parallax background */}
        <div data-parallax-layers className="absolute inset-0">
          <div data-parallax-layer="1" className="absolute inset-x-0 top-0 h-[72vh] lg:inset-y-0 lg:left-auto lg:right-0 lg:h-auto lg:w-[68%]">
            <picture>
              <source media="(min-width: 1024px)" srcSet={crassusAsset.url} />
              <img
                src={crassusMobileAsset.url}
                alt="Crassus Gobbi em atmosfera cósmica dourada"
                className="h-full w-full object-cover object-[50%_28%] lg:object-center"
              />
            </picture>
          </div>
          <div data-parallax-layer="2" className="absolute inset-0">
            {/* Mobile: fade suave e contínuo da foto para o fundo */}
            <div className="absolute inset-x-0 top-0 h-[78vh] lg:hidden bg-[linear-gradient(180deg,oklch(0.09_0_0/0.7)_0%,oklch(0.09_0_0/0.5)_12%,oklch(0.09_0_0/0.12)_28%,oklch(0.09_0_0/0.35)_52%,oklch(0.09_0_0/0.85)_72%,oklch(0.09_0_0)_92%)]" />
            <div className="absolute inset-x-0 top-[77vh] bottom-0 bg-background lg:hidden" />
            <div className="absolute inset-0 hidden lg:block bg-[linear-gradient(90deg,oklch(0.09_0_0)_0%,oklch(0.09_0_0)_26%,oklch(0.09_0_0/0.7)_38%,transparent_52%)]" />
            <div className="absolute inset-x-0 bottom-0 h-32 hidden lg:block bg-gradient-to-t from-background to-transparent" />
          </div>



        </div>

        <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col items-start justify-start px-5 pb-16 pt-[7vh] sm:justify-center sm:px-6 sm:pb-24 sm:pt-24">
          <h1
            data-reveal
            className="max-w-[15ch] font-sans text-4xl font-extrabold leading-[0.95] tracking-[-0.03em] text-white sm:text-5xl lg:text-7xl"
          >
            ASTROWAKE:
            <span className="mt-1 block text-gold">Hackeando a Realidade</span>
          </h1>

          {/* Espaço para o rosto do Crassus aparecer no mobile */}
          <div aria-hidden className="h-[34vh] sm:hidden" />



          <p data-reveal className="mt-6 max-w-xl whitespace-pre-line text-[17px] leading-relaxed text-muted-foreground">
            Um encontro ao vivo para você acessar as instruções da sua alma através de uma tecnologia milenar e nunca mais jogar a
            vida no{"\u00A0"}{"\n"}<strong className="font-semibold text-gold">Modo Difícil...</strong>
          </p>


          {/* Date & time bar */}
          <div data-reveal className="mt-7 flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-foreground/90">
            <span className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gold" />
              Nesta quinta-feira
            </span>
            <span className="hidden h-4 w-px bg-border sm:block" />
            <span className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-gold" />
              20h • Horário de Brasília
            </span>
          </div>

          {/* Checklist */}
          <ul data-reveal className="mt-7 max-w-xl space-y-2.5">
            {[
              { title: "Carreira & Escolhas", text: "clareza para onde colocar sua energia para\nprosperar de verdade" },
              { title: "Relações Pessoais", text: "limites claros, sem se anular" },
              { title: "Direção de Vida", text: "seus\u00A0próximos passos com menos ansiedade" },
            ].map((item) => (
              <li key={item.title} className="flex items-start gap-3 text-[15px] text-foreground/90">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-gold" />
                <span>
                  <strong className="font-semibold text-foreground">{item.title}</strong>
                  <span className="whitespace-pre-line text-muted-foreground"> — {item.text}</span>
                </span>
              </li>
            ))}
          </ul>


          {/* CTA opens modal */}
          <button
            data-reveal
            onClick={() => openModal("hero_cta")}
            className="group mt-9 inline-flex w-full items-center justify-center gap-3 rounded-full bg-gradient-to-r from-gold-deep via-gold to-gold-soft px-8 py-4 text-sm font-bold uppercase tracking-[0.16em] text-primary-foreground shadow-[var(--shadow-gold)] transition-transform duration-300 hover:scale-[1.03] sm:w-auto"
          >
            Quero participar
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
          </button>

          {/* Price anchor + scarcity */}
          <div data-reveal className="mt-7">
            <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground/70">
              Valor do ingresso
            </span>
            <div className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <span className="text-2xl font-bold text-muted-foreground/60 line-through">
                R$197,00
              </span>
              <ArrowRight className="h-5 w-5 shrink-0 self-center text-gold" />
              <span className="font-display text-3xl font-semibold text-gold">R$0,00</span>
            </div>
            <p className="mt-2 text-xs uppercase tracking-[0.16em] text-foreground/80">
              Ingresso ao vivo • Máximo 400 pessoas
            </p>
          </div>

          <p data-reveal className="mt-5 flex items-center gap-2 text-xs text-muted-foreground">
            <Lock className="h-3.5 w-3.5 text-gold" />
            Seus dados estão 100% seguros. Livre de spam.
          </p>
        </div>
      </section>

      {/* ==================== QUEM É CRASSUS ==================== */}
      <section className="relative overflow-hidden py-24 sm:py-32">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-gold/40 to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-64 bg-[radial-gradient(ellipse_at_bottom,oklch(0.8_0.14_82/0.08),transparent_60%)]" />

        <div className="mx-auto grid max-w-6xl items-start gap-14 px-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          {/* Portrait */}
          <div className="relative mx-auto w-full max-w-md lg:sticky lg:top-16">
            <div className="pointer-events-none absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-gold/25 via-transparent to-gold/15 blur-2xl" />
            <div className="relative overflow-hidden rounded-[1.5rem] border border-gold/20">
              <img
                src={crassusAsset.url}
                alt="Crassus Gobbi"
                className="aspect-[4/5] w-full object-cover object-center"
              />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-background via-background/60 to-transparent p-6 pt-16">
                <p className="font-display text-2xl font-medium text-white">Crassus Gobbi</p>
                <p className="mt-1 text-sm text-gold-soft">
                  Criador do Método Astrowake • +5.000 Atendimentos
                </p>
              </div>
            </div>
          </div>

          {/* Narrative */}
          <div className="space-y-6">
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-gold">Quem vai te guiar</p>

            <p className="font-display text-2xl leading-snug font-medium text-white sm:text-3xl">
              Astrologia de verdade não é sobre prever o futuro. É sobre tomar as rédeas da sua
              vida e da sua prosperidade.
            </p>

            <div className="space-y-5 text-[16px] leading-relaxed text-foreground/85">
              <p>
                Eu cresci dentro da astrologia. A minha mãe atua há mais de 45 anos no mercado, e
                desde muito cedo eu vi o impacto que o mapa astral tinha na vida das pessoas. Mas eu
                precisei construir o meu próprio caminho.
              </p>
              <p>
                Aos 28 anos, eu era empresário, dono de 5 empresas em Porto Alegre, usava blazer e
                vivia no ritmo acelerado do mercado. Por fora, parecia sucesso. Por dentro, eu estava
                exausto, rasgando dinheiro na tentativa e erro e pilotando a minha vida no escuro.
              </p>
              <p>
                A grande virada aconteceu quando eu parei de tratar a astrologia como teoria e passei
                a aplicar o mapa como uma ferramenta de estratégia financeira e direção da minha vida.
              </p>
              <p>
                Eu alinhei a minha carreira e o meu trabalho ao meu momento da época e comecei a viver
                a astrologia real. O resultado? Conquistei a minha independência financeira, fechei
                meus antigos negócios e hoje vivo com liberdade total, viajando o mundo e trabalhando
                no meu estilo, atendendo pessoas online pelo mundo.
              </p>
              <p className="rounded-xl border border-gold/20 bg-gold/[0.06] p-5">
                Após mais de 5.000 atendimentos individuais, eu criei o evento{" "}
                <span className="font-semibold text-gold-soft">Astrowake</span> para te entregar esse
                mesmo manual. Eu não vou te ensinar a virar astrólogo nem te passar decoreba teórica.
                Eu vou te mostrar como usar essa tecnologia milenar pra você tomar decisões inteligentes
                na sua carreira, no seu dinheiro e nos seus relacionamentos.
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 gap-3 pt-4 sm:grid-cols-3 sm:gap-4">
              {[
                { value: "+5.000", label: "Atendimentos de consultório" },
                { value: "45+", label: "Anos de tradição familiar" },
                { value: "100%", label: "Prático e sem decoreba" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="flex items-center justify-between gap-4 rounded-2xl border border-border bg-card/60 px-5 py-4 text-center sm:flex-col sm:justify-center sm:px-4 sm:py-5"
                >
                  <p className="font-display text-3xl font-semibold text-gold-gradient sm:text-4xl">
                    {stat.value}
                  </p>
                  <p className="text-left text-[11px] font-medium uppercase tracking-wide text-muted-foreground sm:mt-2 sm:text-center">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ==================== MODAL / POPUP ==================== */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          onClick={() => closeModal()}
        >
          <div
            className="relative w-full max-w-md overflow-hidden rounded-[1.5rem] border border-gold/25 bg-card shadow-[var(--shadow-gold)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[radial-gradient(ellipse_at_top,oklch(0.8_0.14_82/0.28),transparent_70%)]" />

            <button
              onClick={() => closeModal()}
              aria-label="Fechar"
              className="absolute right-4 top-4 rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-white/10 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="relative p-7 sm:p-8">
              <span className="inline-flex items-center gap-2 rounded-full border border-gold/40 bg-gold/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-gold-soft">
                <ShieldCheck className="h-3.5 w-3.5" />
                Vaga gratuita
              </span>

              <h2 className="mt-5 font-display text-3xl font-medium text-white">
                Garanta Sua Vaga Gratuita
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                Preencha os dados abaixo para receber o link VIP da sala ao vivo:
              </p>

              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                <div>
                  <label htmlFor="nome" className="mb-1.5 block text-xs font-semibold text-foreground/80">
                    Seu Nome Completo
                  </label>
                  <input
                    id="nome"
                    type="text"
                    required
                    placeholder="Ex.: Maria Silva"
                    value={formData.nome}
                    onChange={setField("nome")}
                    className="w-full rounded-xl border border-input bg-background/70 px-4 py-3.5 text-sm text-white placeholder:text-muted-foreground/60 focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold transition-all"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="mb-1.5 block text-xs font-semibold text-foreground/80">
                    Seu Melhor E-mail
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    placeholder="voce@email.com"
                    value={formData.email}
                    onChange={setField("email")}
                    className="w-full rounded-xl border border-input bg-background/70 px-4 py-3.5 text-sm text-white placeholder:text-muted-foreground/60 focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold transition-all"
                  />
                </div>
                <div>
                  <label htmlFor="whatsapp" className="mb-1.5 block text-xs font-semibold text-foreground/80">
                    Seu WhatsApp com DDD
                  </label>
                  <input
                    id="whatsapp"
                    type="tel"
                    required
                    placeholder="(11) 99999-9999"
                    value={formData.whatsapp}
                    onChange={setField("whatsapp")}
                    className="w-full rounded-xl border border-input bg-background/70 px-4 py-3.5 text-sm text-white placeholder:text-muted-foreground/60 focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold transition-all"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold-deep via-gold to-gold-soft px-6 py-4 text-sm font-bold uppercase tracking-[0.14em] text-primary-foreground shadow-[var(--shadow-gold)] transition-transform duration-300 hover:scale-[1.02] disabled:opacity-80"
                >
                  {isSubmitting ? (
                    <>
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/40 border-t-primary-foreground" />
                      Garantindo vaga...
                    </>
                  ) : (
                    <>
                      Quero garantir minha vaga
                      <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
                    </>
                  )}
                </button>
              </form>

              <p className="mt-5 flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <Lock className="h-3.5 w-3.5 text-gold" />
                Seus dados estão 100% seguros. Livre de spam.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
