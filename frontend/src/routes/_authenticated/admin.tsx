import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useServerFn } from "@tanstack/react-start";
import {
  Users,
  CalendarDays,
  Globe2,
  Clock,
  RefreshCw,
  LogOut,
  Search,
  Download,
  ShieldAlert,
} from "lucide-react";
import { authSession } from "@/lib/auth-session";
import { listLeads, type LeadRow } from "@/lib/leads.functions";

export const Route = createFileRoute("/_authenticated/admin")({
  head: () => ({
    meta: [
      { title: "Painel de Leads — Astrowake" },
      { name: "description", content: "Acompanhe os leads captados, horários, origem e localidade." },
      { name: "robots", content: "noindex" },
      { property: "og:title", content: "Painel de Leads — Astrowake" },
      { property: "og:description", content: "Acompanhe os leads captados, horários, origem e localidade." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: AdminPage,
});

const dateFmt = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "America/Sao_Paulo",
});

function AdminPage() {
  const navigate = useNavigate();
  const fetchLeads = useServerFn(listLeads);
  const [search, setSearch] = useState("");

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["leads"],
    queryFn: () => fetchLeads(),
  });

  const leads: LeadRow[] = useMemo(() => data?.leads ?? [], [data]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return leads;
    return leads.filter((l) =>
      [l.nome, l.email, l.whatsapp, l.cidade, l.regiao, l.pais, l.origem]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q))
    );
  }, [leads, search]);

  const stats = useMemo(() => {
    const now = Date.now();
    const day = 24 * 60 * 60 * 1000;
    const today = leads.filter((l) => now - new Date(l.created_at).getTime() < day).length;
    const week = leads.filter((l) => now - new Date(l.created_at).getTime() < 7 * day).length;
    const cities = new Map<string, number>();
    const hours = new Map<number, number>();
    for (const l of leads) {
      const city = [l.cidade, l.regiao].filter(Boolean).join(" / ") || "Desconhecida";
      cities.set(city, (cities.get(city) ?? 0) + 1);
      const hour = Number(
        new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", hour12: false, timeZone: "America/Sao_Paulo" })
          .format(new Date(l.created_at))
          .replace(/\D/g, "")
      );
      hours.set(hour, (hours.get(hour) ?? 0) + 1);
    }
    const topCities = [...cities.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6);
    const peakHour = [...hours.entries()].sort((a, b) => b[1] - a[1])[0];
    return { today, week, topCities, peakHour, hours };
  }, [leads]);

  const exportCsv = () => {
    const headers = [
      "data_hora",
      "nome",
      "email",
      "whatsapp",
      "cidade",
      "regiao",
      "pais",
      "timezone",
      "origem",
      "utm_source",
      "utm_medium",
      "utm_campaign",
      "ip",
    ];
    const rows = filtered.map((l) => [
      dateFmt.format(new Date(l.created_at)),
      l.nome,
      l.email,
      l.whatsapp,
      l.cidade ?? "",
      l.regiao ?? "",
      l.pais ?? "",
      l.timezone ?? "",
      l.origem ?? "",
      l.utm_source ?? "",
      l.utm_medium ?? "",
      l.utm_campaign ?? "",
      l.ip ?? "",
    ]);
    const csv = [headers, ...rows]
      .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `leads-astrowake-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const signOut = () => {
    authSession.signOut();
    navigate({ to: "/auth" });
  };

  const isForbidden = error instanceof Error && /forbidden/i.test(error.message);

  return (
    <div className="min-h-screen bg-background px-4 py-10 text-foreground sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-gold">Administração</p>
            <h1 className="mt-2 font-display text-3xl text-white sm:text-4xl">Leads do Astrowake</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-2 rounded-full border border-gold/40 bg-gold/10 px-4 py-2 text-sm font-semibold text-gold-soft hover:bg-gold/20"
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
              Atualizar
            </button>
            <button
              onClick={exportCsv}
              className="inline-flex items-center gap-2 rounded-full bg-gold px-4 py-2 text-sm font-bold text-background hover:opacity-90"
            >
              <Download className="h-4 w-4" />
              Exportar CSV
            </button>
            <button
              onClick={signOut}
              className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm text-muted-foreground hover:text-white"
            >
              <LogOut className="h-4 w-4" />
              Sair
            </button>
          </div>
        </header>

        {isForbidden ? (
          <div className="mt-10 flex items-start gap-3 rounded-2xl border border-gold/25 bg-white/[0.03] p-6">
            <ShieldAlert className="mt-0.5 h-5 w-5 text-gold" />
            <div>
              <p className="font-semibold text-white">Acesso não autorizado</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Sua conta está autenticada, mas não tem permissão de administrador.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard icon={<Users className="h-5 w-5 text-gold" />} label="Total de leads" value={leads.length} />
              <StatCard icon={<CalendarDays className="h-5 w-5 text-gold" />} label="Últimas 24h" value={stats.today} />
              <StatCard icon={<CalendarDays className="h-5 w-5 text-gold" />} label="Últimos 7 dias" value={stats.week} />
              <StatCard
                icon={<Clock className="h-5 w-5 text-gold" />}
                label="Horário de pico"
                value={stats.peakHour ? `${String(stats.peakHour[0]).padStart(2, "0")}h` : "—"}
                hint={stats.peakHour ? `${stats.peakHour[1]} leads` : undefined}
              />
            </div>

            <section className="mt-6 rounded-2xl border border-gold/20 bg-white/[0.03] p-6">
              <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-gold">
                <Globe2 className="h-4 w-4" /> Principais localidades
              </h2>
              {stats.topCities.length === 0 ? (
                <p className="mt-3 text-sm text-muted-foreground">Sem dados ainda.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {stats.topCities.map(([city, count]) => (
                    <div key={city} className="flex items-center gap-3">
                      <span className="w-48 shrink-0 truncate text-sm text-foreground/90">{city}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-gold"
                          style={{ width: `${(count / stats.topCities[0]![1]) * 100}%` }}
                        />
                      </div>
                      <span className="w-10 text-right text-sm text-muted-foreground">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <div className="mt-8 flex items-center gap-3 rounded-full border border-border bg-white/[0.03] px-4 py-2.5">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por nome, e-mail, cidade…"
                className="w-full bg-transparent text-sm text-white placeholder:text-muted-foreground/70 focus:outline-none"
              />
            </div>

            <div className="mt-4 overflow-x-auto rounded-2xl border border-gold/20">
              <table className="w-full min-w-[860px] text-left text-sm">
                <thead className="bg-white/[0.04] text-xs uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3">Data / Hora (BRT)</th>
                    <th className="px-4 py-3">Nome</th>
                    <th className="px-4 py-3">E-mail</th>
                    <th className="px-4 py-3">WhatsApp</th>
                    <th className="px-4 py-3">Localidade</th>
                    <th className="px-4 py-3">Origem</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                        Carregando leads…
                      </td>
                    </tr>
                  )}
                  {!isLoading && filtered.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                        Nenhum lead encontrado.
                      </td>
                    </tr>
                  )}
                  {filtered.map((lead) => (
                    <tr key={lead.id} className="border-t border-white/5">
                      <td className="whitespace-nowrap px-4 py-3 text-foreground/90">
                        {dateFmt.format(new Date(lead.created_at))}
                      </td>
                      <td className="px-4 py-3 text-white">{lead.nome}</td>
                      <td className="px-4 py-3 text-muted-foreground">{lead.email}</td>
                      <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">{lead.whatsapp}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {[lead.cidade, lead.regiao, lead.pais].filter(Boolean).join(" / ") || "—"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {lead.utm_source ?? lead.origem ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  hint,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  hint?: string | undefined;
}) {
  return (
    <div className="rounded-2xl border border-gold/20 bg-white/[0.03] p-5">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-3 font-display text-3xl text-white">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
