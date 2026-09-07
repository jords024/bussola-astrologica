# 🌌 Bússola Astrológica: Quiz, Leitura Personalizada & Painel de Leads

Plataforma astrológica completa desenvolvida para o astrólogo **Crassus Gobbi**, integrando quiz interativo com leitura personalizada via IA, cálculo de precisão astrológica, painel administrativo com atualização em tempo real via WebSockets e landing pages de alta conversão.

---

## 🧭 Visão Geral do Ecossistema

O ecossistema da **Bússola Astrológica** é composto por duas aplicações integradas:

1. **Aplicação do Quiz & Painel de Leads (`quiz/`)**:
   - Desenvolvida em **Python 3.10+ / FastAPI / WebSockets**, servindo na raiz `/` o quiz em 11 etapas, cálculo astrológico de casas e trânsitos (Swiss Ephemeris / Kerykeion), geração de carta personalizada por IA, acompanhamento em tempo real e painel administrativo protegido (`/painel`).
2. **Landing Pages & Vendas (`frontend/`)**:
   - Desenvolvida com **TanStack Start (SSR)**, **React 19**, **Tailwind CSS v4** e **PostgreSQL**, com apresentação das 12 casas (as 12 portas da vida), animações e checkout Hotmart.

---

## ✨ Recursos do Quiz e Leitura Personalizada (`quiz/`)

- **Quiz Dinâmico em 11 Etapas:** Interface responsiva guiando o visitante desde a identificação até a escolha de áreas da vida e preenchimento de nascimento (data, hora e cidade com geolocalização).
- **Cálculo Astrológico de Precisão:** Cálculo real de casas astrológicas e posicionamentos planetários.
- **Carta Personalizada por IA:** Análise profunda e personalizada com fallback automático para carta de reserva.
- **Mandala Interativa & Oferta:** Apresentação visual da mandala astrológica e transição para a oferta das aulas.

---

## ⚡ Painel Administrativo em Tempo Real (`/painel`)

O painel administrativo (`/painel`, protegido por autenticação HTTP Basic) conta com:

- **Sincronização em Tempo Real via WebSocket (`/painel/ws`):** Atualizações instantâneas de novos leads, avanço de etapas no funil, cliques no checkout e status de compra sem recarregar a página (F5).
- **Filtro de Visitantes Ao Vivo (`🟢 Ao vivo agora`):** Monitoramento instantâneo de quem está com o quiz aberto nos últimos 90s e qual tela está visualizando.
- **Marcação de Compra com Confirmação Segura:** Botão interativo (`💰 Comprou` / `✅ Comprou`) com popup modal centralizado e elegante (com proteção contra fechamento ao clicar fora) e filtro rápido `"💰 Só quem comprou"`.
- **Agrupamento de Múltiplos Envios:** Detecção automática de contatos repetidos com acordeão expansível (`▶ 2x`, `▶ 3x`) e opção de exclusão individual ou coletiva.
- **Arrasto Horizontal com o Mouse (`drag-to-scroll`):** Navegação horizontal rápida com o botão esquerdo do mouse na tabela de Leituras.
- **5 Abas de Controle:** Funil por Tela, Leituras, Formulário & Horário, Áreas & Casas e Saúde do Agente.

---

## 📁 Estrutura de Diretórios

O projeto é organizado de forma modular e limpa:

```plaintext
Landing Page - Bussula Astrologica/
├── docker/                             # Arquivos de Infraestrutura e Docker
│   ├── Dockerfile                      # Configuração da imagem de produção SSR
│   ├── .dockerignore                   # Arquivos ignorados no build do contêiner
│   ├── docker-compose-local.yml        # Orquestração local (App + PostgreSQL)
│   ├── docker-compose-producao.yml     # Orquestração para Docker Swarm & Traefik
│   └── init.sql                        # Script de criação das tabelas do banco de dados
│
├── frontend/                           # Código-fonte da Aplicação Web
│   ├── public/                         # Arquivos estáticos (fontes, assets, favicon)
│   ├── src/
│   │   ├── assets/                     # Imagens e ilustrações em WebP/PNG
│   │   ├── components/                 # Componentes React (Bússola, UI, Rodapé, etc.)
│   │   ├── lib/                        # Funções de servidor, autenticação, DB e tracking
│   │   ├── routes/                     # Rotas e páginas (TanStack Router)
│   │   ├── test/                       # Suíte de testes unitários (Vitest)
│   │   ├── server.ts                   # Ponto de entrada do servidor SSR Nitro
│   │   └── styles.css                  # Estilos globais e temas Tailwind v4
│   ├── scripts/                        # Scripts de download e otimização de imagens
│   ├── package.json                    # Dependências e scripts do frontend
│   ├── tsconfig.json                   # Configuração TypeScript
│   ├── vite.config.ts                  # Configuração do Vite e TanStack Start
│   └── vitest.config.ts                # Configuração do executor de testes
│
├── package.json                        # Scripts utilitários de delegação na raiz
└── README.md                           # Documentação do projeto
```

