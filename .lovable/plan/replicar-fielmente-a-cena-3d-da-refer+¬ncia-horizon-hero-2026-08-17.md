# Replicar fielmente a cena 3D da referência (Horizon Hero)

O vídeo mostra o efeito original: céu noturno azul-profundo, campo de estrelas branco denso e cintilante, um **sol branco** intenso nascendo atrás da crista da montanha com bloom forte, névoa atmosférica azulada e silhuetas de montanha quase pretas. A cena atual usa um portal/eclipse dourado com anéis, montanhas marrom-douradas e nebulosa laranja — visualmente distante da referência.

## O que muda

1. **Remover o portal de eclipse dourado** (disco escuro, anéis astronômicos, coroa pulsante). Ele será substituído pelo sol.
2. **Sol branco atrás da montanha**: esfera emissiva branca com halo em camadas (núcleo branco puro → borda levemente quente), posicionada no horizonte atrás da crista principal, de modo que só a parte superior apareça. O halo cresce/atenua suavemente conforme o scroll avança.
3. **Estrelas premium**: campo denso em três profundidades, pontos brancos/azulados com brilho suave (sprite radial em vez de quadrado), cintilação individual com fases aleatórias e leve variação de tamanho. Estrelas mais próximas ao sol ficam ofuscadas (fade por proximidade), como na referência.
4. **Atmosfera azul**: nebulosa reescrita como gradiente atmosférico frio (azul-noite → índigo) muito sutil, concentrado no horizonte; fog exponencial azulado no lugar do marrom atual.
5. **Montanhas**: silhuetas quase pretas com leve rim light frio vindo do sol (não dourado), camadas com haze crescente à distância para dar profundidade.
6. **Render**: exposure e bloom recalibrados para o contraste da referência (fundo escuro, sol estourado, estrelas nítidas).
7. **Identidade Astrowake preservada**: o dourado continua nos textos, botões e UI da hero (títulos, indicador "Desça para acessar as instruções da sua alma"), apenas a cena 3D passa a seguir o visual da referência.
8. **Mobile**: mesma cena com contagem de estrelas e resolução de bloom reduzidas, sol reposicionado para caber no enquadramento vertical sem colidir com o texto.

## Detalhes técnicos

Arquivo único: `src/components/ui/horizon-hero-section.tsx`.

- Excluir `createEclipse` e as refs `eclipse`, `eclipseRings`, `eclipseGlow`; remover as chamadas no `animate`.
- `createSun()`: `THREE.Mesh` (esfera) com `MeshBasicMaterial` branco + 2 planos de halo com `ShaderMaterial` aditivo (falloff `pow(1-d, k)`), `depthWrite: false`, `fog: false`; posicionado em `camZ - ~1200`, `y` baixo (no nível da crista), acompanhando a câmera no eixo Z como as estrelas já fazem.
- Estrelas: `PointsMaterial`/shader com `gl_PointCoord` para máscara radial, atributos `aPhase`/`aSize` para twinkle, cores entre `0xffffff` e `0xcfe0ff`.
- Nebulosa: manter o plano, trocar `color1/color2` para tons frios e reduzir frequência do ruído; `scene.fog = FogExp2(0x0a1020, ...)`.
- Montanhas: shader de gradiente com `base ~0x05070c`, `top ~0x11151f` e rim light `0x8fb4ff` de baixa intensidade.
- `toneMappingExposure` e parâmetros do `UnrealBloomPass` ajustados após validação visual com screenshots do preview.

Nenhuma mudança em rotas, copy, formulário, tracking ou backend.
