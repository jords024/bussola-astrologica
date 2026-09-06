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

## Componentes

- `publico/`: quiz, mandala exibida como imagem e carrossel interativo.
- `api/` e `servicos/`: cálculo Kerykeion, geração da carta, auditoria, eventos e painel.
- `prompts/carta.txt`: instruções da carta personalizada.
- `/painel`: painel protegido pela senha configurada.
- `/api/saude`: diagnóstico de dependências e configuração.
- `testes/`: testes de cálculo, leitura e eventos.

Configure uma senha fictícia em `PAINEL_SENHA` para o teste de autenticação do painel.

```sh
python -m unittest discover -s testes -p "test_*.py" -q
```

## Limites atuais

O checkout ainda é demonstrativo. O PDF mencionado na oferta ainda não tem geração e entrega implementadas. A publicação no GitHub não conecta pagamentos, credenciais nem hospedagem. Sem horário confiável, o quiz não inventa uma casa aberta. Falhas do modelo podem usar a carta de reserva calculada pelo servidor.