---

## 🛠️ Tecnologias Utilizadas

- **Frontend & SSR:** [TanStack Start](https://tanstack.com/start), [React 19](https://react.dev/), [Vite](https://vite.dev/), [Nitro Server](https://nitro.unjs.io/)
- **Estilização & Animações:** [Tailwind CSS v4](https://tailwindcss.com/), [GSAP (ScrollTrigger)](https://gsap.com/), [Framer Motion](https://www.framer.com/motion/)
- **Componentes UI & Ícones:** [Radix UI](https://www.radix-ui.com/), [Lucide React](https://lucide.dev/)
- **Banco de Dados & Autenticação:** [PostgreSQL 16](https://www.postgresql.org/), `pg` (node-postgres), `bcryptjs`, `jose` (JWT)
- **Infraestrutura & Containers:** [Docker](https://www.docker.com/), Docker Compose, Traefik
- **Testes Unitários:** [Vitest](https://vitest.dev/), [@testing-library/react](https://testing-library.com/)

---

## 🚀 Como Executar o Projeto

### 1. Executando o Quiz e Painel de Leads (Python / Docker)

#### Opção A: Via Docker Compose (Recomendado)
Execute na raiz do projeto:
```bash
docker compose -f docker/docker-compose-quiz.yml up -d --build
```
Acesse:
- **Quiz Completo:** [http://localhost:8765](http://localhost:8765)
- **Painel Administrativo:** [http://localhost:8765/painel](http://localhost:8765/painel)

#### Opção B: Localmente com Python
```bash
cd quiz
python -m venv .venv

# Ative o ambiente virtual:
# Windows: .\.venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8765 --reload
```

---

### 2. Executando a Landing Page (Frontend SSR / Node.js)

```bash
cd frontend
npm install
npm run dev
```
Acesse: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Testes Unitários

O projeto conta com cobertura completa e testes automatizados em ambas as aplicações:

### Backend (Python / Pytest)
```bash
cd quiz
.\.venv\Scripts\pytest -o pythonpath=. testes
# 75 testes cobrindo integração, painel, tempo real, websocket, webhooks e persistência
```

### Frontend (Vitest)
```bash
npm test -- --run
# 68 testes cobrindo componentes, validações, autenticação, modais e rotas
```
cd frontend
npm run test -- --watch
```

---

## 🗄️ Estrutura do Banco de Dados

O banco de dados é inicializado automaticamente pelo script [`docker/init.sql`](file:///c:/Users/aryar/.gemini/antigravity/scratch/Projetos%20Serios/Landing%20Page%20-%20Bussula%20Astrologica/docker/init.sql):

- **`users`:** Armazena e-mail, hash seguro da senha e data de criação.
- **`user_roles`:** Perfis de acesso (`admin`, `user`).
- **`leads`:** Registros completos de leads capturados (Nome, E-mail, WhatsApp, Origem, IP, Cidade, Região, País, Timezone e parâmetros UTM).

---

## 📦 Deploy em Produção

O arquivo [`docker/docker-compose-producao.yml`](file:///c:/Users/aryar/.gemini/antigravity/scratch/Projetos%20Serios/Landing%20Page%20-%20Bussula%20Astrologica/docker/docker-compose-producao.yml) contém o manifesto de implantação para **Docker Swarm** com roteamento automático via **Traefik**, certificado SSL Let's Encrypt e compressão gzip/brotli para o domínio oficial `crassusastrologo.com.br`.
