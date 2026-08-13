FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_BASE_URL=https://enterprise-ai-agent-platform-production.up.railway.app/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

RUN echo "Building frontend with VITE_API_BASE_URL=${VITE_API_BASE_URL}" \
    && npm run build


FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]