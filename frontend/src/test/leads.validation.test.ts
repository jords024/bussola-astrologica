import { describe, it, expect } from "vitest";
import { clean, getBrasiliaDateTime } from "@/lib/leads.functions";

describe("Lead Validation & Cleaning", () => {
  it("should clean and trim string values", () => {
    expect(clean("  joao silva  ")).toBe("joao silva");
    expect(clean("   ")).toBeNull();
    expect(clean(null)).toBeNull();
    expect(clean(undefined)).toBeNull();
    expect(clean(12345)).toBeNull();
  });

  it("should truncate strings exceeding maximum length", () => {
    const longString = "a".repeat(200);
    const result = clean(longString, 50);
    expect(result).not.toBeNull();
    expect(result?.length).toBe(50);
  });

  it("should validate email format correctly", () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    expect(emailRegex.test("usuario@exemplo.com")).toBe(true);
    expect(emailRegex.test("contato.teste@dominio.com.br")).toBe(true);
    expect(emailRegex.test("invalido-sem-arroba")).toBe(false);
    expect(emailRegex.test("invalido@semdominio")).toBe(false);
  });

  it("should format date and time in America/Sao_Paulo timezone correctly", () => {
    // 2026-08-29T20:30:00.000Z is 17:30:00 in Brasilia (UTC-3)
    const fixedUtcDate = new Date("2026-08-29T20:30:00.000Z");
    const formatted = getBrasiliaDateTime(fixedUtcDate);
    expect(formatted).toBe("29/08/2026, 17:30:00");
  });

  it("should validate and format WhatsApp numbers with DDI and DDD correctly", () => {
    const formatarBR = (v: string) => {
      const d = v.replace(/\D/g, "").slice(0, 11);
      if (!d) return "";
      if (d.length <= 2) return `(${d}`;
      if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
      if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
      return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
    };

    expect(formatarBR("11987654321")).toBe("(11) 98765-4321");
    expect(formatarBR("85999998888")).toBe("(85) 99999-8888");
    expect(formatarBR("1133334444")).toBe("(11) 3333-4444");

    const validarTel = (ddi: string, tel: string) => {
      const digitos = tel.replace(/\D/g, "");
      if (!digitos) return false;
      if (ddi === "+55" && digitos.length < 10) return false;
      if (digitos.length < 7) return false;
      return true;
    };

    expect(validarTel("+55", "11987654321")).toBe(true);
    expect(validarTel("+55", "119876")).toBe(false); // Incompleto sem número completo
    expect(validarTel("+351", "912345678")).toBe(true); // Portugal
    expect(validarTel("+1", "5550000000")).toBe(true); // EUA
  });
});
