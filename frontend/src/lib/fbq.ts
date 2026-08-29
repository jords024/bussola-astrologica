export const META_PIXEL_ID = "776532458708522";

declare global {
  interface Window {
    fbq?: (...args: unknown[]) => void;
  }
}

export function fbqTrack(event: string, params?: Record<string, unknown>) {
  if (typeof window === "undefined" || typeof window.fbq !== "function") return;
  if (params) {
    window.fbq("track", event, params);
  } else {
    window.fbq("track", event);
  }
}

export function fbqTrackCustom(event: string, params?: Record<string, unknown>) {
  if (typeof window === "undefined" || typeof window.fbq !== "function") return;
  if (params) {
    window.fbq("trackCustom", event, params);
  } else {
    window.fbq("trackCustom", event);
  }
}

// O script base já dispara o PageView do carregamento inicial.
// Este helper evita duplicar esse primeiro disparo em navegações SPA.
let initialPageViewDone = false;

export function trackPageView() {
  if (!initialPageViewDone) {
    initialPageViewDone = true;
    return;
  }
  fbqTrack("PageView");
}
