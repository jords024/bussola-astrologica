import { createMiddleware } from '@tanstack/react-start';
import { authSession } from './auth-session';

export const attachAuth = createMiddleware({ type: 'function' }).client(
  async ({ next }) => {
    const token = authSession.getToken();
    return next({
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  },
);
