import "./lib/error-capture";

import zlib from "node:zlib";
import { promisify } from "node:util";
import { consumeLastCapturedError } from "./lib/error-capture";
import { renderErrorPage } from "./lib/error-page";

const gzipAsync = promisify(zlib.gzip);

type ServerEntry = {
  fetch: (request: Request, env: unknown, ctx: unknown) => Promise<Response> | Response;
};

let serverEntryPromise: Promise<ServerEntry> | undefined;

async function getServerEntry(): Promise<ServerEntry> {
  if (!serverEntryPromise) {
    serverEntryPromise = import("@tanstack/react-start/server-entry").then(
      (m) => (m.default ?? m) as ServerEntry,
    );
  }
  return serverEntryPromise;
}

async function compressResponseIfNeeded(request: Request, response: Response): Promise<Response> {
  const acceptEncoding = request.headers.get("accept-encoding") ?? "";
  if (!acceptEncoding.includes("gzip")) return response;

  const contentEncoding = response.headers.get("content-encoding");
  if (contentEncoding) return response;

  const contentType = response.headers.get("content-type") ?? "";
  const isCompressible =
    contentType.includes("text/html") ||
    contentType.includes("application/json") ||
    contentType.includes("text/css") ||
    contentType.includes("application/javascript") ||
    contentType.includes("text/plain") ||
    contentType.includes("image/svg+xml");

  if (!isCompressible) return response;

  const buffer = Buffer.from(await response.arrayBuffer());
  if (buffer.length < 512) {
    return new Response(buffer, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  }

  const compressed = await gzipAsync(buffer);
  const newHeaders = new Headers(response.headers);
  newHeaders.set("content-encoding", "gzip");
  newHeaders.set("content-length", String(compressed.length));
  newHeaders.delete("etag");

  return new Response(compressed, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}

// h3 swallows in-handler throws into a normal 500 Response with body
// {"unhandled":true,"message":"HTTPError"} — try/catch alone never fires for those.
async function normalizeCatastrophicSsrResponse(response: Response): Promise<Response> {
  if (response.status < 500) return response;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return response;

  const body = await response.clone().text();
  if (!isH3SwallowedErrorBody(body)) return response;

  console.error(consumeLastCapturedError() ?? new Error(`h3 swallowed SSR error: ${body}`));
  return new Response(renderErrorPage(), {
    status: 500,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}

function isH3SwallowedErrorBody(body: string): boolean {
  try {
    const payload = JSON.parse(body) as { unhandled?: unknown; message?: unknown };
    return payload.unhandled === true && payload.message === "HTTPError";
  } catch {
    return false;
  }
}

export default {
  async fetch(request: Request, env: unknown, ctx: unknown) {
    try {
      const handler = await getServerEntry();
      const rawResponse = await handler.fetch(request, env, ctx);
      const normalized = await normalizeCatastrophicSsrResponse(rawResponse);
      return await compressResponseIfNeeded(request, normalized);
    } catch (error) {
      console.error(error);
      const errRes = new Response(renderErrorPage(), {
        status: 500,
        headers: { "content-type": "text/html; charset=utf-8" },
      });
      return await compressResponseIfNeeded(request, errRes);
    }
  },
};
