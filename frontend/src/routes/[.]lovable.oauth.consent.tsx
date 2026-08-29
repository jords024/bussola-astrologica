import { createFileRoute, redirect } from "@tanstack/react-router";
import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";

type OAuthDetails = {
  client?: { name?: string } | null;
  redirect_url?: string;
  redirect_to?: string;
};

type OAuthApi = {
  getAuthorizationDetails: (
    id: string,
  ) => Promise<{ data: OAuthDetails | null; error: Error | null }>;
  approveAuthorization: (id: string) => Promise<{ data: OAuthDetails | null; error: Error | null }>;
  denyAuthorization: (id: string) => Promise<{ data: OAuthDetails | null; error: Error | null }>;
};

const oauth = () => (supabase.auth as unknown as { oauth: OAuthApi }).oauth;

export const Route = createFileRoute("/.lovable/oauth/consent")({
  ssr: false,
  validateSearch: (s: Record<string, unknown>) => ({
    authorization_id: typeof s["authorization_id"] === "string" ? s["authorization_id"] : "",
  }),
  beforeLoad: async ({ search, location }) => {
    if (!search.authorization_id) throw new Error("Missing authorization_id");
    const { data } = await supabase.auth.getSession();
    const next = location.pathname + location.searchStr;
    if (!data.session) throw redirect({ to: "/auth", search: { next } });
  },
  loader: async ({ location }) => {
    const authorizationId = new URLSearchParams(location.search).get("authorization_id")!;
    const { data, error } = await oauth().getAuthorizationDetails(authorizationId);
    if (error) throw error;
    const immediate = data?.redirect_url ?? data?.redirect_to;
    if (immediate && !data?.client) throw redirect({ href: immediate });
    return data;
  },
  component: Consent,
  errorComponent: ({ error }) => (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-center text-sm text-muted-foreground">
      Não foi possível carregar esta solicitação: {String((error as Error)?.message ?? error)}
    </main>
  ),
});

function Consent() {
  const details = Route.useLoaderData();
  const { authorization_id } = Route.useSearch();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const clientName = details?.client?.name ?? "um aplicativo";

  async function decide(approve: boolean) {
    setBusy(true);
    setError(null);
    const { data, error: err } = approve
      ? await oauth().approveAuthorization(authorization_id)
      : await oauth().denyAuthorization(authorization_id);
    if (err) {
      setBusy(false);
      setError(err.message);
      return;
    }
    const target = data?.redirect_url ?? data?.redirect_to;
    if (!target) {
      setBusy(false);
      setError("O servidor de autorização não retornou um redirecionamento.");
      return;
    }
    window.location.href = target;
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 py-16">
      <div className="w-full max-w-md rounded-2xl border border-gold/25 bg-white/[0.03] p-8 backdrop-blur">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-gold/40 bg-gold/10">
          <ShieldCheck className="h-6 w-6 text-gold" />
        </div>
        <h1 className="mt-6 text-center font-display text-3xl text-white">Conectar {clientName}</h1>
        <p className="mt-3 text-center text-sm text-muted-foreground">
          {clientName} poderá acessar os dados do Astrowake como você, incluindo os leads que a sua
          conta pode ver.
        </p>

        {error && <p className="mt-4 text-center text-sm text-gold-soft">{error}</p>}

        <div className="mt-8 space-y-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => decide(true)}
            className="w-full rounded-full bg-gold px-6 py-3.5 text-sm font-bold text-background transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {busy ? "Aguarde…" : "Aprovar acesso"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => decide(false)}
            className="w-full rounded-full border border-gold/25 px-6 py-3.5 text-sm font-semibold text-foreground/80 transition-colors hover:text-gold-soft disabled:opacity-60"
          >
            Recusar
          </button>
        </div>
      </div>
    </main>
  );
}

export default Consent;
