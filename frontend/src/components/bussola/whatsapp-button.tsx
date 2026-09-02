import { useState } from "react";
import { fbqTrackCustom } from "@/lib/fbq";

const WHATSAPP_NUMBER = "554792331247";
const WHATSAPP_MESSAGE = "Quero saber mais sobre o Bússola Astrológico";
const WHATSAPP_URL = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;

export default function WhatsappButton() {
  const [hovered, setHovered] = useState(false);

  const handleClick = () => {
    fbqTrackCustom("ClicouWhatsApp", { origem: "botao_flutuante" });
  };

  return (
    <div className="fixed bottom-20 right-4 z-50 flex items-center gap-3 sm:bottom-24 sm:right-6">
      {/* Tooltip opcional no hover */}
      <div
        className={`hidden rounded-full border border-gold/30 bg-[oklch(0.1_0.03_265/0.95)] px-4 py-1.5 text-xs font-medium text-foreground shadow-lg backdrop-blur-md transition-all duration-300 sm:block ${
          hovered ? "translate-x-0 opacity-100" : "pointer-events-none translate-x-2 opacity-0"
        }`}
      >
        Tire suas dúvidas no WhatsApp
      </div>

      <a
        href={WHATSAPP_URL}
        target="_blank"
        rel="noopener noreferrer"
        onClick={handleClick}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        aria-label="Fale conosco no WhatsApp"
        className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-[0_8px_25px_rgba(37,211,102,0.45)] transition-all duration-300 hover:scale-110 hover:bg-[#20bd5a] hover:shadow-[0_10px_30px_rgba(37,211,102,0.65)] active:scale-95 sm:h-15 sm:w-15"
      >
        {/* Anel de pulso sutil */}
        <span className="pointer-events-none absolute inset-0 -z-10 animate-ping rounded-full bg-[#25D366]/40 opacity-75 duration-1000" />

        {/* Ícone SVG oficial do WhatsApp */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="h-7 w-7 transition-transform duration-300 group-hover:scale-105 sm:h-8 sm:w-8"
        >
          <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91C2.13 13.66 2.59 15.36 3.45 16.86L2.05 22L7.3 20.62C8.75 21.41 10.38 21.83 12.04 21.83C17.5 21.83 21.95 17.38 21.95 11.92C21.95 9.27 20.92 6.78 19.05 4.91C17.18 3.03 14.69 2 12.04 2M12.05 3.67C14.25 3.67 16.31 4.53 17.87 6.09C19.42 7.65 20.28 9.72 20.28 11.92C20.28 16.46 16.58 20.15 12.04 20.15C10.56 20.15 9.11 19.76 7.85 19L7.55 18.83L4.43 19.65L5.26 16.61L5.06 16.29C4.24 15 3.8 13.47 3.8 11.91C3.81 7.37 7.5 3.67 12.05 3.67M9.16 7.68C9 7.68 8.78 7.74 8.6 7.95C8.42 8.16 7.91 8.64 7.91 9.61C7.91 10.58 8.62 11.51 8.72 11.65C8.82 11.79 10.1 13.77 12.06 14.62C12.53 14.82 12.89 14.94 13.17 15.03C13.64 15.18 14.07 15.16 14.41 15.11C14.79 15.05 15.58 14.63 15.75 14.16C15.92 13.69 15.92 13.28 15.87 13.2C15.82 13.12 15.69 13.07 15.5 12.97C15.31 12.87 14.39 12.42 14.22 12.36C14.05 12.3 13.93 12.27 13.8 12.47C13.67 12.67 13.31 13.09 13.2 13.22C13.09 13.35 12.98 13.37 12.79 13.27C12.6 13.17 11.8 12.91 10.85 12.06C10.11 11.4 9.61 10.59 9.47 10.35C9.33 10.11 9.45 9.98 9.55 9.88C9.64 9.79 9.75 9.64 9.85 9.53C9.95 9.42 9.99 9.34 10.05 9.21C10.11 9.08 10.08 8.97 10.03 8.87C9.98 8.77 9.58 7.79 9.42 7.39C9.26 7 9.1 7.05 8.97 7.05H8.62L9.16 7.68Z" />
        </svg>
      </a>
    </div>
  );
}
