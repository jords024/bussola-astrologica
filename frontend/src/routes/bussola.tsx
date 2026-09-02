import { createFileRoute } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useEffect, useRef, useState } from "react";
import { fbqTrack, fbqTrackCustom, trackPageView } from "../lib/fbq";
import { submitLead } from "../lib/leads.functions";
import CheckoutModal, { type CheckoutFormData } from "../components/bussola/checkout-modal";
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
        rel: "preconnect",
        href: "https://zapvoicecrassos.aryaraj.shop",
        crossOrigin: "anonymous",
      },
      {
        rel: "dns-prefetch",
        href: "https://zapvoicecrassos.aryaraj.shop",
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

const HOTMART_BASE_URL = "https://pay.hotmart.com/Q107238351O";

function BussolaPage() {
  const pixelFired = useRef(false);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [checkoutOrigem, setCheckoutOrigem] = useState("hero_bussola");
  const [isRedirecting, setIsRedirecting] = useState(false);
  const sendLead = useServerFn(submitLead);

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

  const handleOpenCheckout = (origem = "hero_bussola") => {
    setCheckoutOrigem(origem);
    setIsCheckoutOpen(true);
  };

  const handleProcessCheckout = async (data: CheckoutFormData) => {
    setIsRedirecting(true);
    try {
      // Captura parâmetros UTM e origem da navegação
      const currentParams =
        typeof window !== "undefined"
          ? new URLSearchParams(window.location.search)
          : new URLSearchParams();
      const utm_source = currentParams.get("utm_source") || undefined;
      const utm_medium = currentParams.get("utm_medium") || undefined;
      const utm_campaign = currentParams.get("utm_campaign") || undefined;
      const referrer = typeof document !== "undefined" ? document.referrer : undefined;
      const ddi = data.ddi || "55";
      const fullPhone = `+${ddi}${data.whatsapp}`;

      // 1. Salva o lead no banco de dados e dispara webhook ZapVoice (com timeout resiliente de 3.5s no cliente)
      try {
        const sendLeadPromise = sendLead({
          data: {
            nome: data.nome,
            whatsapp: fullPhone,
            origem: `checkout_pre_populado_${checkoutOrigem}`,
            referrer,
            utm_source,
            utm_medium,
            utm_campaign,
          },
        });
        const clientTimeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error("Lead submission client timeout")), 3500),
        );

        await Promise.race([sendLeadPromise, clientTimeoutPromise]);
      } catch (leadError) {
        console.warn(
          "Aviso: falha ou timeout ao salvar lead pré-checkout, prosseguindo com Hotmart:",
          leadError,
        );
      }

      // 2. Dispara eventos de Pixel Meta
      fbqTrack("Lead", { content_name: "Bussola Astrologica" });
      fbqTrack("InitiateCheckout", { content_name: "Bussola Astrologica" });
      fbqTrackCustom("ClicouCheckout", { origem: checkoutOrigem });

      // 3. Constrói a URL pré-populada da Hotmart
      const hotmartUrl = new URL(HOTMART_BASE_URL);
      hotmartUrl.searchParams.set("checkoutMode", "10");
      hotmartUrl.searchParams.set("name", data.nome);
      if (data.whatsapp) {
        hotmartUrl.searchParams.set("phonenumber", data.whatsapp);
        hotmartUrl.searchParams.set("phoneac", ddi);
      }

      // Repassa parâmetros UTM existentes na URL atual para a Hotmart
      if (typeof window !== "undefined") {
        const searchParams = new URLSearchParams(window.location.search);
        [
          "utm_source",
          "utm_medium",
          "utm_campaign",
          "utm_content",
          "utm_term",
          "src",
          "sck",
        ].forEach((param) => {
          const val = searchParams.get(param);
          if (val) hotmartUrl.searchParams.set(param, val);
        });
        window.location.href = hotmartUrl.toString();
      }
    } catch (err) {
      console.error("Erro no processamento do checkout:", err);
      // Fallback: redireciona mesmo em caso de erro
      const ddi = data.ddi || "55";
      window.location.href = `${HOTMART_BASE_URL}?checkoutMode=10&name=${encodeURIComponent(data.nome)}&phonenumber=${encodeURIComponent(data.whatsapp)}&phoneac=${ddi}`;
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
        <BlocoOfertaFinal onCheckout={() => handleOpenCheckout("oferta_final")} />
      </div>
      <BlocoHistoriaCrassus />
      <BlocoFAQ />
      <RodapeBussola />

      <WhatsappButton />

      {/* Modal de Pré-Checkout Pré-Populado */}
      <CheckoutModal
        isOpen={isCheckoutOpen}
        onClose={() => !isRedirecting && setIsCheckoutOpen(false)}
        onSubmit={handleProcessCheckout}
        isLoading={isRedirecting}
      />
    </main>
  );
}
