FROM node:22-alpine

WORKDIR /app

# Install native dependencies if needed
RUN apk add --no-cache libc6-compat

# Copy package descriptors
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build production assets (SSR + Client bundles)
RUN npm run build

# Expose app port
EXPOSE 3000

ENV PORT=3000
ENV HOST=0.0.0.0
ENV NODE_ENV=production

# Run standalone compiled Nitro SSR server (fast, lightweight ~40MB RAM)
CMD ["node", ".output/server/index.mjs"]
