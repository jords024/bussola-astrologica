import React, { useEffect, useState } from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  delayRender,
  continueRender,
} from 'remotion';
import { ThreeCanvas } from '@remotion/three';
import { Shape } from 'three';
import captionsData from './tour-captions.json';

// --- Color Palette ---
const ink = '#0c0a13';
const cream = '#f5efe6';
const gold = '#dbad60';
const purple = '#b8a4e8';
const lime = '#d8ea9c';

// --- Easing Helpers ---
const ease = (f: number, d = 20) =>
  interpolate(f, [0, d], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });

const pop = (f: number, damping = 18, stiffness = 130) =>
  spring({ frame: f, fps: 30, config: { damping, stiffness } });

const displayStyle: React.CSSProperties = {
  fontFamily: 'Display, sans-serif',
  fontWeight: 400,
  lineHeight: 0.92,
  letterSpacing: -3,
};

// --- Scene Bounds (Frames) based on edge-tts audio timings ---
const bounds = [0, 438, 953, 1479, 1846];

// --- 3D Three.js Components ---
const GoldMat = () => (
  <meshPhongMaterial color="#dbad60" specular="#fff5df" shininess={90} />
);

function Compass3D({ frame }: { frame: number }) {
  const rot = frame * 0.015;
  return (
    <group rotation={[0.25, rot, -0.1]}>
      {/* Outer rim */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[1.2, 1.2, 0.18, 64]} />
        <meshStandardMaterial color="#171424" metalness={0.65} roughness={0.28} />
      </mesh>
      <mesh position={[0, 0, 0.12]}>
        <torusGeometry args={[1.14, 0.065, 16, 72]} />
        <GoldMat />
      </mesh>
      {/* 12 House Markers */}
      {Array.from({ length: 12 }, (_, i) => {
        const a = (i * Math.PI) / 6;
        return (
          <mesh
            key={i}
            position={[Math.sin(a) * 0.95, Math.cos(a) * 0.95, 0.15]}
            rotation={[0, 0, -a]}
          >
            <boxGeometry args={[0.032, i % 3 === 0 ? 0.18 : 0.08, 0.04]} />
            <GoldMat />
          </mesh>
        );
      })}
      {/* Astrological Needle */}
      <group rotation={[0, 0, Math.sin(frame * 0.03) * 0.4 - 0.3]}>
        <mesh position={[0, 0.36, 0.22]}>
          <coneGeometry args={[0.18, 0.95, 4]} />
          <GoldMat />
        </mesh>
        <mesh position={[0, -0.36, 0.22]} rotation={[0, 0, Math.PI]}>
          <coneGeometry args={[0.18, 0.95, 4]} />
          <meshStandardMaterial color="#f7ecdc" metalness={0.5} roughness={0.25} />
        </mesh>
      </group>
      <mesh position={[0, 0, 0.28]}>
        <sphereGeometry args={[0.12, 24, 24]} />
        <GoldMat />
      </mesh>
    </group>
  );
}

function ArmillaryGlobe3D({ frame }: { frame: number }) {
  return (
    <group rotation={[0.5, frame * 0.012, -0.28]}>
      {[0, 1, 2].map((i) => (
        <mesh key={i} rotation={[i * (Math.PI / 3), (Math.PI / 3) * i, frame * 0.003]}>
          <torusGeometry args={[1.7 - i * 0.15, 0.026, 16, 96]} />
          <meshStandardMaterial
            color={i === 1 ? purple : gold}
            metalness={0.8}
            roughness={0.2}
          />
        </mesh>
      ))}
      {/* Glowing Center Core */}
      <mesh rotation={[frame * 0.015, 0.3, frame * 0.01]}>
        <octahedronGeometry args={[0.55]} />
        <meshStandardMaterial color={purple} metalness={0.8} roughness={0.18} />
      </mesh>
      {/* 12 Zodiac Nodes */}
      {Array.from({ length: 12 }, (_, i) => {
        const a = (i * Math.PI) / 6;
        return (
          <mesh key={i} position={[Math.cos(a) * 1.7, Math.sin(a) * 1.7, 0]}>
            <sphereGeometry args={[i % 3 === 0 ? 0.1 : 0.05, 16, 16]} />
            <meshStandardMaterial
              color={i % 3 === 0 ? lime : cream}
              metalness={0.5}
              roughness={0.2}
            />
          </mesh>
        );
      })}
    </group>
  );
}

