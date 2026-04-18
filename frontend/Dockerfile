# Stage 1: Build the Vite bundle
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY tsconfig.json tsconfig.node.json vite.config.ts tailwind.config.js postcss.config.js index.html ./
COPY src ./src

# Build-time env (optional) — passed via docker-compose `args`
ARG VITE_REGISTER_ENABLED=false
ARG VITE_AUTH_DISABLED=false
ENV VITE_REGISTER_ENABLED=$VITE_REGISTER_ENABLED
ENV VITE_AUTH_DISABLED=$VITE_AUTH_DISABLED

RUN npm run build

# Stage 2: Serve static bundle + reverse-proxy /api to the backend
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost/ > /dev/null || exit 1
