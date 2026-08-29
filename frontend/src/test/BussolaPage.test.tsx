import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import HeroBussola from "@/components/bussola/hero-bussola";
import BlocoTudoFlui from "@/components/bussola/bloco-tudo-flui";
import BlocoSemanaSeguinte from "@/components/bussola/bloco-semana-seguinte";
import Bloco12Portas from "@/components/bussola/bloco-12-portas";
import BlocoHistoriaCrassus from "@/components/bussola/bloco-historia-crassus";
import BlocoOfertaHeadline from "@/components/bussola/bloco-oferta-headline";
import BlocoOfertaFinal from "@/components/bussola/bloco-oferta-final";
import CtaFixo from "@/components/bussola/cta-fixo";
import BlocoFAQ from "@/components/bussola/bloco-faq";
import WhatsappButton from "@/components/bussola/whatsapp-button";
import RodapeBussola from "@/components/bussola/rodape-bussola";
import { fireEvent } from "@testing-library/react";
import { vi } from "vitest";

describe("Bussola Sales Page Components", () => {
  it("should render HeroBussola with CTA button and trigger onCtaClick", () => {
    const onCtaClick = vi.fn();
    render(<HeroBussola onCtaClick={onCtaClick} />);
    const ctaButtons = screen.getAllByRole("button");
    expect(ctaButtons.length).toBeGreaterThan(0);
    fireEvent.click(ctaButtons[0]);
    expect(onCtaClick).toHaveBeenCalled();
    const heroImg = screen.getByAltText(/Roda zodiacal dourada/i);
    expect(heroImg).toHaveAttribute("loading", "eager");
    expect(heroImg).toHaveAttribute("fetchpriority", "high");
  });

  it("should support backwards compatible onCheckout in HeroBussola", () => {
    const onCheckout = vi.fn();
    render(<HeroBussola onCheckout={onCheckout} />);
    const ctaButtons = screen.getAllByRole("button");
    expect(ctaButtons.length).toBeGreaterThan(0);
    fireEvent.click(ctaButtons[0]);
    expect(onCheckout).toHaveBeenCalled();
  });

  it('should render BlocoOfertaHeadline with id="oferta" and correct texts', () => {
    const { container } = render(<BlocoOfertaHeadline />);
    const section = container.querySelector("section#oferta");
    expect(section).toBeInTheDocument();
    expect(screen.getByText(/Você não precisa decorar o céu\./i)).toBeInTheDocument();
    expect(screen.getByText(/Precisa aprender onde olhar\./i)).toBeInTheDocument();
    expect(screen.getByText(/TUDO QUE VOCÊ VAI RECEBER/i)).toBeInTheDocument();
  });

  it("should render BlocoOfertaFinal with CTA button and trigger onCheckout", () => {
    const onCheckout = vi.fn();
    render(<BlocoOfertaFinal onCheckout={onCheckout} />);
    const ctaButton = screen.getByRole("button", { name: /Quero abrir minhas portas/i });
    expect(ctaButton).toBeInTheDocument();
    fireEvent.click(ctaButton);
    expect(onCheckout).toHaveBeenCalled();
  });

  it("should render CtaFixo and trigger onCheckout", () => {
    const onCheckout = vi.fn();
    render(<CtaFixo onCheckout={onCheckout} />);
    const ctaButton = screen.getByRole("button", {
      name: /Quero abrir minhas portas/i,
      hidden: true,
    });
    expect(ctaButton).toBeInTheDocument();
    fireEvent.click(ctaButton);
    expect(onCheckout).toHaveBeenCalled();
  });

  it("should render BlocoTudoFlui with eager loading for fast above-the-fold display", () => {
    render(<BlocoTudoFlui />);
    const img = screen.getByAltText(/Tem semana que tudo flui/i);
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("loading", "eager");
    expect(img).toHaveAttribute("fetchpriority", "high");
  });

  it("should render BlocoSemanaSeguinte with eager loading", () => {
    render(<BlocoSemanaSeguinte />);
    const img = screen.getByAltText(/Aí chega a semana seguinte/i);
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("loading", "eager");
    expect(img).toHaveAttribute("fetchpriority", "high");
  });

  it("should render Bloco12Portas with image correctly", () => {
    render(<Bloco12Portas />);
    const img = screen.getByAltText(/As 12 Portas/i);
    expect(img).toBeInTheDocument();
  });

  it("should render BlocoHistoriaCrassus with eager portrait", () => {
    render(<BlocoHistoriaCrassus />);
    const img = screen.getByAltText(/Crassus Gobbi, astrólogo/i);
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("loading", "eager");
  });

  it("should include BlocoFAQ with all questions", () => {
    render(<BlocoFAQ />);
    expect(screen.getByText(/Como vou receber o acesso\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Preciso saber astrologia para conseguir usar\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Por quanto tempo terei acesso\?/i)).toBeInTheDocument();
  });

  it("should render WhatsappButton correctly", () => {
    render(<WhatsappButton />);
    expect(screen.getByRole("link", { name: /Fale conosco no WhatsApp/i })).toBeInTheDocument();
  });

  it("should render RodapeBussola with CNPJ and legal links", () => {
    render(<RodapeBussola />);
    expect(screen.getByText(/43\.066\.768\/0001-70/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Políticas de Privacidade/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Termos de Uso/i })).toBeInTheDocument();
  });
});
