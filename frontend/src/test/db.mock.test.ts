// @vitest-environment node
import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as db from '@/lib/db';
import { hasRole, countAdmins, addRole, getUserRoles } from '@/lib/auth.server';

vi.mock('@/lib/db', () => ({
  query: vi.fn(),
}));

describe('Database Roles & Admin Operations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should check if user has admin role', async () => {
    vi.mocked(db.query).mockResolvedValueOnce({
      rows: [{ exists: true }],
      rowCount: 1,
      command: 'SELECT',
      oid: 0,
      fields: [],
    });

    const isAdmin = await hasRole('user-123', 'admin');
    expect(isAdmin).toBe(true);
    expect(db.query).toHaveBeenCalledWith(
      expect.stringContaining('SELECT EXISTS'),
      ['user-123', 'admin']
    );
  });

  it('should count existing admins', async () => {
    vi.mocked(db.query).mockResolvedValueOnce({
      rows: [{ count: '2' }],
      rowCount: 1,
      command: 'SELECT',
      oid: 0,
      fields: [],
    });

    const count = await countAdmins();
    expect(count).toBe(2);
  });

  it('should add a role for a user', async () => {
    vi.mocked(db.query).mockResolvedValueOnce({
      rows: [],
      rowCount: 1,
      command: 'INSERT',
      oid: 0,
      fields: [],
    });

    await addRole('user-456', 'admin');
    expect(db.query).toHaveBeenCalledWith(
      expect.stringContaining('INSERT INTO user_roles'),
      ['user-456', 'admin']
    );
  });

  it('should get all roles for a user', async () => {
    vi.mocked(db.query).mockResolvedValueOnce({
      rows: [{ role: 'admin' }, { role: 'user' }],
      rowCount: 2,
      command: 'SELECT',
      oid: 0,
      fields: [],
    });

    const roles = await getUserRoles('user-789');
    expect(roles).toEqual(['admin', 'user']);
  });
});
