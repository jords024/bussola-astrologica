import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import TimerOferta, { getTimeUntilMidnight, formatarDataHoje } from "@/components/bussola/timer-oferta";
import BlocoOfertaFinal from "@/components/bussola/bloco-oferta-final";

describe("TimerOferta Component & Countdown Logic", () => {
  it("should calculate remaining time until 23:59:59 correctly", () => {
    // Simulando 20:00:00
    const mockDate = new Date(2026, 8, 14, 20, 0, 0, 0);
    const result = getTimeUntilMidnight(mockDate);

    // 23:59:59.999 - 20:00:00 = 3h 59m 59s
    expect(result.hours).toBe(3);
    expect(result.minutes).toBe(59);
    expect(result.seconds).toBe(59);
    expect(result.totalMs).toBeGreaterThan(0);
  });

  it("should format date correctly with formatarDataHoje", () => {
    const mockDate = new Date(2026, 8, 14); // 14 de setembro
    expect(formatarDataHoje(mockDate)).toBe("14/09");

    const mockDate2 = new Date(2026, 0, 5); // 05 de janeiro
    expect(formatarDataHoje(mockDate2)).toBe("05/01");
  });

  it("should render TimerOferta with dynamic today date in label and time units", () => {
    render(<TimerOferta />);

    const hoje = formatarDataHoje();
    expect(screen.getByText(new RegExp(`Válido só hoje \\(${hoje}\\) até as 23:59`, "i"))).toBeInTheDocument();
    expect(screen.getByText(/horas/i)).toBeInTheDocument();
    expect(screen.getByText(/min/i)).toBeInTheDocument();
    expect(screen.getByText(/seg/i)).toBeInTheDocument();
  });

  it("should support custom label text in TimerOferta", () => {
    render(<TimerOferta texto="Oferta relâmpago expira hoje às 23:59" />);
    expect(screen.getByText(/Oferta relâmpago expira hoje às 23:59/i)).toBeInTheDocument();
  });

  it("should render timer with today date in BlocoOfertaFinal only when mostrarTimer is true", () => {
    const onCheckout = () => {};
    const { rerender } = render(
      <BlocoOfertaFinal onCheckout={onCheckout} mostrarTimer={false} />,
    );
    expect(screen.queryByTestId("timer-oferta")).not.toBeInTheDocument();

    rerender(<BlocoOfertaFinal onCheckout={onCheckout} mostrarTimer={true} />);
    expect(screen.getByTestId("timer-oferta")).toBeInTheDocument();
    const hoje = formatarDataHoje();
    expect(screen.getByText(new RegExp(`Válido só hoje \\(${hoje}\\) até as 23:59`, "i"))).toBeInTheDocument();
  });
});
