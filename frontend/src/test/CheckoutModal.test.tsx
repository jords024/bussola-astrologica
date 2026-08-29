import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import CheckoutModal, {
  formatPhoneByCountry,
  COUNTRIES,
} from "@/components/bussola/checkout-modal";

describe("CheckoutModal Component with Country Selector", () => {
  it("should not render anything when isOpen is false", () => {
    const { container } = render(
      <CheckoutModal isOpen={false} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("should render form with Brazil (+55) as default selected country", () => {
    render(<CheckoutModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText(/Seu nome completo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Seu WhatsApp com DDD/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/País selecionado: Brasil \(\+55\)/i)).toBeInTheDocument();
    expect(screen.getByText("+55")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Ir para pagamento seguro/i })).toBeInTheDocument();
  });

  it("should format Brazilian phone numbers with DDD mask correctly", () => {
    expect(formatPhoneByCountry("", "BR")).toBe("");
    expect(formatPhoneByCountry("4", "BR")).toBe("(4");
    expect(formatPhoneByCountry("47", "BR")).toBe("(47");
    expect(formatPhoneByCountry("47999998888", "BR")).toBe("(47) 99999-8888");
    expect(formatPhoneByCountry("4799998888", "BR")).toBe("(47) 9999-8888");
  });

  it("should open country dropdown and allow selecting another country like Portugal (+351)", () => {
    render(<CheckoutModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);
    const countryButton = screen.getByLabelText(/País selecionado: Brasil \(\+55\)/i);
    fireEvent.click(countryButton);

    const portugalOption = screen.getByText("Portugal");
    expect(portugalOption).toBeInTheDocument();
    fireEvent.click(portugalOption);

    expect(screen.getByLabelText(/País selecionado: Portugal \(\+351\)/i)).toBeInTheDocument();
    expect(screen.getByText("+351")).toBeInTheDocument();
  });

  it("should display validation errors when submitting invalid inputs", async () => {
    const handleSubmit = vi.fn();
    render(<CheckoutModal isOpen={true} onClose={vi.fn()} onSubmit={handleSubmit} />);
    const submitBtn = screen.getByRole("button", { name: /Ir para pagamento seguro/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Por favor, digite seu nome completo/i)).toBeInTheDocument();
    expect(await screen.findByText(/Digite seu WhatsApp completo com DDD/i)).toBeInTheDocument();
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("should call onSubmit with clean digits and DDI 55 by default when valid", async () => {
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    render(<CheckoutModal isOpen={true} onClose={vi.fn()} onSubmit={handleSubmit} />);

    const nomeInput = screen.getByLabelText(/Seu nome completo/i);
    const phoneInput = screen.getByLabelText(/Seu WhatsApp com DDD/i);
    const submitBtn = screen.getByRole("button", { name: /Ir para pagamento seguro/i });

    fireEvent.change(nomeInput, { target: { value: "Maria Silva" } });
    fireEvent.change(phoneInput, { target: { value: "47999887766" } });

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleSubmit).toHaveBeenCalledWith({
        nome: "Maria Silva",
        whatsapp: "47999887766",
        ddi: "55",
        countryCode: "BR",
      });
    });
  });

  it("should apply mobile safe area and 100dvh classes", () => {
    render(<CheckoutModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveClass("min-h-[100dvh]");
    expect(dialog.className).toContain("safe-area-inset-bottom");
  });

  it("should display loading state when isLoading is true", () => {
    render(<CheckoutModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByText(/Carregando checkout seguro/i)).toBeInTheDocument();
    const submitBtn = screen.getByRole("button", { name: /Carregando checkout seguro/i });
    expect(submitBtn).toBeDisabled();
  });

  it("should call onClose when close button is clicked", () => {
    const handleClose = vi.fn();
    render(<CheckoutModal isOpen={true} onClose={handleClose} onSubmit={vi.fn()} />);
    const closeBtn = screen.getByLabelText(/Fechar formulário de compra/i);
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
