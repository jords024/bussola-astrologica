import pg from "pg";

const { Pool } = pg;

// Singleton pool instance across hot reloads and SSR invocations
declare global {
  // eslint-disable-next-line no-var
  var __pg_pool: pg.Pool | undefined;
}

function getConnectionString(): string {
  if (process.env.DATABASE_URL) {
    return process.env.DATABASE_URL;
  }
  const user = process.env.PGUSER || "postgres";
  const password = process.env.PGPASSWORD || "postgres";
  const host = process.env.PGHOST || "localhost";
  const port = process.env.PGPORT || "5432";
  const database = process.env.PGDATABASE || "bussola_astrologica";
  return `postgres://${user}:${password}@${host}:${port}/${database}`;
}

export function createPool(): pg.Pool {
  const connectionString = getConnectionString();
  const pool = new Pool({
    connectionString,
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  });

  pool.on("error", (err) => {
    console.error("Unexpected error on idle PostgreSQL client", err);
  });

  return pool;
}

export const pool = globalThis.__pg_pool ?? createPool();
if (process.env.NODE_ENV !== "production") {
  globalThis.__pg_pool = pool;
}

export const INIT_DB_SQL = `
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, role)
);

CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  nome TEXT NOT NULL,
  email TEXT,
  whatsapp TEXT NOT NULL,
  origem TEXT,
  ip TEXT,
  cidade TEXT,
  regiao TEXT,
  pais TEXT,
  timezone TEXT,
  user_agent TEXT,
  referrer TEXT,
  utm_source TEXT,
  utm_medium TEXT,
  utm_campaign TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles (user_id);
`;

export async function runMigrations(targetPool: pg.Pool = pool): Promise<boolean> {
  try {
    await targetPool.query(INIT_DB_SQL);
    await targetPool.query("ALTER TABLE leads ALTER COLUMN email DROP NOT NULL").catch(() => {});
    return true;
  } catch (err) {
    console.warn("⚠️ [BANCO DE DADOS] Aviso ao rodar auto-migração:", err);
    return false;
  }
}

// Executa auto-migração não bloqueante ao carregar o módulo (fora de ambiente de testes)
if (!process.env.VITEST && process.env.NODE_ENV !== "test") {
  runMigrations().catch(() => {});
}

export async function query<R extends pg.QueryResultRow = pg.QueryResultRow>(
  text: string,
  params?: unknown[],
): Promise<pg.QueryResult<R>> {
  return pool.query<R>(text, params);
}
