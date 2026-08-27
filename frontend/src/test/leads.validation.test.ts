import { describe, it, expect } from 'vitest';
import { clean } from '@/lib/leads.functions';

describe('Lead Validation & Cleaning', () => {
  it('should clean and trim string values', () => {
    expect(clean('  joao silva  ')).toBe('joao silva');
    expect(clean('   ')).toBeNull();
    expect(clean(null)).toBeNull();
    expect(clean(undefined)).toBeNull();
    expect(clean(12345)).toBeNull();
  });

  it('should truncate strings exceeding maximum length', () => {
    const longString = 'a'.repeat(200);
    const result = clean(longString, 50);
    expect(result).not.toBeNull();
    expect(result?.length).toBe(50);
  });

  it('should validate email format correctly', () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    expect(emailRegex.test('usuario@exemplo.com')).toBe(true);
    expect(emailRegex.test('contato.teste@dominio.com.br')).toBe(true);
    expect(emailRegex.test('invalido-sem-arroba')).toBe(false);
    expect(emailRegex.test('invalido@semdominio')).toBe(false);
  });
});
