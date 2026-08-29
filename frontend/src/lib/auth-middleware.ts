import { createMiddleware } from "@tanstack/react-start";
import { getRequest } from "@tanstack/react-start/server";
import { verifyAuthToken, type UserPayload } from "./auth.server";

export interface AuthContext {
  userId: string;
  email: string;
  roles: string[];
  user: UserPayload;
}

export const requireAuth = createMiddleware({ type: "function" }).server(async ({ next }) => {
  const request = getRequest();
  const authHeader = request?.headers?.get("authorization");

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    throw new Error("Unauthorized: No authorization token provided");
  }

  const token = authHeader.slice(7).trim();
  if (!token) {
    throw new Error("Unauthorized: Empty token");
  }

  const user = await verifyAuthToken(token);
  if (!user) {
    throw new Error("Unauthorized: Invalid or expired token");
  }

  return next({
    context: {
      userId: user.id,
      email: user.email,
      roles: user.roles,
      user,
    },
  });
});
