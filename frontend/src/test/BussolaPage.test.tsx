import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import HeroBussola from '@/components/bussola/hero-bussola';
import BlocoTudoFlui from '@/components/bussola/bloco-tudo-flui';
import BlocoSemanaSeguinte from '@/components/bussola/bloco-semana-seguinte';
import Bloco12Portas from '@/components/bussola/bloco-12-portas';
import BlocoHistoriaCrassus from '@/components/bussola/bloco-historia-crassus';
import BlocoFAQ from '@/components/bussola/bloco-faq';
import WhatsappButton from '@/components/bussola/whatsapp-button';
import RodapeBussola from '@/components/bussola/rodape-bussola';

describe('Bussola Sales Page Components', () => {
  it('should render HeroBussola with CTA button and eager loading', () => {
    const onCheckout = () => {};
    render(<HeroBussola onCheckout={onCheckout} />);
    const ctaButtons = screen.getAllByRole('button');
    expect(ctaButtons.length).toBeGreaterThan(0);
    const heroImg = screen.getByAltText(/Roda zodiacal dourada/i);
    expect(heroImg).toHaveAttribute('loading', 'eager');
    expect(heroImg).toHaveAttribute('fetchpriority', 'high');
  });

  it('should render BlocoTudoFlui with eager loading for fast above-the-fold display', () => {
    render(<BlocoTudoFlui />);
    const img = screen.getByAltText(/Tem semana que tudo flui/i);
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('loading', 'eager');
    expect(img).toHaveAttribute('fetchpriority', 'high');
  });

  it('should render BlocoSemanaSeguinte with eager loading', () => {
    render(<BlocoSemanaSeguinte />);
    const img = screen.getByAltText(/Aí chega a semana seguinte/i);
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('loading', 'eager');
    expect(img).toHaveAttribute('fetchpriority', 'high');
  });

  it('should render Bloco12Portas with image correctly', () => {
    render(<Bloco12Portas />);
    const img = screen.getByAltText(/As 12 Portas/i);
    expect(img).toBeInTheDocument();
  });

  it('should render BlocoHistoriaCrassus with eager portrait', () => {
    render(<BlocoHistoriaCrassus />);
    const img = screen.getByAltText(/Crassus Gobbi, astrólogo/i);
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('loading', 'eager');
  });

  it('should include BlocoFAQ with all questions', () => {
    render(<BlocoFAQ />);
    expect(screen.getByText(/Como vou receber o acesso\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Preciso saber astrologia para conseguir usar\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Por quanto tempo terei acesso\?/i)).toBeInTheDocument();
  });

  it('should render WhatsappButton correctly', () => {
    render(<WhatsappButton />);
    expect(screen.getByRole('link', { name: /Fale conosco no WhatsApp/i })).toBeInTheDocument();
  });

  it('should render RodapeBussola with CNPJ and legal links', () => {
    render(<RodapeBussola />);
    expect(screen.getByText(/43\.066\.768\/0001-70/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Políticas de Privacidade/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Termos de Uso/i })).toBeInTheDocument();
  });
});
