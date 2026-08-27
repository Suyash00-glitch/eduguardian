# ============================================================
# EduGuardian AI - Frontend Dockerfile
# Multi-stage build:
#   Stage 1 (builder): Node.js - installs deps & builds Vite app
#   Stage 2 (runtime): Nginx - serves static files + proxies /api
# ============================================================

# -- Stage 1: Build ------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first
COPY package.json package-lock.json ./

RUN npm ci --silent

# Copy source code
COPY . .

# Build with relative /api proxy URL
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# -- Stage 2: Serve with Nginx -------------------------------
FROM nginx:1.27-alpine AS runtime

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx reverse-proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
