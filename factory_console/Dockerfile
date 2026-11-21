# factory_console image: builds the dashboard with Vite, then serves it with nginx. Build from the repository root.
FROM node:22-alpine AS build
WORKDIR /app
COPY factory_console/package.json factory_console/package-lock.json ./
RUN npm ci
COPY factory_console .
# Baked into the bundle at build time. The browser calls factory_core on the host's published port.
ARG VITE_API_MODE=live
ARG VITE_API_BASE_URL=http://localhost:8000
RUN VITE_API_MODE=$VITE_API_MODE VITE_API_BASE_URL=$VITE_API_BASE_URL npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Client side routes (/dashboard, /models/...) fall back to index.html.
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  location / { try_files $uri $uri/ /index.html; }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
