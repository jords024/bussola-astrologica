import { useEffect, useRef, useState } from "react";
import { ArrowRight, Lock } from "lucide-react";

type Props = {
  onCheckout: () => void;
};

/**
 * Barra de CTA fixa no rodapé. Só aparece depois que o hero (que já tem seu
 * próprio CTA grande) sai de vista, para não competir com ele nem poluir a
 * primeira dobra. Some de novo perto do topo, caso o visitante role de volta.
 */
export default function CtaFixo({ onCheckout }: Props) {
  const [pastHero, setPastHero] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const tickingRef = useRef(false);

  useEffect(() => {
    const THRESHOLD = window.innerHeight * 0.95;

    const update = () => {
      tickingRef.current = false;
      setPastHero((prev) => {
        const next = window.scrollY > THRESHOLD;
        return prev === next ? prev : next;
      });
    };

    const onScroll = () => {
      if (tickingRef.current) return;
      tickingRef.current = true;
      requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onModalToggle = (e: Event) => {
      setModalOpen(Boolean((e as CustomEvent<boolean>).detail));
    };
    window.addEventListener("bussola:casas-modal", onModalToggle);
    return () => window.removeEventListener("bussola:casas-modal", onModalToggle);
  }, []);

  const visible = pastHero && !modalOpen;

  return (
    <div
      aria-hidden={!visible}
      className={`fixed inset-x-0 bottom-0 z-40 transition-all duration-500 ease-out ${
        visible ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-full opacity-0"
      }`}
      style={{ paddingBottom: "max(10px, env(safe-area-inset-bottom, 0px))" }}
    >
      <div className="border-t border-gold/25 bg-background/92 backdrop-blur-lg">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:gap-5 sm:px-6">
          <div className="hidden shrink-0 sm:block">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Bússola Astrológica
            </p>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground/80">
              <Lock className="h-3 w-3 text-gold" />
              7 dias de garantia
            </p>
          </div>

          <button
            type="button"
            onClick={onCheckout}
            className="group flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold-deep via-gold-soft to-gold px-5 py-3 text-xs font-black uppercase tracking-[0.12em] text-background shadow-[0_10px_30px_-10px_color-mix(in_oklab,var(--gold)_55%,transparent)] transition-transform duration-300 hover:scale-[1.01] active:scale-[0.99] sm:flex-initial sm:px-8 sm:text-sm"
          >
            <span>Quero abrir minhas portas</span>
            <span className="ml-1 rounded-full bg-background/15 px-2 py-0.5 text-[11px] font-bold normal-case tracking-normal sm:ml-2">
              R$67
            </span>
            <ArrowRight className="h-4 w-4 shrink-0 transition-transform duration-300 group-hover:translate-x-1" />
          </button>
        </div>
      </div>
    </div>
  );
}
