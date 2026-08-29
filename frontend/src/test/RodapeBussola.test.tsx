import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import RodapeBussola, { DADOS_EMPRESA } from "@/components/bussola/rodape-bussola";

describe("RodapeBussola Component", () => {
  it("should render company information: CNPJ, Razão Social and Crassus Gobbi", () => {
    render(<RodapeBussola />);
    expect(screen.getByText(new RegExp(DADOS_EMPRESA.cnpj, "i"))).toBeInTheDocument();
    expect(screen.getByText(new RegExp(DADOS_EMPRESA.razaoSocial, "i"))).toBeInTheDocument();
    expect(screen.getByText(new RegExp(DADOS_EMPRESA.autor, "i"))).toBeInTheDocument();
  });

  it("should render legal links for Privacy Policy and Terms of Use opening in a new tab", () => {
    render(<RodapeBussola />);
    const privacyLink = screen.getByRole("link", { name: /Políticas de Privacidade/i });
    expect(privacyLink).toBeInTheDocument();
    expect(privacyLink).toHaveAttribute("href", "/politicas-de-privacidade");
    expect(privacyLink).toHaveAttribute("target", "_blank");
    expect(privacyLink).toHaveAttribute("rel", "noopener noreferrer");

    const termsLink = screen.getByRole("link", { name: /Termos de Uso/i });
    expect(termsLink).toBeInTheDocument();
    expect(termsLink).toHaveAttribute("href", "/termos-de-uso");
    expect(termsLink).toHaveAttribute("target", "_blank");
    expect(termsLink).toHaveAttribute("rel", "noopener noreferrer");
  });
});
