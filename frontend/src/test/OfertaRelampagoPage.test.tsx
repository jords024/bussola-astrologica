import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import HeroBussolaV2 from "@/components/bussola/hero-bussola-v2";
import BlocoOfertaFinal from "@/components/bussola/bloco-oferta-final";
import {
  OfertaRelampagoPage,
  PRECO_A_VISTA,
  PRECO_PARCELADO,
  HOTMART_CHECKOUT_URL,
  buildHotmartCheckoutUrl,
} from "@/routes/oferta-relampago";

describe("Oferta Relampago Page & Customized Pricing", () => {
  it("should have correct initial price constants for oferta-relampago page", () => {
    expect(PRECO_A_VISTA).toBe("R$47");
    expect(PRECO_PARCELADO).toBe("12x de R$4,86");
    expect(HOTMART_CHECKOUT_URL).toContain("pay.hotmart.com");
    expect(HOTMART_CHECKOUT_URL).toContain("off=ya381gy5");
  });

  it("should render HeroBussolaV2 with custom price R$47", () => {
    const onCheckout = vi.fn();
    render(<HeroBussolaV2 onCheckout={onCheckout} preco="R$47" />);
    expect(screen.getByText(/R\$47/i)).toBeInTheDocument();

    const ctaButton = screen.getByRole("button", { name: /Quero abrir minhas portas/i });
    expect(ctaButton).toBeInTheDocument();
    fireEvent.click(ctaButton);
    expect(onCheckout).toHaveBeenCalledTimes(1);
  });

  it("should render BlocoOfertaFinal with custom price props for R$47", () => {
    const onCheckout = vi.fn();
    render(
      <BlocoOfertaFinal
        onCheckout={onCheckout}
        precoAVista="R$47"
        precoParcelado="12x de R$4,86"
      />,
    );

    expect(screen.getByText(/12x de R\$4,86/i)).toBeInTheDocument();
    expect(
      screen.getByText((_, el) => el?.textContent?.trim() === "ou R$47 à vista"),
    ).toBeInTheDocument();

    const ctaButton = screen.getByRole("button", { name: /Quero abrir minhas portas/i });
    expect(ctaButton).toBeInTheDocument();
    fireEvent.click(ctaButton);
    expect(onCheckout).toHaveBeenCalledTimes(1);
  });

  it("should render full OfertaRelampagoPage with custom price R$47 and countdown timer", () => {
    render(<OfertaRelampagoPage />);

    // Verifica se os valores R$47 e 12x de R$4,86 aparecem na pagina renderizada
    const elementsWithPreco = screen.getAllByText(/R\$47/i);
    expect(elementsWithPreco.length).toBeGreaterThanOrEqual(2);

    expect(screen.getByText(/12x de R\$4,86/i)).toBeInTheDocument();

    // Verifica presenca do botao de CTA da oferta
    const ctaButtons = screen.getAllByRole("button", { name: /Quero abrir minhas portas/i });
    expect(ctaButtons.length).toBeGreaterThan(0);

    // Verifica presenca do timer de contagem regressiva com a data de hoje
    expect(screen.getByTestId("timer-oferta")).toBeInTheDocument();
    expect(screen.getByText(/Válido só hoje/i)).toBeInTheDocument();
    expect(screen.getByText(/23:59/i)).toBeInTheDocument();
  });

  it("should build Hotmart checkout URL forwarding UTM params for oferta-relampago", () => {
    const search = "?utm_source=meta_ads&utm_campaign=oferta_relampago_promo&src=afiliado1";
    const builtUrl = buildHotmartCheckoutUrl(search);
    const parsed = new URL(builtUrl);

    expect(parsed.origin + parsed.pathname).toBe("https://pay.hotmart.com/Q107238351O");
    expect(parsed.searchParams.get("off")).toBe("ya381gy5");
    expect(parsed.searchParams.get("checkoutMode")).toBe("10");
    expect(parsed.searchParams.get("utm_source")).toBe("meta_ads");
    expect(parsed.searchParams.get("utm_campaign")).toBe("oferta_relampago_promo");
    expect(parsed.searchParams.get("src")).toBe("afiliado1");
  });
});
