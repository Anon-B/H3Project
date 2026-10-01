FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# MapLibre GL worker is not emitted as a stable public asset by Vite's package graph.
# Keep stable public worker assets for setWorkerUrl('/maplibre-gl-worker.mjs').
COPY --from=build /app/node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs /usr/share/nginx/html/maplibre-gl-worker.mjs
COPY --from=build /app/node_modules/maplibre-gl/dist/maplibre-gl-shared.mjs /usr/share/nginx/html/maplibre-gl-shared.mjs
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
CMD ["nginx","-g","daemon off;"]