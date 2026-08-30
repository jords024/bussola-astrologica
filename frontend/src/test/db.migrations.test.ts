// @vitest-environment node
import { describe, it, expect, vi } from "vitest";
import { runMigrations, INIT_DB_SQL } from "@/lib/db";
import type pg from "pg";

describe("Database Automatic Migrations", () => {
  it("should contain all required table definitions in INIT_DB_SQL", () => {
    expect(INIT_DB_SQL).toContain("CREATE TABLE IF NOT EXISTS users");
    expect(INIT_DB_SQL).toContain("CREATE TABLE IF NOT EXISTS user_roles");
    expect(INIT_DB_SQL).toContain("CREATE TABLE IF NOT EXISTS leads");
    expect(INIT_DB_SQL).toContain("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\"");
    expect(INIT_DB_SQL).toContain("CREATE INDEX IF NOT EXISTS idx_leads_created_at");
  });

  it("should run migrations successfully when pool query succeeds", async () => {
    const mockQuery = vi.fn().mockResolvedValue({ rows: [], rowCount: 0 });
    const mockPool = {
      query: mockQuery,
    } as unknown as pg.Pool;

    const success = await runMigrations(mockPool);
    expect(success).toBe(true);
    expect(mockQuery).toHaveBeenCalledTimes(2);
    expect(mockQuery).toHaveBeenCalledWith(INIT_DB_SQL);
  });

  it("should handle migration error gracefully without throwing", async () => {
    const mockQuery = vi.fn().mockRejectedValue(new Error("Connection refused"));
    const mockPool = {
      query: mockQuery,
    } as unknown as pg.Pool;

    const success = await runMigrations(mockPool);
    expect(success).toBe(false);
  });
});
