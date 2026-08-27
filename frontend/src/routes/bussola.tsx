import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { fbqTrack, fbqTrackCustom, trackPageView } from "../lib/fbq";
import heroAsset from "../assets/bussola-hero.png.asset.json";
import heroMobileAsset from "../assets/bussola-hero-mobile.png.asset.json";
import fluiAsset from "../assets/bussola-tudo-flui.png.asset.json";
import fluiMobileAsset from "../assets/bussola-tudo-flui-mobile.png.asset.json";
import semanaAsset from "../assets/bussola-semana-seguinte.png.asset.json";
import retratoAsset from "../assets/crassus-retrato.webp";
import erroAsset from "../assets/bussola-erro-nunca-foi-voce.png.asset.json";

import portasSeAbrindoAsset from "../assets/bussola-portas-se-abrindo.webp";
import esforcouODobroAsset from "../assets/bussola-esforcou-o-dobro.webp";
import precisavaSeEsforcarAsset from "../assets/bussola-precisava-se-esforcar.webp";
import procurouExplicacaoAsset from "../assets/bussola-procurou-explicacao.webp";
import naoFoiFaltaDeEsforcoAsset from "../assets/bussola-nao-foi-falta-de-esforco.webp";
import dozePortasAsset from "../assets/bussola-12-portas.webp";
import portasNaoVivemMesmoCicloAsset from "../assets/bussola-portas-nao-vivem-mesmo-ciclo.webp";
import portaAbertaVocePercebeAsset from "../assets/bussola-porta-aberta-voce-percebe.webp";
import voceChamaDeSorteAsset from "../assets/bussola-voce-chama-de-sorte.webp";
import portaNaoCedeAsset from "../assets/bussola-porta-nao-cede.webp";
import portaErradaAsset from "../assets/bussola-porta-errada.webp";
import aprenderLerPortasAsset from "../assets/bussola-aprender-ler-portas.webp";
import mesmoSignoMomentosDiferentesAsset from "../assets/bussola-mesmo-signo-momentos-diferentes.webp";
import horoscopoGenericoRadioAsset from "../assets/bussola-horoscopo-generico-radio.webp";
import comoIdentificaPortaAbertaAsset from "../assets/bussola-como-identifica-porta-aberta.webp";
import passo1AbraMapaAsset from "../assets/bussola-passo1-abra-mapa.webp";
import passo2DescubraPortaAsset from "../assets/bussola-passo2-descubra-porta.webp";
import passo3ConsulteInterpretacaoAsset from "../assets/bussola-passo3-consulte-interpretacao.webp";
import eProntoAsset from "../assets/bussola-e-pronto.webp";
import ondePararDeForcarAsset from "../assets/bussola-onde-parar-de-forcar.webp";
import nemTodaFasePedeEsforcoAsset from "../assets/bussola-nem-toda-fase-pede-esforco.webp";

import HeroBussola from "../components/bussola/hero-bussola";
import BlocoTudoFlui from "../components/bussola/bloco-tudo-flui";
import BlocoSemanaSeguinte from "../components/bussola/bloco-semana-seguinte";
import BlocoRelogioCosmico from "../components/bussola/bloco-relogio-cosmico";
import Bloco12Casas from "../components/bussola/bloco-12-casas";
import BlocoHistoriaCrassus from "../components/bussola/bloco-historia-crassus";
import BlocoErroNuncaFoiVoce from "../components/bussola/bloco-erro-nunca-foi-voce";
import BlocoPortasSeAbrindo from "../components/bussola/bloco-portas-se-abrindo";
import BlocoEsforcouODobro from "../components/bussola/bloco-esforcou-o-dobro";
import BlocoPrecisavaSeEsforcar from "../components/bussola/bloco-precisava-se-esforcar";
import BlocoProcurouExplicacao from "../components/bussola/bloco-procurou-explicacao";
import BlocoNaoFoiFaltaDeEsforco from "../components/bussola/bloco-nao-foi-falta-de-esforco";
import Bloco12Portas from "../components/bussola/bloco-12-portas";
import BlocoPortasNaoVivemMesmoCiclo from "../components/bussola/bloco-portas-nao-vivem-mesmo-ciclo";
import BlocoPortaAbertaVocePercebe from "../components/bussola/bloco-porta-aberta-voce-percebe";
import BlocoVoceChamaDeSorte from "../components/bussola/bloco-voce-chama-de-sorte";
import BlocoPortaNaoCede from "../components/bussola/bloco-porta-nao-cede";
import BlocoPortaErrada from "../components/bussola/bloco-porta-errada";
import BlocoAprenderLerPortas from "../components/bussola/bloco-aprender-ler-portas";
import BlocoMesmoSignoMomentosDiferentes from "../components/bussola/bloco-mesmo-signo-momentos-diferentes";
import BlocoHoroscopoGenericoRadio from "../components/bussola/bloco-horoscopo-generico-radio";
import BlocoComoIdentificaPortaAberta from "../components/bussola/bloco-como-identifica-porta-aberta";
import BlocoPasso1AbraMapa from "../components/bussola/bloco-passo1-abra-mapa";
import BlocoPasso2DescubraPorta from "../components/bussola/bloco-passo2-descubra-porta";
import BlocoPasso3ConsulteInterpretacao from "../components/bussola/bloco-passo3-consulte-interpretacao";
import BlocoEPronto from "../components/bussola/bloco-e-pronto";
import BlocoOndePararDeForcar from "../components/bussola/bloco-onde-parar-de-forcar";
import BlocoNemTodaFasePedeEsforco from "../components/bussola/bloco-nem-toda-fase-pede-esforco";
import BlocoOfertaHeadline from "../components/bussola/bloco-oferta-headline";
import BlocoOfertaConteudo from "../components/bussola/bloco-oferta-conteudo";
import BlocoOfertaFinal from "../components/bussola/bloco-oferta-final";
import BlocoFAQ from "../components/bussola/bloco-faq";
import RodapeBussola from "../components/bussola/rodape-bussola";
import WhatsappButton from "../components/bussola/whatsapp-button";
import CtaFixo from "../components/bussola/cta-fixo";

