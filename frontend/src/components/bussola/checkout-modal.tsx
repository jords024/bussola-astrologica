import { useState, useEffect, useRef } from "react";
import { X, Lock, ShieldCheck, Zap, User, ChevronDown, Check, ArrowRight, Loader2 } from "lucide-react";

export type CountryInfo = {
  code: string;
  name: string;
  ddi: string;
  flag: string;
};

export const COUNTRIES: CountryInfo[] = [
  { code: "BR", name: "Brasil", ddi: "55", flag: "🇧🇷" },
  { code: "PT", name: "Portugal", ddi: "351", flag: "🇵🇹" },
  { code: "US", name: "Estados Unidos", ddi: "1", flag: "🇺🇸" },
  { code: "ES", name: "Espanha", ddi: "34", flag: "🇪🇸" },
  { code: "AR", name: "Argentina", ddi: "54", flag: "🇦🇷" },
  { code: "GB", name: "Reino Unido", ddi: "44", flag: "🇬🇧" },
  { code: "DE", name: "Alemanha", ddi: "49", flag: "🇩🇪" },
  { code: "IT", name: "Itália", ddi: "39", flag: "🇮🇹" },
  { code: "FR", name: "França", ddi: "33", flag: "🇫🇷" },
  { code: "AO", name: "Angola", ddi: "244", flag: "🇦🇴" },
  { code: "MZ", name: "Moçambique", ddi: "258", flag: "🇲🇿" },
  { code: "PY", name: "Paraguai", ddi: "595", flag: "🇵🇾" },
  { code: "UY", name: "Uruguai", ddi: "598", flag: "🇺🇾" },
  { code: "CL", name: "Chile", ddi: "56", flag: "🇨🇱" },
  { code: "CO", name: "Colômbia", ddi: "57", flag: "🇨🇴" },
  { code: "MX", name: "México", ddi: "52", flag: "🇲🇽" },
  { code: "CA", name: "Canadá", ddi: "1", flag: "🇨🇦" },
  { code: "CH", name: "Suíça", ddi: "41", flag: "🇨🇭" },
  { code: "JP", name: "Japão", ddi: "81", flag: "🇯🇵" },
  { code: "AU", name: "Austrália", ddi: "61", flag: "🇦🇺" },
];

export type CheckoutFormData = {
  nome: string;
  whatsapp: string;
  ddi: string;
  countryCode: string;
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CheckoutFormData) => Promise<void> | void;
  isLoading?: boolean;
};

export function formatPhoneByCountry(val: string, countryCode: string): string {
  const digits = val.replace(/\D/g, "");
  if (countryCode === "BR") {
    const sliced = digits.slice(0, 11);
    if (sliced.length <= 2) return sliced.length ? `(${sliced}` : "";
    if (sliced.length <= 6) return `(${sliced.slice(0, 2)}) ${sliced.slice(2)}`;
    if (sliced.length <= 10) return `(${sliced.slice(0, 2)}) ${sliced.slice(2, 6)}-${sliced.slice(6)}`;
    return `(${sliced.slice(0, 2)}) ${sliced.slice(2, 7)}-${sliced.slice(7)}`;
  }
  return digits.slice(0, 15);
}

