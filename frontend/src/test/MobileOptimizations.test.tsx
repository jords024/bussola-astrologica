import { describe, it, expect, vi } from "vitest";
import { formatPhoneByCountry, COUNTRIES } from "@/components/bussola/checkout-modal";

describe("Mobile Performance & Optimizations Suite", () => {
  it("should support multiple country phone formats without breaking", () => {
    // Portugal
    expect(formatPhoneByCountry("912345678", "PT")).toBe("912345678");
    // Estados Unidos
    expect(formatPhoneByCountry("2025550143", "US")).toBe("2025550143");
    // Espanha
    expect(formatPhoneByCountry("612345678", "ES")).toBe("612345678");
  });

  it("should include all required international country codes in list", () => {
    const codes = COUNTRIES.map((c) => c.code);
    expect(codes).toContain("BR");
    expect(codes).toContain("PT");
    expect(codes).toContain("US");
    expect(codes).toContain("ES");
    expect(codes).toContain("AR");
  });

  it("should handle timeout resilience in promises cleanly without unhandled rejection", async () => {
    const slowTask = new Promise((resolve) => setTimeout(() => resolve("done"), 10000));
    const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout")), 50));

    let timedOut = false;
    try {
      await Promise.race([slowTask, timeout]);
    } catch (err) {
      timedOut = true;
      expect((err as Error).message).toBe("Timeout");
    }
    expect(timedOut).toBe(true);
  });
});
