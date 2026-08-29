// @vitest-environment node
import { describe, it, expect } from "vitest";
import { hashPassword, comparePassword, createAuthToken, verifyAuthToken } from "@/lib/auth.server";

describe("Auth Server Functions", () => {
  it("should correctly hash and verify passwords", async () => {
    const rawPassword = "mySecretPassword123!";
    const hash = await hashPassword(rawPassword);

    expect(hash).toBeDefined();
    expect(hash).not.toBe(rawPassword);

    const isValid = await comparePassword(rawPassword, hash);
    expect(isValid).toBe(true);

    const isInvalid = await comparePassword("wrongPassword", hash);
    expect(isInvalid).toBe(false);
  });

  it("should generate and verify valid JWT tokens", async () => {
    const user = {
      id: "123e4567-e89b-12d3-a456-426614174000",
      email: "admin@astrowake.com",
      roles: ["admin", "user"],
    };

    const token = await createAuthToken(user);
    expect(token).toBeDefined();
    expect(typeof token).toBe("string");

    const payload = await verifyAuthToken(token);
    expect(payload).not.toBeNull();
    expect(payload?.id).toBe(user.id);
    expect(payload?.email).toBe(user.email);
    expect(payload?.roles).toContain("admin");
  });

  it("should reject invalid or tampered tokens", async () => {
    const invalidPayload = await verifyAuthToken("invalid.jwt.token");
    expect(invalidPayload).toBeNull();

    const emptyPayload = await verifyAuthToken("");
    expect(emptyPayload).toBeNull();
  });
});
