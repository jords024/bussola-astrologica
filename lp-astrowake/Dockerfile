FROM nginx:alpine

LABEL maintainer="Aryaraj Fernandes <aryarajmarketing@gmail.com>"
LABEL version="1.3.2"
LABEL description="Landing Page Astrowake - Hackeando a Realidade"

# Copia configuracao otimizada do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia arquivos estaticos do site (frontend + configuracoes)
COPY . /usr/share/nginx/html/

# Remove arquivos de build e documentacao de dentro do container
RUN rm -f /usr/share/nginx/html/Dockerfile \
          /usr/share/nginx/html/nginx.conf \
          /usr/share/nginx/html/README.md

EXPOSE 80 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O - http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
