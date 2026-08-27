import pg from 'pg';

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
  const user = process.env.PGUSER || 'postgres';
  const password = process.env.PGPASSWORD || 'postgres';
  const host = process.env.PGHOST || 'localhost';
  const port = process.env.PGPORT || '5432';
  const database = process.env.PGDATABASE || 'bussola_astrologica';
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

  pool.on('error', (err) => {
    console.error('Unexpected error on idle PostgreSQL client', err);
  });

  return pool;
}

export const pool = globalThis.__pg_pool ?? createPool();
if (process.env.NODE_ENV !== 'production') {
  globalThis.__pg_pool = pool;
}

export async function query<R extends pg.QueryResultRow = pg.QueryResultRow>(
  text: string,
  params?: unknown[]
): Promise<pg.QueryResult<R>> {
  return pool.query<R>(text, params);
}
