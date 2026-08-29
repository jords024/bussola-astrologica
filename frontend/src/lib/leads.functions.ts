import { createServerFn } from "@tanstack/react-start";
import { getRequest, getRequestHeader } from "@tanstack/react-start/server";
import { requireAuth } from "./auth-middleware";
import { query } from "./db";
import {
  hashPassword,
  comparePassword,
  createAuthToken,
  getUserRoles,
  hasRole,
  countAdmins,
  addRole,
} from "./auth.server";

export type LeadInput = {
  nome: string;
  email?: string | undefined;
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

export function clean(value: unknown, max = 300): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.slice(0, max);
}

export const submitLead = createServerFn({ method: "POST" })
  .validator((data: LeadInput) => {
    const nome = clean(data?.nome, 120);
    const rawEmail = clean(data?.email, 160);
    const whatsapp = clean(data?.whatsapp, 40);
    if (!nome || !whatsapp) throw new Error("Dados incompletos");

    let email: string | null = null;
    if (rawEmail) {
      const normalized = rawEmail.toLowerCase();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized)) {
        throw new Error("E-mail inválido");
      }
      email = normalized;
    }

    return {
      nome,
      email,
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
    const cf = (request as unknown as { cf?: Record<string, unknown> })?.cf;

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

    const userAgent = clean(getRequestHeader("user-agent"), 400);

    console.log(
      `\n🚀 [NOVO LEAD CAPTADO] Nome: "${data.nome}" | WhatsApp: "${data.whatsapp}" | Origem: "${data.origem || "checkout_pre_populado"}"`,
    );

    await query(
      `INSERT INTO leads (
        nome, email, whatsapp, origem, ip, cidade, regiao, pais, timezone, user_agent, referrer, utm_source, utm_medium, utm_campaign
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
      [
        data.nome,
        data.email,
        data.whatsapp,
        data.origem,
        ip,
        cidade,
        regiao,
        pais,
        timezone,
        userAgent,
        data.referrer,
        data.utm_source,
        data.utm_medium,
        data.utm_campaign,
      ],
    );

    // Disparo do webhook para o ZapVoice com os dados essenciais do checkout pré-populado
    try {
      const cleanDigits = data.whatsapp.replace(/\D/g, "");

      const hotmartPayload = {
        event: "PURCHASE_OUT_OF_SHOPPING_CART",
        checkout_pre_populado: true,
        is_checkout_pre_populado: true,
        tipo: "checkout_pre_populado",
        origem: data.origem || "checkout_pre_populado",
        nome: data.nome,
        name: data.nome,
        whatsapp: data.whatsapp,
        phone: data.whatsapp,
        data: {
          product: {
            name: "Bússola Astrológica",
          },
          buyer: {
            name: data.nome,
            phone: data.whatsapp,
            checkout_phone: cleanDigits,
          },
        },
      };

      console.log(
        `📡 [WEBHOOK DISPARADO] Enviando para ZapVoice (https://zapvoicecrassos.aryaraj.shop/api/webhooks/bussula-hotmart)`,
      );
      console.log(`📦 [WEBHOOK JSON PAYLOAD]:\n${JSON.stringify(hotmartPayload, null, 2)}`);

      const webhookRes = await fetch(
        "https://zapvoicecrassos.aryaraj.shop/api/webhooks/bussula-hotmart",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(hotmartPayload),
          signal: AbortSignal.timeout(5000),
        },
      );

      const resJson = await webhookRes.json().catch(() => null);

      if (!webhookRes.ok) {
        console.warn(
          `⚠️ [WEBHOOK RESPOSTA COM ERRO] Status: ${webhookRes.status} ${webhookRes.statusText} | Resposta:`,
          resJson,
        );
      } else {
        console.info(`✅ [WEBHOOK SUCESSO] Resposta do ZapVoice:`, resJson);
      }
    } catch (webhookError) {
      console.error("❌ [WEBHOOK FALHA]: Erro ao enviar webhook para ZapVoice:", webhookError);
    }

    return { ok: true };
  });

