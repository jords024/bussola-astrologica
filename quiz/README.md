# Bússola Astrológica: quiz e leitura personalizada

Aplicação atual do quiz em 11 etapas, com mandala, carta personalizada, carrossel das 12 casas e oferta das aulas por R$67 à vista. O FastAPI serve o quiz na raiz `/`, os arquivos em `/estatico` e a API na mesma origem.

## Executar com Python 3.11

A partir de `quiz/`:

```sh
python -m venv .venv
# Ative o ambiente virtual conforme seu sistema.
pip install -r requirements.txt
# Copie .env.example para .env e preencha os valores privados.
uvicorn main:app --host 127.0.0.1 --port 8765
```

Configure `OPENAI_API_KEY`, `MODELO_LEITURA` e uma senha forte em `PAINEL_SENHA`. Configure `DIR_DADOS` para uma pasta gravável fora do OneDrive (por exemplo C:/bussola-dados no Windows). Nenhuma chave ou dado de usuário é versionado.

Abra http://127.0.0.1:8765. Para testar sem contar no funil, use `?t=1`.

## Docker

Depois de criar `quiz/.env`, execute na raiz do repositório:

```sh
docker compose -f docker/docker-compose-quiz.yml up -d --build
```

O volume `quiz_dados` guarda leituras, eventos e cache. A porta é local por padrão. Para publicar, configure seu proxy HTTPS para este serviço; o frontend React antigo não executa Python. Os arquivos Compose anteriores continuam destinados à aplicação anterior.

## Componentes e Funcionalidades

- `publico/`: quiz dinâmico em 11 etapas, mandala cósmica e carrossel interativo das 12 casas.
- `api/` e `servicos/`:
  - Cálculo astrológico com Swiss Ephemeris / Kerykeion.
  - Geração de carta astrológica personalizada via IA com fallback para carta de reserva.
  - Sincronização em tempo real via WebSockets (`/painel/ws`).
  - Monitoramento de presença e tela atual de visitantes ativos em tempo real (`rastreador_presenca.py`).
  - Gestão de status de compra (`comprou: true/false`), agrupamento de envios repetidos e exclusão segura.
- `prompts/carta.txt`: instruções contextuais para a IA.
- `/painel`: painel administrativo protegido com 5 abas (Funil, Leituras, Formulário & Horário, Áreas & Casas, Saúde do Agente):
  - **Filtros rápidos:** Todas as leituras, Só quem foi pro checkout, 🟢 Ao vivo agora, 💰 Só quem comprou.
  - **Mão de arrasto horizontal (`drag-to-scroll`):** navegação fluida com o botão esquerdo do mouse exclusiva na tabela de Leituras.
  - **Popup Modal Centralizado:** confirmação elegante ao marcar e desmarcar compra de contatos (sem fechar ao clicar fora).
  - **Acordeão de Múltiplos Envios:** visualização compactada de envios repetidos (`▶ 2x`, `▶ 3x`).
- `/api/saude`: diagnóstico de dependências, latência e configuração.
- `testes/`: suíte de 75 testes automatizados cobrindo cálculo, leitura, persistência, websocket e painel.

## Testes Unitários

Configure as variáveis de teste e execute:

```sh
python -m pytest -o pythonpath=. testes
```

## Limites atuais

O checkout é demonstrativo. A publicação no GitHub não conecta credenciais privadas. Sem horário confiável, o quiz não inventa uma casa aberta. Falhas do modelo LLM acionam a carta de reserva calculada localmente pelo servidor.