const PREFETCH_IMAGES = [
  fluiAsset.url,
  fluiMobileAsset.url,
  semanaAsset.url,
  retratoAsset,
  erroAsset.url,
  portasSeAbrindoAsset,
  esforcouODobroAsset,
  precisavaSeEsforcarAsset,
  procurouExplicacaoAsset,
  naoFoiFaltaDeEsforcoAsset,
  dozePortasAsset,
  portasNaoVivemMesmoCicloAsset,
  portaAbertaVocePercebeAsset,
  voceChamaDeSorteAsset,
  portaNaoCedeAsset,
  portaErradaAsset,
  aprenderLerPortasAsset,
  mesmoSignoMomentosDiferentesAsset,
  horoscopoGenericoRadioAsset,
  comoIdentificaPortaAbertaAsset,
  passo1AbraMapaAsset,
  passo2DescubraPortaAsset,
  passo3ConsulteInterpretacaoAsset,
  eProntoAsset,
  ondePararDeForcarAsset,
  nemTodaFasePedeEsforcoAsset,
];


const DESCRICAO =
  "Aprenda a identificar quais portas estão abertas para você agora — no dinheiro, no amor, na carreira e em outras 9 áreas da vida. Acesso imediato, 7 dias de garantia.";

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

const CHECKOUT_URL = "https://pay.hotmart.com/Q107238351O?checkoutMode=10";

function BussolaPage() {
  const pixelFired = useRef(false);

  useEffect(() => {
    if (pixelFired.current) return;
    pixelFired.current = true;
    trackPageView();
  }, []);

  // Pré-carrega todas as ilustrações da página em segundo plano (idle)
  // para que fiquem salvas no cache de memória do navegador antes do scroll
  useEffect(() => {
    const prefetch = () => {
      PREFETCH_IMAGES.forEach((src) => {
        const img = new Image();
        img.src = src;
      });
    };

    if (typeof window !== "undefined") {
      if ("requestIdleCallback" in window) {
        const handle = (window as unknown as { requestIdleCallback: (cb: () => void) => number }).requestIdleCallback(prefetch);
        return () => {
          if ("cancelIdleCallback" in window) {
            (window as unknown as { cancelIdleCallback: (id: number) => void }).cancelIdleCallback(handle);
          }
        };
      } else {
        const timer = setTimeout(prefetch, 300);
        return () => clearTimeout(timer);
      }
    }
  }, []);

  // Dificulta o "salvar imagem" / copiar conteúdo da página (não é segurança
  // real — view-source e devtools ainda acessam tudo — apenas dissuade o
  // visitante casual de baixar as artes ou colar o texto em outro lugar.
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

  const handleCheckout = (origem = "hero_bussola") => {
    fbqTrack("InitiateCheckout", { content_name: "Bussola Astrologica" });
    fbqTrackCustom("ClicouCheckout", { origem });
    window.location.href = CHECKOUT_URL;
  };

  return (
    <main className="relative w-full select-none bg-background font-body text-foreground selection:bg-gold selection:text-background">
      <HeroBussola onCheckout={() => handleCheckout("hero_bussola")} />
      <BlocoTudoFlui />
      <BlocoSemanaSeguinte />
      <BlocoRelogioCosmico />
      <Bloco12Casas />
      <BlocoHistoriaCrassus />
      <BlocoErroNuncaFoiVoce />
      <BlocoPortasSeAbrindo />
      <BlocoEsforcouODobro />
      <BlocoPrecisavaSeEsforcar />
      <BlocoProcurouExplicacao />
      <BlocoNaoFoiFaltaDeEsforco />
      <Bloco12Portas />
      <BlocoPortasNaoVivemMesmoCiclo />
      <BlocoPortaAbertaVocePercebe />
      <BlocoVoceChamaDeSorte />
      <BlocoPortaNaoCede />
      <BlocoPortaErrada />
      <BlocoAprenderLerPortas />
      <BlocoMesmoSignoMomentosDiferentes />
      <BlocoHoroscopoGenericoRadio />
      <BlocoComoIdentificaPortaAberta />
      <BlocoPasso1AbraMapa />
      <BlocoPasso2DescubraPorta />
      <BlocoPasso3ConsulteInterpretacao />
      <BlocoEPronto />
      <BlocoOndePararDeForcar />
      <BlocoNemTodaFasePedeEsforco />
      <BlocoOfertaHeadline />
      <BlocoOfertaConteudo />
      <BlocoOfertaFinal onCheckout={() => handleCheckout("oferta_final")} />
      <BlocoFAQ />
      <RodapeBussola />

      <WhatsappButton />
      <CtaFixo onCheckout={() => handleCheckout("cta_fixo")} />
    </main>
  );
}
