import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { fbqTrack, fbqTrackCustom, trackPageView } from "../lib/fbq";
import heroAsset from "../assets/bussola-hero.png.asset.json";
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
import CtaFixo from "../components/bussola/cta-fixo";


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
  }),
  component: BussolaPage,
});

const CHECKOUT_URL = "https://pay.hotmart.com/Q107238351O";

function BussolaPage() {
  const pixelFired = useRef(false);

  useEffect(() => {
    if (pixelFired.current) return;
    pixelFired.current = true;
    trackPageView();
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

      <CtaFixo onCheckout={() => handleCheckout("cta_fixo")} />
    </main>
  );
}
