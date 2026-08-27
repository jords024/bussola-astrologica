import { defineTool } from "@lovable.dev/mcp-js";
import { z } from "zod";
import { supabaseForUser } from "../supabase";

type Row = { created_at: string; cidade: string | null; regiao: string | null; origem: string | null };

function rank(values: Array<string | null>, top = 8) {
  const counts = new Map<string, number>();
  for (const value of values) {
    const key = value?.trim() || "Desconhecido";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, top)
    .map(([label, total]) => ({ label, total }));
}

export default defineTool({
  name: "lead_stats",
  title: "Estatísticas de leads",
  description:
    "Resumo dos leads do Astrowake: total, últimas 24h e 7 dias, horário de pico, cidades e origens mais frequentes. Requer conta de administrador.",
  inputSchema: {
    days: z.number().int().min(1).max(365).default(30).describe("Janela de análise em dias."),
  },
  outputSchema: {
    janela_dias: z.number(),
    total_na_janela: z.number(),
    ultimas_24h: z.number(),
    ultimos_7_dias: z.number(),
    horario_pico_utc: z.string().nullable(),
    cidades: z.array(z.object({ label: z.string(), total: z.number() })),
    origens: z.array(z.object({ label: z.string(), total: z.number() })),
  },
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  handler: async ({ days }, ctx) => {
    if (!ctx.isAuthenticated()) {
      return { content: [{ type: "text", text: "Não autenticado." }], isError: true };
    }
    const window = days ?? 30;
    const since = new Date(Date.now() - window * 86_400_000).toISOString();
    const supabase = supabaseForUser(ctx);
    const { data, error } = await supabase
      .from("leads")
      .select("created_at, cidade, regiao, origem")
      .gte("created_at", since)
      .order("created_at", { ascending: false })
      .limit(5000);

    if (error) return { content: [{ type: "text", text: error.message }], isError: true };

    const rows = (data ?? []) as Row[];
    const now = Date.now();
    const last24h = rows.filter((r) => now - Date.parse(r.created_at) <= 86_400_000).length;
    const last7d = rows.filter((r) => now - Date.parse(r.created_at) <= 7 * 86_400_000).length;

    const hours = new Map<number, number>();
    for (const row of rows) {
      const hour = new Date(row.created_at).getUTCHours();
      hours.set(hour, (hours.get(hour) ?? 0) + 1);
    }
    const peak = [...hours.entries()].sort((a, b) => b[1] - a[1])[0];

    const stats = {
      janela_dias: window,
      total_na_janela: rows.length,
      ultimas_24h: last24h,
      ultimos_7_dias: last7d,
      horario_pico_utc: peak ? `${String(peak[0]).padStart(2, "0")}:00` : null,
      cidades: rank(rows.map((r) => (r.cidade ? `${r.cidade}${r.regiao ? ` / ${r.regiao}` : ""}` : null))),
      origens: rank(rows.map((r) => r.origem)),
    };

    return {
      content: [{ type: "text", text: JSON.stringify(stats, null, 2) }],
      structuredContent: stats,
    };
  },
});
