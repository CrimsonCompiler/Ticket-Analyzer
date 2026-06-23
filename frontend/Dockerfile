# Frontend image for Ticket Analyzer.
# - Builds the React/Vite production bundle.
# - Serves it with Nginx on port 3000.
# - Nginx reverse-proxies /api to the backend service on the internal
#   Docker network, so CORS is not required.
# - BACKEND_HOST and BACKEND_PORT are templated into nginx.conf at
#   container start so the upstream can change without rebuilding.

FROM node:20-alpine AS build

WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY . .
# VITE_API_BASE_URL is set so the client calls /api on the same origin.
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine
# envsubst is in busybox-extras on alpine 1.27; install explicitly to be safe.
RUN apk add --no-cache gettext

# Copy the template, then a tiny entrypoint that substitutes the
# backend address and starts nginx in the foreground.
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Default values used only if the orchestrator does not pass them.
# docker-compose passes the real ones from .env.
ENV BACKEND_HOST=backend \
    BACKEND_PORT=8000

COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
