import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Compass } from "lucide-react";

const EASE = [0.16, 1, 0.3, 1] as const;

export default function BlocoOfertaHeadline() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    // no-op: reserved for future scroll-linked polish
  }, []);

  return (
    <section
      ref={sectionRef}
      aria-label="Você não precisa decorar o céu"
      className="relative isolate w-full overflow-hidden bg-background py-20 md:py-28"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(55% 45% at 50% 30%, color-mix(in oklab, var(--gold) 16%, transparent) 0%, transparent 70%)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-gold/40 to-transparent"
      />

      <div className="relative mx-auto max-w-3xl px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.8, ease: EASE }}
          className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-gold/30 bg-gold/10"
        >
          <Compass className="h-6 w-6 text-gold" />
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.8, ease: EASE, delay: 0.08 }}
          className="mt-7 font-display text-[1.9rem] font-semibold leading-[1.18] text-foreground sm:text-4xl md:text-[2.75rem]"
        >
          Você não precisa decorar o céu.
          <br />
          <span className="text-gold-gradient">Precisa aprender onde olhar.</span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.8, ease: EASE, delay: 0.16 }}
          className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg"
        >
          E é exatamente isso que a{" "}
          <span className="font-semibold text-foreground">Bússola Astrológica</span> vai te
          ensinar.
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={{ duration: 0.7, ease: EASE, delay: 0.3 }}
          className="mx-auto mt-14 flex items-center justify-center gap-4"
        >
          <span className="h-px w-16 bg-gradient-to-r from-transparent to-gold/50" />
          <span className="text-[11px] font-bold uppercase tracking-[0.3em] text-gold-soft/90">
            Tudo que você vai receber
          </span>
          <span className="h-px w-16 bg-gradient-to-l from-transparent to-gold/50" />
        </motion.div>
      </div>
    </section>
  );
}
