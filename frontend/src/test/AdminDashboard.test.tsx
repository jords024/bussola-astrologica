import { describe, it, expect } from 'vitest';
import type { LeadRow } from '@/lib/leads.functions';

describe('Admin Dashboard Data Logic', () => {
  const mockLeads: LeadRow[] = [
    {
      id: '1',
      created_at: new Date(Date.now() - 1000 * 60 * 60).toISOString(), // 1 hour ago
      nome: 'Carlos Silva',
      email: 'carlos@exemplo.com',
      whatsapp: '11999998888',
      origem: 'instagram',
      ip: '127.0.0.1',
      cidade: 'São Paulo',
      regiao: 'SP',
      pais: 'BR',
      timezone: 'America/Sao_Paulo',
      user_agent: 'Mozilla/5.0',
      referrer: null,
      utm_source: 'meta_ads',
      utm_medium: 'cpc',
      utm_campaign: 'lancamento',
    },
    {
      id: '2',
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // 2 days ago
      nome: 'Mariana Santos',
      email: 'mariana@exemplo.com',
      whatsapp: '21988887777',
      origem: 'google',
      ip: '127.0.0.1',
      cidade: 'Rio de Janeiro',
      regiao: 'RJ',
      pais: 'BR',
      timezone: 'America/Sao_Paulo',
      user_agent: 'Mozilla/5.0',
      referrer: null,
      utm_source: null,
      utm_medium: null,
      utm_campaign: null,
    },
  ];

  it('should filter leads by search term', () => {
    const query = 'carlos';
    const filtered = mockLeads.filter((l) =>
      [l.nome, l.email, l.whatsapp, l.cidade, l.regiao, l.pais, l.origem]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(query.toLowerCase()))
    );

    expect(filtered).toHaveLength(1);
    expect(filtered[0].nome).toBe('Carlos Silva');
  });

  it('should calculate recent lead metrics correctly', () => {
    const now = Date.now();
    const day = 24 * 60 * 60 * 1000;
    const today = mockLeads.filter((l) => now - new Date(l.created_at).getTime() < day).length;
    const week = mockLeads.filter((l) => now - new Date(l.created_at).getTime() < 7 * day).length;

    expect(today).toBe(1);
    expect(week).toBe(2);
  });
});
