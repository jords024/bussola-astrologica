import { defineTool } from "@lovable.dev/mcp-js";
import { z } from "zod";
import { supabaseForUser } from "../supabase";

export default defineTool({
  name: "list_leads",
  title: "Listar leads",
  description:
    "Lista os leads captados na landing page do Astrowake (nome, e-mail, WhatsApp, origem, cidade e data), do mais recente para o mais antigo. Requer conta de administrador.",
  inputSchema: {
    limit: z.number().int().min(1).max(200).default(50).describe("Quantidade máxima de leads."),
    search: z.string().trim().min(1).optional().describe("Filtro por nome ou e-mail."),
    since: z
      .string()
      .datetime()
      .optional()
      .describe("Data ISO 8601: retorna apenas leads criados a partir dela."),
  },
  outputSchema: {
    leads: z.array(z.record(z.string(), z.unknown())),
    count: z.number(),
  },
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  handler: async ({ limit, search, since }, ctx) => {
    if (!ctx.isAuthenticated()) {
      return { content: [{ type: "text", text: "Não autenticado." }], isError: true };
    }
    const supabase = supabaseForUser(ctx);
    let query = supabase
      .from("leads")
      .select(
        "id, created_at, nome, email, whatsapp, origem, cidade, regiao, pais, utm_source, utm_medium, utm_campaign",
      )
      .order("created_at", { ascending: false })
      .limit(limit ?? 50);

    if (since) query = query.gte("created_at", since);
    if (search) query = query.or(`nome.ilike.%${search}%,email.ilike.%${search}%`);

    const { data, error } = await query;
    if (error) return { content: [{ type: "text", text: error.message }], isError: true };

    return {
      content: [{ type: "text", text: JSON.stringify(data ?? [], null, 2) }],
      structuredContent: { leads: data ?? [], count: data?.length ?? 0 },
    };
  },
});
