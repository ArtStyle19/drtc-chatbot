# syntax=docker/dockerfile:1.7
# Frontend image: Angular production build served by an unprivileged nginx.

FROM node:26-trixie-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY . .
RUN npx ng build --configuration production

FROM nginxinc/nginx-unprivileged:1.29-alpine AS runtime
# The image renders /etc/nginx/templates/*.template into conf.d at startup.
ENV BACKEND_UPSTREAM=http://backend:8000 \
    NGINX_RESOLVER=127.0.0.11
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist/drtc-chatbot-web/browser /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD ["wget", "-qO", "/dev/null", "http://127.0.0.1:8080/"]