function CycleTransit3D({ frame }: { frame: number }) {
  return (
    <group rotation={[0.4 + Math.sin(frame * 0.02) * 0.1, frame * 0.02, -0.25]}>
      <mesh>
        <torusGeometry args={[1.05, 0.14, 24, 80, Math.PI * 1.7]} />
        <GoldMat />
      </mesh>
      <mesh position={[0.6, -0.85, 0]} rotation={[0, 0, -0.55]}>
        <coneGeometry args={[0.3, 0.55, 4]} />
        <GoldMat />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0.3]}>
        <torusGeometry args={[0.65, 0.04, 16, 64]} />
        <meshStandardMaterial color={purple} metalness={0.7} roughness={0.2} />
      </mesh>
    </group>
  );
}

function LetterMessage3D({ frame }: { frame: number }) {
  const body = new Shape();
  body.moveTo(-0.86, -0.58);
  body.lineTo(0.86, -0.58);
  body.quadraticCurveTo(1, -0.58, 1, -0.44);
  body.lineTo(1, 0.44);
  body.quadraticCurveTo(1, 0.58, 0.86, 0.58);
  body.lineTo(-0.86, 0.58);
  body.quadraticCurveTo(-1, 0.58, -1, 0.44);
  body.lineTo(-1, -0.44);
  body.quadraticCurveTo(-1, -0.58, -0.86, -0.58);

  const flap = new Shape();
  flap.moveTo(-0.96, 0.58);
  flap.lineTo(0, -0.08);
  flap.lineTo(0.96, 0.58);
  flap.closePath();

  return (
    <group rotation={[0.22, -0.48 + Math.sin(frame * 0.02) * 0.15, -0.1]}>
      <mesh position={[0, 0, -0.2]}>
        <extrudeGeometry
          args={[
            body,
            { depth: 0.3, bevelEnabled: true, bevelSize: 0.065, bevelThickness: 0.065, bevelSegments: 5, steps: 1 },
          ]}
        />
        <meshPhongMaterial color="#201a35" specular="#b8a4e8" shininess={65} />
      </mesh>
      <mesh position={[0, 0, 0.12]}>
        <extrudeGeometry
          args={[
            flap,
            { depth: 0.035, bevelEnabled: true, bevelSize: 0.015, bevelThickness: 0.015, bevelSegments: 2, steps: 1 },
          ]}
        />
        <GoldMat />
      </mesh>
      <mesh position={[0, -0.12, 0.26]} scale={[1, 1, 0.4]}>
        <sphereGeometry args={[0.2, 32, 24]} />
        <GoldMat />
      </mesh>
      <mesh position={[-0.15, 0.88, -0.06]} rotation={[0, 0, 0.07]}>
        <boxGeometry args={[1.35, 0.55, 0.06]} />
        <meshStandardMaterial color="#f5e6c9" roughness={0.6} />
      </mesh>
    </group>
  );
}

function SparkStar3D({ frame }: { frame: number }) {
  return (
    <group rotation={[0.15, frame * 0.02, 0.1]}>
      {[0, Math.PI / 2, Math.PI, Math.PI * 1.5].map((a, i) => (
        <mesh key={i} position={[Math.sin(a) * 0.45, Math.cos(a) * 0.45, 0]} rotation={[0, 0, -a]}>
          <coneGeometry args={[0.26, 1.15, 4]} />
          <GoldMat />
        </mesh>
      ))}
      <mesh>
        <octahedronGeometry args={[0.4]} />
        <GoldMat />
      </mesh>
      <mesh position={[1.0, 0.9, 0.1]}>
        <octahedronGeometry args={[0.22]} />
        <meshStandardMaterial color={lime} metalness={0.5} roughness={0.2} />
      </mesh>
    </group>
  );
}

