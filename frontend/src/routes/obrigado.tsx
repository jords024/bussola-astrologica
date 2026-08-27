import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { CheckCircle2, Calendar, Clock, MessagesSquare, CalendarPlus, Download } from "lucide-react";
import { fbqTrack, fbqTrackCustom, trackPageView } from "../lib/fbq";
import { googleCalendarUrl, outlookCalendarUrl } from "../lib/event";

const WHATSAPP_GROUP_URL = "https://chat.whatsapp.com/Bidw8pFNLtJ6COqH97EOQ7";


export const Route = createFileRoute("/obrigado")({
  head: () => ({
    meta: [
      { title: "Vaga Garantida — Astrowake" },
      {
        name: "description",
        content:
          "Sua vaga no evento Astrowake está garantida. Anote: quinta-feira às 20h (Horário de Brasília).",
      },
      { property: "og:title", content: "Vaga Garantida — Astrowake" },
      {
        property: "og:description",
        content:
          "Sua vaga no evento Astrowake está garantida. Anote: quinta-feira às 20h (Horário de Brasília).",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Obrigado,
});

function Obrigado() {
  const fired = useRef(false);
  useEffect(() => {
    if (fired.current) return;
    fired.current = true;
    trackPageView();
    fbqTrack("Lead");
  }, []);

  return (

    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-6 py-20">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,oklch(0.8_0.14_82/0.12),transparent_55%)]" />

      <div className="relative mx-auto max-w-xl text-center">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-gold/40 bg-gold/10 shadow-[var(--shadow-gold)]">
          <CheckCircle2 className="h-10 w-10 text-gold" />
        </div>

        <p className="mt-8 text-xs font-bold uppercase tracking-[0.28em] text-gold">
          Vaga garantida
        </p>

        <h1 className="mt-4 font-display text-4xl font-medium leading-tight text-white sm:text-5xl">
          Sua vaga no <span className="text-gold-gradient italic">Astrowake</span> está reservada.
        </h1>

        <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
          Tudo acontece no grupo do WhatsApp. Clique no botão abaixo e entre no
          grupo VIP para não perder nada.
        </p>

        <a
          href={WHATSAPP_GROUP_URL}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => fbqTrackCustom("ClicouGrupoWhatsApp")}
          className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full bg-gold px-7 py-4 text-base font-bold text-background shadow-[var(--shadow-gold)] transition-opacity hover:opacity-90"
        >
          <MessagesSquare className="h-5 w-5" />
          Entrar no grupo do WhatsApp
        </a>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-foreground/90">
          <span className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gold" />
            Nesta Quinta-Feira
          </span>
          <span className="h-4 w-px bg-border" />
          <span className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-gold" />
            Às 20h00 (Horário de Brasília)
          </span>
        </div>

        <div className="mt-10 rounded-2xl border border-gold/25 bg-white/[0.03] p-5 backdrop-blur-sm">
          <p className="text-sm font-semibold text-foreground">
            Adicione o evento à sua agenda e receba o lembrete
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Enviamos o convite também para o seu e-mail. Lembretes: 1 dia antes e 15 minutos antes.
          </p>
          <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-center">
            <a
              href={googleCalendarUrl()}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => fbqTrackCustom("AdicionouAgenda", { tipo: "google" })}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-gold/40 bg-gold/10 px-5 py-3 text-sm font-semibold text-gold-soft transition-colors hover:bg-gold/20"
            >
              <CalendarPlus className="h-4 w-4" />
              Google Agenda
            </a>
            <a
              href={outlookCalendarUrl()}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => fbqTrackCustom("AdicionouAgenda", { tipo: "outlook" })}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-gold/40 bg-gold/10 px-5 py-3 text-sm font-semibold text-gold-soft transition-colors hover:bg-gold/20"
            >
              <CalendarPlus className="h-4 w-4" />
              Outlook
            </a>
            <a
              href="/api/public/convite.ics"
              onClick={() => fbqTrackCustom("AdicionouAgenda", { tipo: "ics" })}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-border bg-white/[0.04] px-5 py-3 text-sm font-semibold text-foreground/90 transition-colors hover:bg-white/[0.08]"
            >
              <Download className="h-4 w-4" />
              Apple / .ics
            </a>
          </div>
        </div>

        <Link
          to="/"
          className="mt-12 inline-flex items-center justify-center rounded-full border border-gold/40 bg-gold/10 px-7 py-3 text-sm font-semibold text-gold-soft transition-colors hover:bg-gold/20"
        >
          Voltar ao início
        </Link>
      </div>
    </div>
  );
}
