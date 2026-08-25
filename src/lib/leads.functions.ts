import { createServerFn } from "@tanstack/react-start";
import { getRequest, getRequestHeader } from "@tanstack/react-start/server";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";

export type LeadInput = {
  nome: string;
  email: string;
  whatsapp: string;
  origem?: string | undefined;
  referrer?: string | undefined;
  utm_source?: string | undefined;
  utm_medium?: string | undefined;
  utm_campaign?: string | undefined;
};

export type LeadRow = {
  id: string;
  created_at: string;
  nome: string;
  email: string;
  whatsapp: string;
  origem: string | null;
  ip: string | null;
  cidade: string | null;
  regiao: string | null;
  pais: string | null;
  timezone: string | null;
  user_agent: string | null;
  referrer: string | null;
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
};

function clean(value: unknown, max = 300): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.slice(0, max);
}

export const submitLead = createServerFn({ method: "POST" })
  .inputValidator((data: LeadInput) => {
    const nome = clean(data?.nome, 120);
    const email = clean(data?.email, 160);
    const whatsapp = clean(data?.whatsapp, 40);
    if (!nome || !email || !whatsapp) throw new Error("Dados incompletos");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error("E-mail inválido");
    return {
      nome,
      email: email.toLowerCase(),
      whatsapp,
      origem: clean(data?.origem, 80),
      referrer: clean(data?.referrer, 300),
      utm_source: clean(data?.utm_source, 120),
      utm_medium: clean(data?.utm_medium, 120),
      utm_campaign: clean(data?.utm_campaign, 120),
    };
  })
  .handler(async ({ data }) => {
    const request = getRequest();
    const cf = (request as unknown as { cf?: Record<string, unknown> }).cf;

    const ip =
      getRequestHeader("cf-connecting-ip") ??
      getRequestHeader("x-real-ip") ??
      getRequestHeader("x-forwarded-for")?.split(",")[0]?.trim() ??
      null;

    let cidade = clean(cf?.["city"]);
    let regiao = clean(cf?.["region"]);
    let pais = clean(cf?.["country"]) ?? clean(getRequestHeader("cf-ipcountry"));
    let timezone = clean(cf?.["timezone"]);

    // Fallback: geolocalização por IP quando os cabeçalhos da borda não trazem cidade.
    if (!cidade && ip) {
      try {
        const res = await fetch(`https://ipapi.co/${ip}/json/`, {
          signal: AbortSignal.timeout(2500),
        });
        if (res.ok) {
          const geo = (await res.json()) as Record<string, unknown>;
          cidade = cidade ?? clean(geo["city"]);
          regiao = regiao ?? clean(geo["region"]);
          pais = pais ?? clean(geo["country_code"]);
          timezone = timezone ?? clean(geo["timezone"]);
        }
      } catch {
        // geolocalização é opcional — nunca bloqueia o lead
      }
    }

    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { error } = await supabaseAdmin.from("leads").insert({
      ...data,
      ip,
      cidade,
      regiao,
      pais,
      timezone,
      user_agent: clean(getRequestHeader("user-agent"), 400),
    });
    if (error) throw new Error(error.message);
    return { ok: true };
  });

export const listLeads = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const { data: isAdmin } = await context.supabase.rpc("has_role", {
      _user_id: context.userId,
      _role: "admin",
    });
    if (!isAdmin) throw new Error("Forbidden");

    const { data, error } = await context.supabase
      .from("leads")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(1000);
    if (error) throw new Error(error.message);
    return { leads: (data ?? []) as LeadRow[] };
  });

export const checkIsAdmin = createServerFn({ method: "GET" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const { data } = await context.supabase.rpc("has_role", {
      _user_id: context.userId,
      _role: "admin",
    });
    return { isAdmin: Boolean(data) };
  });

// Bootstrap: o primeiro usuário cadastrado vira administrador.
export const claimAdminIfFirst = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .handler(async ({ context }) => {
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { count, error } = await supabaseAdmin
      .from("user_roles")
      .select("id", { count: "exact", head: true })
      .eq("role", "admin");
    if (error) throw new Error(error.message);
    if ((count ?? 0) > 0) return { promoted: false };
    const { error: insertError } = await supabaseAdmin
      .from("user_roles")
      .insert({ user_id: context.userId, role: "admin" });
    if (insertError) throw new Error(insertError.message);
    return { promoted: true };
  });