// --- Orbital Background Rings ---
function OrbitsVfx({ f }: { f: number }) {
  return (
    <AbsoluteFill style={{ overflow: 'hidden', opacity: 0.55, pointerEvents: 'none' }}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: 1400,
            height: 780,
            left: -160,
            top: 480 + i * 130,
            border: `1px solid ${i === 1 ? 'rgba(184, 164, 232, 0.25)' : 'rgba(219, 173, 96, 0.18)'}`,
            borderRadius: '50%',
            transform: `rotate(${-28 + i * 34 + f * 0.03}deg)`,
          }}
        />
      ))}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at 50% 40%, rgba(121, 97, 147, 0.22), transparent 70%)',
        }}
      />
    </AbsoluteFill>
  );
}

// --- Scene Kinetic Title ---
function SceneTitle({
  tag,
  title,
  sub,
  t,
}: {
  tag: string;
  title: string;
  sub: string;
  t: number;
}) {
  const eTag = ease(t, 14);
  const eTitle = ease(t, 20);
  const eSub = ease(t - 6, 20);

  return (
    <div style={{ position: 'absolute', top: 190, left: 75, right: 75, zIndex: 10 }}>
      {/* Category Pill */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 16px',
          background: 'rgba(219, 173, 96, 0.12)',
          border: '1px solid rgba(219, 173, 96, 0.3)',
          borderRadius: 20,
          color: gold,
          fontSize: 18,
          letterSpacing: 3,
          fontWeight: 600,
          opacity: eTag,
          transform: `translateY(${(1 - eTag) * 20}px)`,
          marginBottom: 16,
        }}
      >
        <span>✦</span> {tag}
      </div>

      {/* Main Punchy Title */}
      <div style={{ overflow: 'hidden', paddingBottom: 6 }}>
        <div
          style={{
            ...displayStyle,
            fontSize: 120,
            color: cream,
            transform: `translateY(${(1 - eTitle) * 140}px)`,
          }}
        >
          {title}
        </div>
      </div>

      {/* Editorial Subtitle */}
      <div
        style={{
          fontFamily: 'Editorial, serif',
          fontStyle: 'italic',
          fontSize: 68,
          color: purple,
          lineHeight: 1.15,
          marginTop: 4,
          opacity: eSub,
          transform: `translateX(${(1 - eSub) * 45}px)`,
        }}
      >
        {sub}
      </div>
    </div>
  );
}

