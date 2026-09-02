import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import WhatsappButton from "@/components/bussola/whatsapp-button";

describe("WhatsappButton Component", () => {
  it("should render the WhatsApp button with correct link, phone and encoded message", () => {
    render(<WhatsappButton />);
    const link = screen.getByRole("link", { name: /Fale conosco no WhatsApp/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");

    const href = link.getAttribute("href");
    expect(href).toContain("554792331247");
    expect(href).toContain(encodeURIComponent("Quero saber mais sobre o Bússola Astrológico"));
    expect(href).not.toContain("%3F");
  });

  it("should display the hover tooltip text", () => {
    render(<WhatsappButton />);
    expect(screen.getByText(/Tire suas dúvidas no WhatsApp/i)).toBeInTheDocument();
  });

  it("should trigger click handler without errors", () => {
    render(<WhatsappButton />);
    const link = screen.getByRole("link", { name: /Fale conosco no WhatsApp/i });
    expect(() => fireEvent.click(link)).not.toThrow();
  });
});
