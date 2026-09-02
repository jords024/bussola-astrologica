import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import HeroBussolaV2 from "@/components/bussola/hero-bussola-v2";
import BlocoVoceJaSePegouPensando from "@/components/bussola/bloco-voce-ja-se-pegou-pensando";
import BlocoCulpaNaoESua from "@/components/bussola/bloco-culpa-nao-e-sua";
import BlocoOQueSaoTransitos from "@/components/bussola/bloco-o-que-sao-transitos";
import BlocoMecanismo12Portas from "@/components/bussola/bloco-mecanismo-12-portas";
import BlocoComoFunciona from "@/components/bussola/bloco-como-funciona";
import BlocoPortasInterativas from "@/components/bussola/bloco-portas-interativas";
import BlocoParaQuemE from "@/components/bussola/bloco-para-quem-e";

describe("Bussola Redesign Components", () => {
  describe("HeroBussolaV2", () => {
    it("should render heading and trigger onCheckout click", () => {
      const onCheckout = vi.fn();
      render(<HeroBussolaV2 onCheckout={onCheckout} />);

      expect(
        screen.getByRole("heading", { level: 1, name: /Destrave o mesmo conhecimento astrológico/i })
      ).toBeInTheDocument();
      expect(screen.getByAltText(/Bússola Astrológica/i)).toBeInTheDocument();

      const ctaBtn = screen.getByRole("button", { name: /Quero abrir minhas portas/i });
      expect(ctaBtn).toBeInTheDocument();
      fireEvent.click(ctaBtn);
      expect(onCheckout).toHaveBeenCalledTimes(1);

      expect(screen.getByText(/Acesso imediato/i)).toBeInTheDocument();
      expect(screen.getByText(/7 dias de garantia/i)).toBeInTheDocument();
      expect(screen.getByText(/R\$67/i)).toBeInTheDocument();
    });
  });

  describe("BlocoVoceJaSePegouPensando", () => {
    it("should render questions and reflexions", () => {
      render(<BlocoVoceJaSePegouPensando />);
      expect(
        screen.getByRole("heading", { level: 2, name: /Você já se pegou pensando/i })
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Por que tem períodos em que tudo parece fluir/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Se alguma dessas te tocou, não é falta de sorte/i)
      ).toBeInTheDocument();
    });
  });

  describe("BlocoCulpaNaoESua", () => {
    it("should render problem cards and simple solution banner", () => {
      render(<BlocoCulpaNaoESua />);
      expect(
        screen.getByRole("heading", { level: 2, name: /A culpa não é sua\./i })
      ).toBeInTheDocument();
      expect(screen.getByText(/O problema do horóscopo genérico/i)).toBeInTheDocument();
      expect(screen.getByText(/A complicação desnecessária/i)).toBeInTheDocument();
      expect(screen.getByText(/A falta de um método prático/i)).toBeInTheDocument();
      expect(screen.getByText(/A verdade é que pode ser/i)).toBeInTheDocument();
    });
  });

  describe("BlocoOQueSaoTransitos", () => {
    it("should render explanation of transits and door/key analogy", () => {
      render(<BlocoOQueSaoTransitos />);
      expect(
        screen.getByRole("heading", { level: 2, name: /O que são os trânsitos/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/O mapa fica parado\. O céu, não\./i)).toBeInTheDocument();
      expect(screen.getByText(/O trânsito é a/i)).toBeInTheDocument();
      expect(screen.getByText(/A casa do seu mapa é a/i)).toBeInTheDocument();
    });
  });

  describe("BlocoMecanismo12Portas", () => {
    it("should render 12 doors mechanism and door cards", () => {
      render(<BlocoMecanismo12Portas />);
      expect(
        screen.getByRole("heading", { level: 2, name: /Você tem 12 portas/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/A porta do dinheiro/i)).toBeInTheDocument();
      expect(screen.getByText(/A porta do amor/i)).toBeInTheDocument();
      expect(screen.getByText(/A porta da carreira/i)).toBeInTheDocument();
      expect(screen.getByText(/A porta do recolhimento/i)).toBeInTheDocument();
    });
  });

  describe("BlocoComoFunciona", () => {
    it("should render the practical steps", () => {
      render(<BlocoComoFunciona />);
      expect(
        screen.getByRole("heading", { level: 2, name: /Como funciona na prática/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/Acesse o guia/i)).toBeInTheDocument();
      expect(screen.getByText(/Abra seu mapa com trânsitos/i)).toBeInTheDocument();
      expect(screen.getByText(/Identifique a área ativada/i)).toBeInTheDocument();
      expect(screen.getByText(/Interprete a visão/i)).toBeInTheDocument();
      expect(screen.getByText(/Aplique na vida real/i)).toBeInTheDocument();
    });
  });

  describe("BlocoPortasInterativas", () => {
    it("should render 12 interactive doors and allow opening a door", () => {
      render(<BlocoPortasInterativas />);
      expect(
        screen.getByRole("heading", { level: 2, name: /Suas 12 portas/i })
      ).toBeInTheDocument();

      const openDinheiroBtn = screen.getByRole("button", { name: /Abrir A porta do Dinheiro/i });
      expect(openDinheiroBtn).toBeInTheDocument();
      fireEvent.click(openDinheiroBtn);

      const closeDinheiroBtn = screen.getByRole("button", { name: /Fechar A porta do Dinheiro/i });
      expect(closeDinheiroBtn).toBeInTheDocument();
      fireEvent.click(closeDinheiroBtn);
    });
  });

  describe("BlocoParaQuemE", () => {
    it("should render for whom and not for whom lists", () => {
      render(<BlocoParaQuemE />);
      expect(
        screen.getByRole("heading", { level: 2, name: /Para quem é a Bússola Astrológica/i })
      ).toBeInTheDocument();
      expect(screen.getByText(/Isso é pra você que\.\.\./i)).toBeInTheDocument();
      expect(screen.getByText(/Isso não é pra você que\.\.\./i)).toBeInTheDocument();
      expect(
        screen.getByText(/Quer entender os próprios ciclos e parar de viver no automático\./i)
      ).toBeInTheDocument();
    });
  });
});
