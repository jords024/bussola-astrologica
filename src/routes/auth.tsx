import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { Lock, LogIn } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { claimAdminIfFirst } from "@/lib/leads.functions";

function safeNext(value: unknown): string | undefined {
  return typeof value === "string" && value.startsWith("/") && !value.startsWith("//") ? value : undefined;
}

export const Route = createFileRoute("/auth")({
  validateSearch: (s: Record<string, unknown>): { next?: string } => {
    const next = safeNext(s["next"]);
    return next ? { next } : {};
  },
  head: () => ({
    meta: [
      { title: "Acesso Administrativo — Astrowake" },
      { name: "description", content: "Área restrita de administração dos leads do evento Astrowake." },
      { name: "robots", content: "noindex" },
      { property: "og:title", content: "Acesso Administrativo — Astrowake" },
      { property: "og:description", content: "Área restrita de administração dos leads do evento Astrowake." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: AuthPage,
});

function AuthPage() {
  const navigate = useNavigate();
  const { next } = Route.useSearch();
  const goNext = () => {
    if (next) window.location.href = next;
    else navigate({ to: "/admin" });
  };
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        if (next) window.location.href = next;
        else navigate({ to: "/admin" });
      }
    });
  }, [navigate, next]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      if (mode === "signup") {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: `${window.location.origin}${next ?? "/admin"}` },
        });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        setMessage("Conta criada. Confirme o e-mail para acessar o painel.");
        return;
      }
      await claimAdminIfFirst().catch(() => undefined);
      goNext();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Não foi possível entrar.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6 py-16">
      <div className="w-full max-w-md rounded-2xl border border-gold/25 bg-white/[0.03] p-8 backdrop-blur">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-gold/40 bg-gold/10">
          <Lock className="h-6 w-6 text-gold" />
        </div>
        <h1 className="mt-6 text-center font-display text-3xl text-white">Painel Astrowake</h1>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          {mode === "login" ? "Entre para ver os leads captados." : "Crie o acesso de administrador."}
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label htmlFor="email" className="mb-1.5 block text-xs font-semibold text-foreground/80">
              E-mail
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-input bg-background/70 px-4 py-3 text-sm text-white focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1.5 block text-xs font-semibold text-foreground/80">
              Senha
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-input bg-background/70 px-4 py-3 text-sm text-white focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
            />
          </div>

          {message && <p className="text-sm text-gold-soft">{message}</p>}

          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-gold px-6 py-3.5 text-sm font-bold text-background transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            <LogIn className="h-4 w-4" />
            {loading ? "Aguarde…" : mode === "login" ? "Entrar" : "Criar acesso"}
          </button>
        </form>

        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "signup" : "login")}
          className="mt-6 w-full text-center text-xs text-muted-foreground underline underline-offset-4 hover:text-gold-soft"
        >
          {mode === "login" ? "Primeiro acesso? Criar conta de administrador" : "Já tenho acesso — entrar"}
        </button>
      </div>
    </div>
  );
}

export default AuthPage;