export const listLeads = createServerFn({ method: "GET" })
  .middleware([requireAuth])
  .handler(async ({ context }) => {
    const isAdmin = await hasRole(context.userId, "admin");
    if (!isAdmin) throw new Error("Forbidden");

    const result = await query<LeadRow>("SELECT * FROM leads ORDER BY created_at DESC LIMIT 1000");

    return { leads: result.rows };
  });

export const checkIsAdmin = createServerFn({ method: "GET" })
  .middleware([requireAuth])
  .handler(async ({ context }) => {
    const isAdmin = await hasRole(context.userId, "admin");
    return { isAdmin };
  });

// Bootstrap: o primeiro usuário cadastrado vira administrador.
export const claimAdminIfFirst = createServerFn({ method: "POST" })
  .middleware([requireAuth])
  .handler(async ({ context }) => {
    const adminCount = await countAdmins();
    if (adminCount > 0) return { promoted: false };
    await addRole(context.userId, "admin");
    return { promoted: true };
  });

// Autenticação: Registro de usuário
export const registerUser = createServerFn({ method: "POST" })
  .validator((data: { email?: unknown; password?: unknown }) => {
    const email = clean(data?.email, 160);
    const password = typeof data?.password === "string" ? data.password : "";
    if (!email || !password) throw new Error("E-mail e senha são obrigatórios.");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error("E-mail inválido.");
    if (password.length < 6) throw new Error("A senha deve ter pelo menos 6 caracteres.");
    return { email: email.toLowerCase(), password };
  })
  .handler(async ({ data }) => {
    const existing = await query<{ id: string }>("SELECT id FROM users WHERE email = $1", [
      data.email,
    ]);
    if (existing.rows.length > 0) {
      throw new Error("Este e-mail já está cadastrado.");
    }

    const passwordHash = await hashPassword(data.password);
    const userRes = await query<{ id: string; email: string }>(
      "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING id, email",
      [data.email, passwordHash],
    );
    const newUser = userRes.rows[0];

    // O primeiro usuário a se registrar ganha o papel de admin automaticamente
    const totalUsersRes = await query<{ count: string }>("SELECT COUNT(*) as count FROM users");
    const totalUsers = parseInt(totalUsersRes.rows[0]?.count || "1", 10);
    const initialRole: "admin" | "user" = totalUsers === 1 ? "admin" : "user";

    await addRole(newUser.id, initialRole);
    const roles = [initialRole];

    const token = await createAuthToken({
      id: newUser.id,
      email: newUser.email,
      roles,
    });

    return {
      token,
      user: {
        id: newUser.id,
        email: newUser.email,
        roles,
      },
    };
  });

// Autenticação: Login
export const loginUser = createServerFn({ method: "POST" })
  .validator((data: { email?: unknown; password?: unknown }) => {
    const email = clean(data?.email, 160);
    const password = typeof data?.password === "string" ? data.password : "";
    if (!email || !password) throw new Error("E-mail e senha são obrigatórios.");
    return { email: email.toLowerCase(), password };
  })
  .handler(async ({ data }) => {
    const result = await query<{ id: string; email: string; password_hash: string }>(
      "SELECT id, email, password_hash FROM users WHERE email = $1",
      [data.email],
    );

    if (result.rows.length === 0) {
      throw new Error("E-mail ou senha inválidos.");
    }

    const user = result.rows[0];
    const match = await comparePassword(data.password, user.password_hash);
    if (!match) {
      throw new Error("E-mail ou senha inválidos.");
    }

    let roles = await getUserRoles(user.id);
    if (roles.length === 0) {
      const adminCount = await countAdmins();
      const defaultRole = adminCount === 0 ? "admin" : "user";
      await addRole(user.id, defaultRole);
      roles = [defaultRole];
    }

    const token = await createAuthToken({
      id: user.id,
      email: user.email,
      roles,
    });

    return {
      token,
      user: {
        id: user.id,
        email: user.email,
        roles,
      },
    };
  });

// Autenticação: Obter usuário atual
export const getCurrentUser = createServerFn({ method: "GET" })
  .middleware([requireAuth])
  .handler(async ({ context }) => {
    return {
      user: {
        id: context.userId,
        email: context.email,
        roles: context.roles,
      },
    };
  });
