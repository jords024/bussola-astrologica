import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { Button } from "@/components/ui/button";

describe("UI Button Component", () => {
  it("should render button with text", () => {
    render(<Button>Clique Aqui</Button>);
    const button = screen.getByRole("button", { name: /Clique Aqui/i });
    expect(button).toBeInTheDocument();
  });

  it("should apply variant and size classes correctly", () => {
    render(
      <Button variant="destructive" size="sm">
        Excluir
      </Button>,
    );
    const button = screen.getByRole("button", { name: /Excluir/i });
    expect(button).toHaveClass("bg-destructive");
  });

  it("should be disabled when disabled prop is passed", () => {
    render(<Button disabled>Aguarde</Button>);
    const button = screen.getByRole("button", { name: /Aguarde/i });
    expect(button).toBeDisabled();
  });
});
