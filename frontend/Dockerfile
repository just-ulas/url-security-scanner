FROM node:22-alpine AS build
WORKDIR /src
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm typecheck && pnpm build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /src/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD wget -qO- http://127.0.0.1/healthz >/dev/null || exit 1
