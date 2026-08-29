import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import PoliticasDePrivacidadePage from "@/routes/politicas-de-privacidade";
import TermosDeUsoPage from "@/routes/termos-de-uso";

describe("Legal Pages", () => {
  describe("PoliticasDePrivacidadePage", () => {
    it("should render the full Privacy Policy title, company information and sections", () => {
      render(<PoliticasDePrivacidadePage />);
      expect(
        screen.getByRole("heading", { level: 1, name: /Políticas de Privacidade/i }),
      ).toBeInTheDocument();
      expect(screen.getAllByText(/43\.066\.768\/0001-70/i).length).toBeGreaterThan(0);
      expect(
        screen.getAllByText(/Astrowake serviços de astrologia Ltda\./i).length,
      ).toBeGreaterThan(0);
      expect(screen.getByText(/Lei Geral de Proteção de Dados Pessoais/i)).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Informações Gerais e Controlador/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Dados Pessoais Coletados/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Direitos do Titular dos Dados/i }),
      ).toBeInTheDocument();
    });
  });

  describe("TermosDeUsoPage", () => {
    it("should render the full Terms of Use title, company details and 7-day guarantee clause", () => {
      render(<TermosDeUsoPage />);
      expect(
        screen.getByRole("heading", { level: 1, name: /Termos de Uso e Condições Gerais/i }),
      ).toBeInTheDocument();
      expect(screen.getAllByText(/43\.066\.768\/0001-70/i).length).toBeGreaterThan(0);
      expect(
        screen.getByRole("heading", { name: /Garantia Incondicional de 7 Dias/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Licença de Uso Individual e Intransferível/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: /Propriedade Intelectual e Direitos Autorais/i }),
      ).toBeInTheDocument();
    });
  });
});