// --- Dynamic 3D Dashboard Showcase ---
function Dashboard3D({
  scene,
  t,
  f,
}: {
  scene: number;
  t: number;
  f: number;
}) {
  const enterSpring = pop(t);

  // Dynamic Camera transformations per scene
  let containerTransform = '';
  let imgTransform = '';
  let highlightCard: React.ReactNode = null;

  if (scene === 0) {
    // Scene 0: Overview - deep 3D perspective floating
    const floatY = Math.sin(f * 0.04) * 10;
    const rotY = -12 + Math.sin(f * 0.02) * 3;
    const rotX = 9 + Math.cos(f * 0.02) * 2;
    containerTransform = `perspective(1600px) translateY(${(1 - enterSpring) * 300 + floatY}px) rotateY(${rotY}deg) rotateX(${rotX}deg) scale(${0.88 + enterSpring * 0.04})`;
    imgTransform = 'scale(1) translate(0, 0)';
  } else if (scene === 1) {
    // Scene 1: Focus on Sol, Lua, Ascendente (left section of screenshot)
    const floatY = Math.sin(f * 0.04) * 8;
    containerTransform = `perspective(1600px) translateY(${floatY}px) rotateY(-8deg) rotateX(6deg) scale(0.96)`;
    imgTransform = `scale(1.95) translate(220px, 10px)`;
    highlightCard = (
      <div
        style={{
          position: 'absolute',
          left: 40,
          top: 360,
          padding: '14px 22px',
          background: 'rgba(20, 16, 32, 0.92)',
          border: `1px solid ${gold}`,
          borderRadius: 14,
          boxShadow: '0 15px 40px rgba(0,0,0,0.6)',
          zIndex: 20,
          opacity: ease(t - 10, 15),
          transform: `translateY(${(1 - ease(t - 10, 15)) * 25}px)`,
        }}
      >
        <div style={{ fontSize: 16, letterSpacing: 3, color: gold, fontWeight: 700 }}>
          ✦ AS 3 FORÇAS NATAL
        </div>
        <div style={{ fontFamily: 'Editorial, serif', fontSize: 26, color: cream, marginTop: 4 }}>
          Sol · Lua · Ascendente
        </div>
      </div>
    );
  } else if (scene === 2) {
    // Scene 2: Focus on Mandala & O Mais Forte de Hoje
    const floatY = Math.sin(f * 0.04) * 8;
    containerTransform = `perspective(1600px) translateY(${floatY}px) rotateY(10deg) rotateX(6deg) scale(0.96)`;
    // Centering the Mandala wheel nicely
    imgTransform = `scale(1.85) translate(-70px, 15px)`;
    highlightCard = (
      <div
        style={{
          position: 'absolute',
          right: 40,
          top: 360,
          padding: '14px 22px',
          background: 'rgba(20, 16, 32, 0.92)',
          border: `1px solid ${lime}`,
          borderRadius: 14,
          boxShadow: '0 15px 40px rgba(0,0,0,0.6)',
          zIndex: 20,
          opacity: ease(t - 10, 15),
          transform: `translateY(${(1 - ease(t - 10, 15)) * 25}px)`,
        }}
      >
        <div style={{ fontSize: 16, letterSpacing: 3, color: lime, fontWeight: 700 }}>
          ✦ SUA PORTA ABERTA
        </div>
        <div style={{ fontFamily: 'Editorial, serif', fontSize: 26, color: cream, marginTop: 4 }}>
          Casa 10 · Carreira em Alta
        </div>
      </div>
    );
  } else if (scene === 3) {
    // Scene 3: A Leitura & Plano de Ação
    const floatY = Math.sin(f * 0.04) * 8;
    containerTransform = `perspective(1600px) translateY(${floatY}px) rotateY(-5deg) rotateX(4deg) scale(0.94)`;
    imgTransform = `scale(1.7) translate(-60px, -30px)`;
    highlightCard = (
      <div
        style={{
          position: 'absolute',
          left: 45,
          top: 340,
          padding: '18px 24px',
          background: 'rgba(17, 14, 28, 0.94)',
          border: `1px solid ${purple}`,
          borderRadius: 16,
          boxShadow: '0 20px 50px rgba(0,0,0,0.7)',
          zIndex: 20,
          opacity: ease(t - 10, 15),
          transform: `translateY(${(1 - ease(t - 10, 15)) * 25}px)`,
        }}
      >
        <div style={{ fontSize: 16, letterSpacing: 3, color: purple, fontWeight: 700 }}>
          ✦ DIRECIONAMENTO TÁTICO
        </div>
        <div style={{ fontSize: 22, color: cream, marginTop: 6, lineHeight: 1.3 }}>
          Onde agir com força hoje & onde segurar a onda.
        </div>
      </div>
    );
  } else {
    // Scene 4: Grand Hero Conclusion
    const floatY = Math.sin(f * 0.04) * 10;
    containerTransform = `perspective(1600px) translateY(${floatY}px) rotateY(0deg) rotateX(4deg) scale(${0.92 + Math.sin(f * 0.03) * 0.02})`;
    imgTransform = 'scale(1.02) translate(0, 0)';
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: 55,
        right: 55,
        top: 640,
        height: 520,
        transform: containerTransform,
        transition: 'transform 0.4s ease-out',
        borderRadius: 24,
        overflow: 'hidden',
        border: `2px solid ${scene === 2 ? lime : scene === 1 ? gold : purple}`,
        boxShadow: `0 40px 90px rgba(0, 0, 0, 0.8), 0 0 45px ${scene === 2 ? 'rgba(216, 234, 156, 0.15)' : 'rgba(184, 164, 232, 0.18)'}`,
        background: '#141122',
        zIndex: 5,
      }}
    >
      {/* Screenshot with dynamic zoom & crop */}
      <div
        style={{
          width: '100%',
          height: '100%',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <Img
          src={staticFile('painel-jordao.png')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: imgTransform,
            transition: 'transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
            transformOrigin: '50% 50%',
          }}
        />
        {/* Glass reflection gradient */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 40%, rgba(0,0,0,0.3) 100%)',
            pointerEvents: 'none',
          }}
        />
      </div>
      {highlightCard}
    </div>
  );
}

