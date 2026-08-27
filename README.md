# 🌌 Bússola Astrológica & Astrowake

Plataforma web e landing pages de alta conversão do astrólogo **Crassus Gobbi**, desenvolvida com **TanStack Start (SSR)**, **React 19**, **Tailwind CSS v4** e **PostgreSQL**.

---

## 🧭 Visão Geral do Projeto

A **Bússola Astrológica** é uma experiência web imersiva voltada para apresentação e venda do método de interpretação de trânsitos astrológicos e ciclos das 12 casas (as 12 portas da vida).

### ✨ Principais Recursos:
- **Página de Vendas (`/bussola`):** Apresentação das 12 portas, animações suaves com GSAP e Framer Motion, ilustrações cósmicas em alta definição e checkout integrado Hotmart.
- **Página de Captura (`/`):** Captação de leads para encontros ao vivo, com validação de dados e geolocalização por IP.
- **Página de Agradecimento (`/obrigado`):** Redirecionamento automático para grupos VIP de WhatsApp e rastreamento de conversão.
- **Painel Administrativo (`/admin`):** Dashboard protegido para visualização, filtragem e exportação em CSV de todos os leads cadastrados.
- **Autenticação Segura (`/auth`):** Login com hash de senha (`bcryptjs`), tokens de sessão JWT (`jose`), cookies `HttpOnly` e controle de permissões por perfil (`user_roles`).
- **Suporte e Contato:** Botão flutuante direto para o canal oficial de atendimento via WhatsApp.
- **Páginas Legais:** Políticas de Privacidade (`/politicas-de-privacidade`) e Termos de Uso (`/termos-de-uso`) em conformidade com a LGPD.

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

### Opção 1: Via Docker (Recomendado)

Suba a aplicação e o banco de dados PostgreSQL com um único comando:

```bash
# Na raiz do projeto:
npm run docker:local
```

Ou diretamente pelo Docker Compose:
```bash
docker compose -f docker/docker-compose-local.yml up -d --build
```

Acesse no navegador:
- **Aplicação Web:** [http://localhost:3000](http://localhost:3000)
- **Página de Vendas da Bússola:** [http://localhost:3000/bussola](http://localhost:3000/bussola)
- **Painel Admin:** [http://localhost:3000/admin](http://localhost:3000/admin)
- **Banco PostgreSQL:** `localhost:5432` (`user: postgres`, `password: postgres`, `db: bussola_astrologica`)

Para parar os contêineres:
```bash
npm run docker:down
```

---

### Opção 2: Desenvolvimento Local (Node.js)

Se preferir rodar apenas o servidor de desenvolvimento com hot-reload:

```bash
# 1. Instale as dependências (caso ainda não tenha feito)
cd frontend
npm install

# 2. Inicie o servidor Vite de desenvolvimento
npm run dev
```

Ou execute a partir da raiz do repositório:
```bash
npm run dev
```

---

## 🧪 Testes Unitários

O projeto possui cobertura completa de testes unitários para componentes visuais, rotas, autenticação, hashing de senhas e validação de leads:

```bash
# Rodar todos os testes unitários da suíte:
npm run test
```

Para rodar em modo contínuo (*watch*):
```bash
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
