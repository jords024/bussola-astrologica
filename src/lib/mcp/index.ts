import { auth, defineMcp } from "@lovable.dev/mcp-js";
import listLeadsTool from "./tools/list-leads";
import leadStatsTool from "./tools/lead-stats";

const projectRef = import.meta.env["VITE_SUPABASE_PROJECT_ID"] ?? "project-ref-unset";

export default defineMcp({
  name: "astrowake",
  title: "Astrowake",
  version: "0.1.0",
  instructions:
    "Ferramentas do Astrowake (landing page do Crassus Gobbi). Use `list_leads` para consultar os leads captados e `lead_stats` para um resumo com volume, horário de pico, cidades e origens. Todas exigem uma conta de administrador do app.",
  auth: auth.oauth.issuer({
    issuer: `https://${projectRef}.supabase.co/auth/v1`,
    acceptedAudiences: "authenticated",
  }),
  tools: [listLeadsTool, leadStatsTool],
});
