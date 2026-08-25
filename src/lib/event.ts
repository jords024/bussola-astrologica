// Dados do evento Astrowake — usados no convite de calendário (.ics) e nos links.
export const EVENT = {
  title: "ASTROWAKE — Encontro ao vivo com Crassus Gobbi",
  description:
    "Encontro ao vivo e gratuito para você acessar as instruções da sua alma.\\n\\nTudo acontece no grupo do WhatsApp: https://chat.whatsapp.com/Bidw8pFNLtJ6COqH97EOQ7",
  location: "Online — Grupo do WhatsApp",
  url: "https://crassusastrologo.com.br",
  // 13/08/2026 às 20h00 (Brasília, UTC-3) → 23:00Z. Duração 1h30.
  startUtc: "20260813T230000Z",
  endUtc: "20260814T003000Z",
} as const;

export function googleCalendarUrl(): string {
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: EVENT.title,
    dates: `${EVENT.startUtc}/${EVENT.endUtc}`,
    details: EVENT.description.replace(/\\n/g, "\n"),
    location: EVENT.location,
    ctz: "America/Sao_Paulo",
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export function outlookCalendarUrl(): string {
  const params = new URLSearchParams({
    path: "/calendar/action/compose",
    rru: "addevent",
    subject: EVENT.title,
    body: EVENT.description.replace(/\\n/g, "\n"),
    location: EVENT.location,
    startdt: "2026-08-13T23:00:00Z",
    enddt: "2026-08-14T00:30:00Z",
  });
  return `https://outlook.live.com/calendar/0/deeplink/compose?${params.toString()}`;
}

/** Gera o conteúdo .ics com dois lembretes (1 dia antes e 15 min antes). */
export function buildIcs(uid = `astrowake-${EVENT.startUtc}@crassusastrologo.com.br`): string {
  const stamp = EVENT.startUtc;
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Astrowake//Convite//PT-BR",
    "CALSCALE:GREGORIAN",
    "METHOD:REQUEST",
    "BEGIN:VEVENT",
    `UID:${uid}`,
    `DTSTAMP:${stamp}`,
    `DTSTART:${EVENT.startUtc}`,
    `DTEND:${EVENT.endUtc}`,
    `SUMMARY:${EVENT.title}`,
    `DESCRIPTION:${EVENT.description}`,
    `LOCATION:${EVENT.location}`,
    `URL:${EVENT.url}`,
    "STATUS:CONFIRMED",
    "TRANSP:OPAQUE",
    "BEGIN:VALARM",
    "TRIGGER:-P1D",
    "ACTION:DISPLAY",
    "DESCRIPTION:Amanhã tem Astrowake ao vivo às 20h",
    "END:VALARM",
    "BEGIN:VALARM",
    "TRIGGER:-PT15M",
    "ACTION:DISPLAY",
    "DESCRIPTION:O Astrowake começa em 15 minutos",
    "END:VALARM",
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
}
