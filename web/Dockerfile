# ---- deps: shared base with installed node_modules ----
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

# ---- build: production bundle (dist/) ----
FROM deps AS build
COPY . .
RUN npm run build

# ---- prod: serve dist/ via nginx ----
# Build/run explicitly with: docker build --target prod -t peopledesk-web:prod ./web
FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# ---- dev: default target, used by docker-compose.yml for local dev ----
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
