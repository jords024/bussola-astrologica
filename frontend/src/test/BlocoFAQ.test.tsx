import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import BlocoFAQ, { FAQ_ITEMS } from "@/components/bussola/bloco-faq";

describe("BlocoFAQ Component", () => {
  it("should render the FAQ heading and description", () => {
    render(<BlocoFAQ />);
    expect(screen.getByRole("heading", { name: /PERGUNTAS FREQUENTES/i })).toBeInTheDocument();
    expect(screen.getByText(/Tudo o que você precisa saber sobre o/i)).toBeInTheDocument();
  });

  it("should render all 6 FAQ questions with closed state by default", () => {
    render(<BlocoFAQ />);
    FAQ_ITEMS.forEach((item) => {
      const button = screen.getByRole("button", { name: new RegExp(item.pergunta, "i") });
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute("aria-expanded", "false");
    });
  });

  it("should expand and show the answer when a question button is clicked", () => {
    render(<BlocoFAQ />);
    const firstItem = FAQ_ITEMS[0];
    const button = screen.getByRole("button", { name: new RegExp(firstItem.pergunta, "i") });

    // Click to open
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(new RegExp(firstItem.resposta, "i"))).toBeInTheDocument();

    // Click again to close
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("should switch open question when clicking another FAQ item", () => {
    render(<BlocoFAQ />);
    const button1 = screen.getByRole("button", { name: new RegExp(FAQ_ITEMS[0].pergunta, "i") });
    const button2 = screen.getByRole("button", { name: new RegExp(FAQ_ITEMS[1].pergunta, "i") });

    // Open first
    fireEvent.click(button1);
    expect(button1).toHaveAttribute("aria-expanded", "true");
    expect(button2).toHaveAttribute("aria-expanded", "false");

    // Open second
    fireEvent.click(button2);
    expect(button1).toHaveAttribute("aria-expanded", "false");
    expect(button2).toHaveAttribute("aria-expanded", "true");
  });
});
