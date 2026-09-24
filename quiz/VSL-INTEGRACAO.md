# VSL na última etapa — 24/09/2026

Implementado localmente na versão atual do quiz, com cópia sincronizada em `../../bussola-backend`. Não foi publicado, enviado ao GitHub nem gerada/enviada imagem Docker.

## Fluxo

O percurso ativo agora é `0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 10`: nove telas. Após a carta (7), a avaliação opcional existente leva diretamente à VSL/oferta (10). Voltar da oferta retorna à carta. As telas antigas Portas (8) e Ponte (9) não fazem parte do percurso; seus IDs/HTML permanecem para compatibilidade com o histórico e o painel. O progresso usa os nove passos ativos. Relatórios históricos ainda podem mostrar os rótulos antigos 8 e 9 sem novas visitas — isso não representa abandono nessa versão.

O vídeo de preparação da leitura, na etapa 6, permanece independente. A nova VSL está na etapa 10 e não substitui aquele player.

## Tela final

- Abertura curta conectada à leitura recebida, seguida da VSL vertical.
- Oferta de R$67 ou 12x de R$6,93 imediatamente abaixo do vídeo, com o checkout e rastreamento existentes.
- Detalhes dos materiais recolhidos em seção expansível; garantia e perguntas frequentes continuam disponíveis.
- Reprodução por iniciativa do visitante, com controles nativos, tela cheia, som e legendas já incorporadas ao vídeo.
- Sem bloqueio de compra por tempo assistido. Sem reprodução automática.
- Vídeo carregado apenas ao entrar na última tela. Pausa ao sair da oferta ou ocultar a aba. Erro oferece nova tentativa e acesso direto ao arquivo.

## Arquivos

- `publico/index.html`: layout, navegação e player.
- `publico/video/vsl-web-720p.mp4`: H.264/AAC, 720 × 1280, aproximadamente 38 MB, duração 4min40s, faststart.
- `publico/video/vsl-poster.jpg`: capa extraída do vídeo.
- `testes/check-vsl.cjs`: teste de navegador isolado; não envia dados a APIs externas nem efetua pagamento.
- `testes/vsl-mobile.png` e `testes/vsl-desktop.png`: capturas de conferência.
- Backup anterior: `../../backups-locais/vsl-integracao-2026-09-24/index-antes-vsl.html`.

O master de edição permanece em `../../Vídeo Quizz/Entrega/vsl-completa-v1.mp4`. Não servir o caminho Windows na página: a URL usada é `/estatico/video/vsl-web-720p.mp4`. Ao publicar, incluir a pasta `publico/video`; manter suporte HTTP Range para avançar no vídeo. Não basta enviar somente index.html.

## Verificação

Chrome, viewports 390 × 844 e 1440 × 1000: passagem carta → oferta, reprodução, duração, ausência de download na abertura, retorno e pausa, etapas puladas, recuperação de erro, checkout/UTM e ausência de erros JavaScript. Inspeção visual das capturas. Servidor estático FastAPI retornou HTTP 206, Content-Range correto e Content-Type video/mp4. APIs externas foram bloqueadas no teste; não foi refeita a geração paga de uma carta nem testada uma compra real.

Para repetir, iniciar o servidor isolado na raiz do workspace:

```powershell
& 'bussola-backend/.venv/Scripts/python.exe' 'video-studio/work/vsl/quiz-preview-server.py'
```

Em outro terminal, com Playwright disponível, executar `node bussola-github/quiz/testes/check-vsl.cjs`. O teste aceita `PLAYWRIGHT_PATH` apontando para o pacote instalado e usa Chrome em Program Files. O hook de navegação é injetado somente na resposta interceptada pelo teste, nunca na página entregue.

Identidade reutilizada: tokens âmbar/carvão, tipografia, ticket, detalhes e controles existentes. A busca 21st não pôde consultar o catálogo por falta de autenticação; nenhum componente externo foi instalado.
