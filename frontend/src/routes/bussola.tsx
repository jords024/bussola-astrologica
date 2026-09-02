import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { fbqTrack, fbqTrackCustom, trackPageView } from "../lib/fbq";
import heroAsset from "../assets/bussola-hero.png.asset.json";
import heroMobileAsset from "../assets/bussola-hero-mobile.png.asset.json";
import retratoAsset from "../assets/crassus-retrato.webp";

import HeroBussolaV2 from "../components/bussola/hero-bussola-v2";
import BlocoVoceJaSePegouPensando from "../components/bussola/bloco-voce-ja-se-pegou-pensando";
import BlocoCulpaNaoESua from "../components/bussola/bloco-culpa-nao-e-sua";
import BlocoOQueSaoTransitos from "../components/bussola/bloco-o-que-sao-transitos";
import BlocoMecanismo12Portas from "../components/bussola/bloco-mecanismo-12-portas";
import BlocoComoFunciona from "../components/bussola/bloco-como-funciona";
import BlocoPortasInterativas from "../components/bussola/bloco-portas-interativas";
import BlocoParaQuemE from "../components/bussola/bloco-para-quem-e";
import BlocoHistoriaCrassus from "../components/bussola/bloco-historia-crassus";
import BlocoOfertaHeadline from "../components/bussola/bloco-oferta-headline";
import BlocoOfertaConteudo from "../components/bussola/bloco-oferta-conteudo";
import BlocoOfertaFinal from "../components/bussola/bloco-oferta-final";
import BlocoFAQ from "../components/bussola/bloco-faq";
import RodapeBussola from "../components/bussola/rodape-bussola";
import WhatsappButton from "../components/bussola/whatsapp-button";

const DESCRICAO =
  "Aprenda a identificar quais portas estão abertas para você agora, no dinheiro, no amor, na carreira e em outras áreas da vida. Acesso imediato, 7 dias de garantia.";

export const HOTMART_CHECKOUT_URL =
  "https://pay.hotmart.com/Q107238351O?checkoutMode=10&name=ARYARAJ+ALVES+FERNANDES&phonenumber=8588146141&phoneac=55";

export function buildHotmartCheckoutUrl(search?: string): string {
  const url = new URL(HOTMART_CHECKOUT_URL);

  if (search) {
    const currentParams = new URLSearchParams(search);
    ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "src", "sck"].forEach(
      (param) => {
        const val = currentParams.get(param);
        if (val) url.searchParams.set(param, val);
      },
    );
  }
  return url.toString();
}

export const Route = createFileRoute("/bussola")({
  head: () => ({
    meta: [
      { title: "Bússola Astrológica — Saiba quais portas estão abertas agora" },
      { name: "description", content: DESCRICAO },
      {
        property: "og:title",
        content: "Bússola Astrológica — Saiba quais portas estão abertas agora",
      },
      { property: "og:description", content: DESCRICAO },
      { property: "og:type", content: "website" },
      { property: "og:image", content: heroAsset.url },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:image", content: heroAsset.url },
    ],
    links: [
      {
        rel: "preconnect",
        href: "https://pay.hotmart.com",
        crossOrigin: "anonymous",
      },
      {
        rel: "dns-prefetch",
        href: "https://pay.hotmart.com",
      },
      {
        rel: "preload",
        as: "image",
        href: heroMobileAsset.url,
        media: "(max-width: 767px)",
      },
      {
        rel: "preload",
        as: "image",
        href: heroAsset.url,
        media: "(min-width: 768px)",
      },
    ],
  }),
  component: BussolaPage,
});

function BussolaPage() {
  const pixelFired = useRef(false);

  useEffect(() => {
    if (pixelFired.current) return;
    pixelFired.current = true;
    trackPageView();
  }, []);

  // Pré-carrega a foto do Crassus (usada no bloco de autoridade) em segundo
  // plano, pra já estar em cache quando a seção entra em vista.
  useEffect(() => {
    const prefetch = () => {
      const img = new Image();
      img.src = retratoAsset;
    };

    if (typeof window !== "undefined") {
      if ("requestIdleCallback" in window) {
        const handle = (
          window as unknown as { requestIdleCallback: (cb: () => void) => number }
        ).requestIdleCallback(prefetch);
        return () => {
          if ("cancelIdleCallback" in window) {
            (window as unknown as { cancelIdleCallback: (id: number) => void }).cancelIdleCallback(
              handle,
            );
          }
        };
      } else {
        const timer = setTimeout(prefetch, 300);
        return () => clearTimeout(timer);
      }
    }
    return undefined;
  }, []);

  // Dificulta o "salvar imagem" / copiar conteúdo da página
  useEffect(() => {
    const preventContextMenu = (e: MouseEvent) => e.preventDefault();
    const preventDragStart = (e: DragEvent) => e.preventDefault();
    document.addEventListener("contextmenu", preventContextMenu);
    document.addEventListener("dragstart", preventDragStart);
    return () => {
      document.removeEventListener("contextmenu", preventContextMenu);
      document.removeEventListener("dragstart", preventDragStart);
    };
  }, []);

  const handleScrollToOferta = () => {
    fbqTrackCustom("ClicouHeroCta", { destino: "oferta" });
    const el = document.getElementById("oferta");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const handleDirectCheckout = (origem = "oferta_final") => {
    fbqTrack("InitiateCheckout", { content_name: "Bussola Astrologica" });
    fbqTrackCustom("ClicouCheckout", { origem });

    if (typeof window !== "undefined") {
      const search = window.location.search || "";
      const targetUrl = buildHotmartCheckoutUrl(search);
      window.location.href = targetUrl;
    }
  };

  return (
    <main className="relative w-full select-none bg-background font-body text-foreground selection:bg-gold selection:text-background">
      <HeroBussolaV2 onCheckout={handleScrollToOferta} />
      <BlocoVoceJaSePegouPensando />
      <BlocoCulpaNaoESua />
      <BlocoOQueSaoTransitos />
      <BlocoMecanismo12Portas />
      <BlocoComoFunciona />
      <BlocoPortasInterativas />
      <BlocoParaQuemE />
      <div id="oferta">
        <BlocoOfertaHeadline />
        <BlocoOfertaConteudo />
        <BlocoOfertaFinal onCheckout={() => handleDirectCheckout("oferta_final")} />
      </div>
      <BlocoHistoriaCrassus />
      <BlocoFAQ />
      <RodapeBussola />

      <WhatsappButton />
    </main>
  );
}