// --- Main Remotion Composition ---
export const PainelTourMotion: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Load Editorial & Display Fonts
  const [handle] = useState(() => delayRender('Carregando fontes'));
  useEffect(() => {
    Promise.all([
      ['Display', 'display.ttf'],
      ['Editorial', 'italic.ttf'],
      ['Body', 'body.ttf'],
      ['BodyBold', 'body-bold.ttf'],
    ].map(async ([name, file]) => {
      const font = new FontFace(name, `url(${staticFile('quiz-v2/' + file)})`);
      await font.load();
      document.fonts.add(font);
    })).then(() => continueRender(handle));
  }, [handle]);

  // Find active scene & local time t
  const scene = bounds.reduce((acc, v, idx) => (f >= v ? idx : acc), 0);
  const t = f - bounds[scene];

  // Active caption
  const currentTimeSec = f / 30;
  const activeCap = captionsData.captions.find(
    (c) => currentTimeSec >= c.start && currentTimeSec < c.end
  );
  const capEase = activeCap ? ease(f - activeCap.start * 30, 6) : 0;

  return (
    <AbsoluteFill
      style={{
        background: ink,
        color: cream,
        fontFamily: 'Body, sans-serif',
        overflow: 'hidden',
      }}
    >
      {/* Background Audio */}
      <Audio src={staticFile('tour-narration.mp3')} volume={1.0} />
      <Audio src={staticFile('quiz-v2/motion.wav')} volume={0.35} />

      {/* Orbits & Atmospheric Background VFX */}
      <OrbitsVfx f={f} />

      {/* Top Brand Bar */}
      <div
        style={{
          position: 'absolute',
          top: 90,
          left: 75,
          right: 75,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 22,
          letterSpacing: 4,
          color: cream,
          zIndex: 20,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: gold, fontSize: 26 }}>✦</span>
          <span>
            BÚSSOLA <span style={{ opacity: 0.5, fontWeight: 300 }}>ASTROLÓGICA</span>
          </span>
        </div>
        <div
          style={{
            fontSize: 20,
            color: purple,
            fontWeight: 600,
            letterSpacing: 2,
            background: 'rgba(184, 164, 232, 0.12)',
            padding: '4px 14px',
            borderRadius: 16,
            border: '1px solid rgba(184, 164, 232, 0.25)',
          }}
        >
          0{scene + 1} / 05
        </div>
      </div>

      {/* Scene Titles */}
      {scene === 0 && (
        <SceneTitle
          tag="O SEU MOMENTO"
          title="CHEGA DE DÚVIDA"
          sub="na sua rotina real."
          t={t}
        />
      )}
      {scene === 1 && (
        <SceneTitle
          tag="QUEM VOCÊ É"
          title="SUAS 3 FORÇAS"
          sub="claras e sem complicação."
          t={t}
        />
      )}
      {scene === 2 && (
        <SceneTitle
          tag="O SEU CÉU HOJE"
          title="A PORTA ABERTA"
          sub="o que avança esta semana."
          t={t}
        />
      )}
      {scene === 3 && (
        <SceneTitle
          tag="DIRECIONAMENTO"
          title="AÇÃO DIRETA"
          sub="sem previsões genéricas."
          t={t}
        />
      )}
      {scene === 4 && (
        <SceneTitle
          tag="CLAREZA DIÁRIA"
          title="SUA BÚSSOLA"
          sub="2 minutos pela manhã."
          t={t}
        />
      )}

      {/* Dynamic 3D Dashboard Showcase */}
      <Dashboard3D scene={scene} t={t} f={f} />

      {/* 3D Floating VFX Icons Canvas */}
      <div
        style={{
          position: 'absolute',
          right: 50,
          top: 1190,
          width: 380,
          height: 380,
          zIndex: 15,
        }}
      >
        <ThreeCanvas
          width={380}
          height={380}
          camera={{ position: [0, 0, 4.8], fov: 40 }}
          gl={{ alpha: true, antialias: true }}
          style={{ background: 'transparent' }}
        >
          <ambientLight intensity={1.4} />
          <directionalLight position={[3, 4, 5]} intensity={4.2} />
          <directionalLight position={[-3, -1, 2]} color={purple} intensity={2.2} />

          {scene === 0 && <Compass3D frame={f} />}
          {scene === 1 && <ArmillaryGlobe3D frame={f} />}
          {scene === 2 && <CycleTransit3D frame={f} />}
          {scene === 3 && <LetterMessage3D frame={f} />}
          {scene === 4 && <SparkStar3D frame={f} />}
        </ThreeCanvas>
      </div>

      {/* Left Bottom Feature Callout */}
      <div
        style={{
          position: 'absolute',
          left: 75,
          top: 1250,
          maxWidth: 540,
          zIndex: 15,
        }}
      >
        {scene === 0 && (
          <div style={{ opacity: ease(t - 8, 18) }}>
            <div style={{ fontSize: 20, letterSpacing: 4, color: gold, fontWeight: 600 }}>
              FERRAMENTA DIÁRIA
            </div>
            <div
              style={{
                fontFamily: 'Editorial, serif',
                fontSize: 44,
                lineHeight: 1.2,
                color: cream,
                marginTop: 8,
              }}
            >
              Para quem não tem tempo a perder.
            </div>
          </div>
        )}
        {scene === 1 && (
          <div style={{ opacity: ease(t - 8, 18) }}>
            <div style={{ fontSize: 20, letterSpacing: 4, color: purple, fontWeight: 600 }}>
              MAPA DESCOMPLICADO
            </div>
            <div
              style={{
                fontFamily: 'Editorial, serif',
                fontSize: 44,
                lineHeight: 1.2,
                color: cream,
                marginTop: 8,
              }}
            >
              Suas forças aplicadas na prática.
            </div>
          </div>
        )}
        {scene === 2 && (
          <div style={{ opacity: ease(t - 8, 18) }}>
            <div style={{ fontSize: 20, letterSpacing: 4, color: lime, fontWeight: 600 }}>
              CÁLCULO EM TEMPO REAL
            </div>
            <div
              style={{
                fontFamily: 'Editorial, serif',
                fontSize: 44,
                lineHeight: 1.2,
                color: cream,
                marginTop: 8,
              }}
            >
              Onde o vento sopra a favor hoje.
            </div>
          </div>
        )}
        {scene === 3 && (
          <div style={{ opacity: ease(t - 8, 18) }}>
            <div style={{ fontSize: 20, letterSpacing: 4, color: gold, fontWeight: 600 }}>
              ESTRATÉGIA PURA
            </div>
            <div
              style={{
                fontFamily: 'Editorial, serif',
                fontSize: 44,
                lineHeight: 1.2,
                color: cream,
                marginTop: 8,
              }}
            >
              Decisões com segurança e foco.
            </div>
          </div>
        )}
        {scene === 4 && (
          <div style={{ opacity: ease(t - 8, 18) }}>
            <div style={{ fontSize: 20, letterSpacing: 4, color: lime, fontWeight: 600 }}>
              ACESSO IMEDIATO
            </div>
            <div
              style={{
                fontFamily: 'Editorial, serif',
                fontSize: 44,
                lineHeight: 1.2,
                color: cream,
                marginTop: 8,
              }}
            >
              A sua bússola nas suas mãos.
            </div>
          </div>
        )}
      </div>

      {/* Subtitle / Caption Card (Synced with Voice) */}
      {activeCap && (
        <div
          style={{
            position: 'absolute',
            left: 70,
            right: 70,
            top: 1620,
            padding: '24px 32px',
            background: 'rgba(18, 15, 27, 0.88)',
            border: '1px solid rgba(219, 173, 96, 0.25)',
            borderRadius: 20,
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(12px)',
            textAlign: 'center',
            fontSize: 40,
            lineHeight: 1.3,
            color: cream,
            opacity: capEase,
            transform: `translateY(${(1 - capEase) * 16}px)`,
            zIndex: 30,
          }}
        >
          <span style={{ color: gold, marginRight: 10 }}>“</span>
          {activeCap.text}
          <span style={{ color: gold, marginLeft: 10 }}>”</span>
        </div>
      )}

      {/* Bottom Progress Bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 70,
          left: 75,
          right: 75,
          display: 'flex',
          gap: 10,
          zIndex: 25,
        }}
      >
        {bounds.map((b, i) => (
          <div
            key={b}
            style={{
              height: 4,
              flex: 1,
              borderRadius: 2,
              background: i <= scene ? gold : 'rgba(255, 255, 255, 0.15)',
              transition: 'background 0.3s ease',
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
