import bcrypt from 'bcryptjs';
import { SignJWT, jwtVerify } from 'jose';
import { query } from './db';

const JWT_SECRET_STRING = process.env.JWT_SECRET || 'bussola_astrologica_jwt_secret_dev_key_12345';
const JWT_SECRET = new TextEncoder().encode(JWT_SECRET_STRING);
const TOKEN_EXPIRATION = '7d';

export interface UserPayload {
  id: string;
  email: string;
  roles: string[];
}

export async function hashPassword(password: string): Promise<string> {
  const salt = await bcrypt.genSalt(10);
  return bcrypt.hash(password, salt);
}

export async function comparePassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export async function createAuthToken(user: { id: string; email: string; roles: string[] }): Promise<string> {
  return new SignJWT({
    sub: user.id,
    email: user.email,
    roles: user.roles,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(TOKEN_EXPIRATION)
    .sign(JWT_SECRET);
}

export async function verifyAuthToken(token: string): Promise<UserPayload | null> {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    if (!payload.sub || typeof payload.sub !== 'string') return null;
    return {
      id: payload.sub,
      email: (payload.email as string) || '',
      roles: Array.isArray(payload.roles) ? (payload.roles as string[]) : [],
    };
  } catch {
    return null;
  }
}

export async function getUserRoles(userId: string): Promise<string[]> {
  const result = await query<{ role: string }>(
    'SELECT role FROM user_roles WHERE user_id = $1',
    [userId]
  );
  return result.rows.map((r) => r.role);
}

export async function hasRole(userId: string, role: string): Promise<boolean> {
  const result = await query<{ exists: boolean }>(
    'SELECT EXISTS (SELECT 1 FROM user_roles WHERE user_id = $1 AND role = $2) as exists',
    [userId, role]
  );
  return Boolean(result.rows[0]?.exists);
}

export async function countAdmins(): Promise<number> {
  const result = await query<{ count: string }>(
    "SELECT COUNT(*) as count FROM user_roles WHERE role = 'admin'"
  );
  return parseInt(result.rows[0]?.count || '0', 10);
}

export async function addRole(userId: string, role: 'admin' | 'user'): Promise<void> {
  await query(
    'INSERT INTO user_roles (user_id, role) VALUES ($1, $2) ON CONFLICT (user_id, role) DO NOTHING',
    [userId, role]
  );
}
