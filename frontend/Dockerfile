# Stage 1: Build React Application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package descriptors and lockfile
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code files
COPY . .

# Build application
RUN npm run build

# Stage 2: Serve via Nginx
FROM nginx:alpine

# Copy built static assets from Stage 1 to Nginx default html path
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
