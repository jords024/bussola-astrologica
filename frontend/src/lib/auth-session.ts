export interface AuthUser {
  id: string;
  email: string;
  roles: string[];
}

export interface AuthSession {
  token: string;
  user: AuthUser;
}

const STORAGE_KEY = "astrowake_auth_session";

export const authSession = {
  getToken(): string | null {
    if (typeof window === "undefined") return null;
    const session = this.getSession();
    return session?.token ?? null;
  },

  getSession(): AuthSession | null {
    if (typeof window === "undefined") return null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw) as AuthSession;
    } catch {
      return null;
    }
  },

  getUser(): AuthUser | null {
    const session = this.getSession();
    return session?.user ?? null;
  },

  setSession(token: string, user: AuthUser): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, user }));
    window.dispatchEvent(new CustomEvent("auth:change", { detail: { token, user } }));
  },

  signOut(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new CustomEvent("auth:change", { detail: null }));
  },
};
