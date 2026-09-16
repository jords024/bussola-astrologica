import { useEffect, useState } from "react";
import { Clock } from "lucide-react";

export interface TimerOfertaProps {
  texto?: string;
  className?: string;
}

export function formatarDataHoje(date = new Date()): string {
  const dia = String(date.getDate()).padStart(2, "0");
  const mes = String(date.getMonth() + 1).padStart(2, "0");
  return `${dia}/${mes}`;
}

export function getTimeUntilMidnight(targetDate = new Date()): {
  hours: number;
  minutes: number;
  seconds: number;
  totalMs: number;
} {
  const now = targetDate;
  const end = new Date(now);
  end.setHours(23, 59, 59, 999);
  const totalMs = Math.max(0, end.getTime() - now.getTime());

  const hours = Math.floor(totalMs / (1000 * 60 * 60));
  const minutes = Math.floor((totalMs / (1000 * 60)) % 60);
  const seconds = Math.floor((totalMs / 1000) % 60);

  return { hours, minutes, seconds, totalMs };
}

export default function TimerOferta({
  texto,
  className = "",
}: TimerOfertaProps) {
  const [dataHoje, setDataHoje] = useState<string>(() => formatarDataHoje());

  const [timeLeft, setTimeLeft] = useState<{
    hours: number;
    minutes: number;
    seconds: number;
  }>(() => {
    const { hours, minutes, seconds } = getTimeUntilMidnight();
    return { hours, minutes, seconds };
  });

  useEffect(() => {
    setDataHoje(formatarDataHoje(new Date()));

    const update = () => {
      const now = new Date();
      setDataHoje(formatarDataHoje(now));
      const { hours, minutes, seconds } = getTimeUntilMidnight(now);
      setTimeLeft({ hours, minutes, seconds });
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const pad = (n: number) => String(n).padStart(2, "0");
  const textoExibido = texto ?? `Válido só hoje (${dataHoje}) até as 23:59`;

  return (
    <div
      data-testid="timer-oferta"
      className={`mx-auto flex w-full max-w-xl flex-col items-center justify-center rounded-2xl border border-gold/30 bg-card/90 px-6 py-4 shadow-[0_10px_35px_-10px_color-mix(in_oklab,var(--gold)_30%,transparent)] backdrop-blur-md ${className}`}
    >
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-gold sm:text-[13px]">
        <Clock className="h-4 w-4 animate-pulse text-gold" />
        <span>{textoExibido}</span>
      </div>

      <div className="mt-3 flex items-center gap-2.5 font-mono text-xl font-bold text-foreground sm:text-2xl">
        <div className="flex flex-col items-center rounded-xl border border-gold/20 bg-background/80 px-3 py-1.5 min-w-[54px] shadow-inner">
          <span>{pad(timeLeft.hours)}</span>
          <span className="text-[9px] font-sans font-medium uppercase tracking-wider text-muted-foreground">
            horas
          </span>
        </div>
        <span className="-mt-3 text-gold/80 font-bold">:</span>
        <div className="flex flex-col items-center rounded-xl border border-gold/20 bg-background/80 px-3 py-1.5 min-w-[54px] shadow-inner">
          <span>{pad(timeLeft.minutes)}</span>
          <span className="text-[9px] font-sans font-medium uppercase tracking-wider text-muted-foreground">
            min
          </span>
        </div>
        <span className="-mt-3 text-gold/80 font-bold">:</span>
        <div className="flex flex-col items-center rounded-xl border border-gold/20 bg-background/80 px-3 py-1.5 min-w-[54px] shadow-inner">
          <span>{pad(timeLeft.seconds)}</span>
          <span className="text-[9px] font-sans font-medium uppercase tracking-wider text-muted-foreground">
            seg
          </span>
        </div>
      </div>
    </div>
  );
}
