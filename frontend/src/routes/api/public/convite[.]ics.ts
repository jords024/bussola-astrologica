import { createFileRoute } from "@tanstack/react-router";
import { buildIcs } from "@/lib/event";

export const Route = createFileRoute("/api/public/convite.ics")({
  server: {
    handlers: {
      GET: async () =>
        new Response(buildIcs(), {
          headers: {
            "Content-Type": "text/calendar; charset=utf-8",
            "Content-Disposition": 'attachment; filename="astrowake.ics"',
            "Cache-Control": "public, max-age=3600",
          },
        }),
    },
  },
});
