import { describe, it, expect, beforeEach, vi } from "vitest";
import { authSession } from "@/lib/auth-session";

describe("Auth Session Client", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("should store session and retrieve token", () => {
    expect(authSession.getToken()).toBeNull();
    expect(authSession.getUser()).toBeNull();

    const mockUser = {
      id: "test-user-id",
      email: "teste@exemplo.com",
      roles: ["admin"],
    };
    const mockToken = "mock.jwt.token";

    authSession.setSession(mockToken, mockUser);

    expect(authSession.getToken()).toBe(mockToken);
    expect(authSession.getUser()).toEqual(mockUser);
  });

  it("should clear session on signOut", () => {
    const mockUser = {
      id: "test-user-id",
      email: "teste@exemplo.com",
      roles: ["user"],
    };
    authSession.setSession("test-token", mockUser);
    expect(authSession.getToken()).toBe("test-token");

    const listener = vi.fn();
    window.addEventListener("auth:change", listener);

    authSession.signOut();

    expect(authSession.getToken()).toBeNull();
    expect(authSession.getUser()).toBeNull();
    expect(listener).toHaveBeenCalled();
  });
});