export default function CheckoutModal({ isOpen, onClose, onSubmit, isLoading = false }: Props) {
  const [nome, setNome] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [selectedCountry, setSelectedCountry] = useState<CountryInfo>(COUNTRIES[0]);
  const [isCountryDropdownOpen, setIsCountryDropdownOpen] = useState(false);
  const [errors, setErrors] = useState<{ nome?: string; whatsapp?: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  // Trava scroll da tela de fundo quando o modal estiver aberto
  useEffect(() => {
    if (isOpen) {
      document.documentElement.style.overflow = "hidden";
      document.body.style.overflow = "hidden";
      document.body.style.touchAction = "none";
      setErrors({});
      setIsCountryDropdownOpen(false);
    } else {
      document.documentElement.style.overflow = "";
      document.body.style.overflow = "";
      document.body.style.touchAction = "";
    }
    return () => {
      document.documentElement.style.overflow = "";
      document.body.style.overflow = "";
      document.body.style.touchAction = "";
    };
  }, [isOpen]);

  // Fecha dropdown de países ao clicar fora dele
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsCountryDropdownOpen(false);
      }
    };
    if (isCountryDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isCountryDropdownOpen]);

  if (!isOpen) return null;

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneByCountry(e.target.value, selectedCountry.code);
    setWhatsapp(formatted);
    if (errors.whatsapp) {
      setErrors((prev) => ({ ...prev, whatsapp: undefined }));
    }
  };

  const handleCountrySelect = (country: CountryInfo) => {
    setSelectedCountry(country);
    setIsCountryDropdownOpen(false);
    // Reformata o telefone já digitado com a regra do novo país
    setWhatsapp((prev) => formatPhoneByCountry(prev, country.code));
  };

  const handleNomeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNome(e.target.value);
    if (errors.nome) {
      setErrors((prev) => ({ ...prev, nome: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { nome?: string; whatsapp?: string } = {};

    const trimmedNome = nome.trim();
    if (!trimmedNome || trimmedNome.length < 3) {
      newErrors.nome = "Por favor, digite seu nome completo.";
    }

    const cleanDigits = whatsapp.replace(/\D/g, "");
    if (selectedCountry.code === "BR") {
      if (cleanDigits.length < 10) {
        newErrors.whatsapp = "Digite seu WhatsApp completo com DDD (10 ou 11 dígitos).";
      }
    } else if (cleanDigits.length < 6) {
      newErrors.whatsapp = "Digite um número de telefone válido.";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setSubmitting(true);
      await onSubmit({
        nome: trimmedNome,
        whatsapp: cleanDigits,
        ddi: selectedCountry.ddi,
        countryCode: selectedCountry.code,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const isBusy = submitting || isLoading;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="checkout-modal-title"
      onWheel={(e) => e.stopPropagation()}
      onTouchMove={(e) => e.stopPropagation()}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overscroll-none touch-none select-none"
    >
      {/* Backdrop — Não fecha ao clicar fora */}
      <div
        className="fixed inset-0 bg-background/85 backdrop-blur-md transition-opacity animate-in fade-in duration-300"
        aria-hidden="true"
      />

      {/* Caixa do Modal */}
      <div
        className="relative w-full max-w-lg overflow-hidden rounded-[26px] border border-gold/35 bg-card/95 p-6 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8),0_0_40px_-10px_color-mix(in_oklab,var(--gold)_30%,transparent)] backdrop-blur-xl sm:p-8 animate-in zoom-in-95 duration-300"
      >
        {/* Glow de fundo */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-56 w-80 rounded-full"
          style={{
            background:
              "radial-gradient(50% 50% at 50% 50%, color-mix(in oklab, var(--gold) 25%, transparent) 0%, transparent 80%)",
          }}
        />

        {/* Botão Fechar (única forma de fechar o modal) */}
        <button
          type="button"
          onClick={onClose}
          disabled={isBusy}
          aria-label="Fechar formulário de compra"
          className="absolute right-4 top-4 rounded-full p-2 text-muted-foreground transition-colors hover:bg-gold/10 hover:text-foreground active:scale-95 disabled:opacity-50"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Cabeçalho */}
        <div className="text-center">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-gold/35 bg-gold/[0.08] px-3.5 py-1 text-[10.5px] font-bold uppercase tracking-[0.2em] text-gold-soft sm:text-[11px]">
            <Zap className="h-3.5 w-3.5 text-gold animate-pulse" />
            Oferta Promocional • Acesso Imediato
          </div>

          <h3
            id="checkout-modal-title"
            className="mt-4 font-display text-2xl font-semibold leading-tight text-foreground sm:text-3xl"
          >
            Para onde enviamos <em className="italic text-gold">seu acesso?</em>
          </h3>
          <p className="mt-2 text-[13.5px] leading-relaxed text-muted-foreground sm:text-sm">
            Preencha seus dados para abrir a página de pagamento 100% seguro da Hotmart com desconto.
          </p>
        </div>

        {/* Resumo da Oferta */}
        <div className="mt-5 rounded-2xl border border-gold/20 bg-background/50 p-3.5 sm:p-4">
          <div className="flex items-center justify-between gap-3 text-xs sm:text-sm">
            <span className="font-medium text-foreground/90">Bússola Astrológica + 4 Bônus</span>
            <div className="text-right">
              <span className="text-xs text-muted-foreground line-through mr-1.5">R$405</span>
              <span className="font-bold text-gold">R$67 à vista</span>
            </div>
          </div>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Campo Nome */}
          <div>
            <label htmlFor="modal-nome" className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Seu nome completo *
            </label>
            <div className="relative mt-1.5">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-gold/60">
                <User className="h-4 w-4" />
              </div>
              <input
                id="modal-nome"
                type="text"
                value={nome}
                onChange={handleNomeChange}
                placeholder="Ex: Maria Silva"
                disabled={isBusy}
                autoComplete="name"
                className={`w-full rounded-xl border bg-background/80 py-3 pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground/50 transition-all focus:outline-none focus:ring-2 ${
                  errors.nome
                    ? "border-destructive focus:border-destructive focus:ring-destructive/30"
                    : "border-gold/25 focus:border-gold focus:ring-gold/25"
                }`}
              />
            </div>
            {errors.nome && <p className="mt-1 text-xs text-destructive">{errors.nome}</p>}
          </div>

          {/* Campo WhatsApp com Seletor de Bandeira / País */}
          <div>
            <label htmlFor="modal-whatsapp" className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Seu WhatsApp com DDD *
            </label>
            <div className="relative mt-1.5 flex rounded-xl border border-gold/25 bg-background/80 focus-within:border-gold focus-within:ring-2 focus-within:ring-gold/25">
              {/* Botão Dropdown País */}
              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  disabled={isBusy}
                  onClick={() => setIsCountryDropdownOpen((prev) => !prev)}
                  className="flex h-full items-center gap-1.5 rounded-l-xl border-r border-gold/20 bg-background/60 px-3 py-3 text-sm font-medium text-foreground transition-colors hover:bg-gold/10 active:scale-95"
                  aria-label={`País selecionado: ${selectedCountry.name} (+${selectedCountry.ddi})`}
                  aria-expanded={isCountryDropdownOpen}
                >
                  <span className="text-lg leading-none" role="img" aria-label={selectedCountry.name}>
                    {selectedCountry.flag}
                  </span>
                  <span className="text-xs font-bold text-gold-soft">+{selectedCountry.ddi}</span>
                  <ChevronDown className="h-3 w-3 text-muted-foreground transition-transform duration-200" />
                </button>

                {/* Lista Dropdown com Bandeiras */}
                {isCountryDropdownOpen && (
                  <div className="absolute left-0 top-full z-50 mt-1 max-h-56 w-60 overflow-y-auto rounded-xl border border-gold/35 bg-card/98 p-1.5 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-150">
                    {COUNTRIES.map((c) => {
                      const isSelected = c.code === selectedCountry.code;
                      return (
                        <button
                          key={c.code}
                          type="button"
                          onClick={() => handleCountrySelect(c)}
                          className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs transition-colors ${
                            isSelected
                              ? "bg-gold/20 font-bold text-gold"
                              : "text-foreground/90 hover:bg-gold/10 hover:text-foreground"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-base leading-none">{c.flag}</span>
                            <span className="truncate">{c.name}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-muted-foreground font-mono">+{c.ddi}</span>
                            {isSelected && <Check className="h-3 w-3 text-gold shrink-0" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Input Telefone */}
              <input
                id="modal-whatsapp"
                type="tel"
                value={whatsapp}
                onChange={handlePhoneChange}
                placeholder={selectedCountry.code === "BR" ? "(00) 00000-0000" : "Número com DDD"}
                disabled={isBusy}
                autoComplete="tel-national"
                className="w-full flex-1 bg-transparent py-3 px-3.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none"
              />
            </div>
            {errors.whatsapp && <p className="mt-1 text-xs text-destructive">{errors.whatsapp}</p>}
          </div>

          {/* Botão de Confirmação */}
          <button
            type="submit"
            disabled={isBusy}
            className="group mt-6 flex w-full items-center justify-center gap-2.5 rounded-xl bg-gradient-to-r from-gold-deep via-gold to-gold-soft px-6 py-4 text-xs font-black uppercase tracking-[0.14em] text-background shadow-[var(--shadow-gold)] transition-transform duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-60 sm:text-sm"
          >
            {isBusy ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Carregando checkout seguro...</span>
              </>
            ) : (
              <>
                <span>Ir para pagamento seguro</span>
                <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
              </>
            )}
          </button>
        </form>

        {/* Rodapé de Confiança */}
        <div className="mt-5 flex flex-wrap items-center justify-center gap-4 text-[11px] text-muted-foreground/80 sm:gap-6">
          <span className="flex items-center gap-1">
            <Lock className="h-3 w-3 text-gold" />
            Ambiente 100% Seguro
          </span>
          <span className="flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-gold" />
            7 dias de garantia
          </span>
        </div>
      </div>
    </div>
  );
}
