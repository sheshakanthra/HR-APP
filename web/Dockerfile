FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Dev server for local compose. For production, build + serve the static dist.
CMD ["npm", "run", "dev"]
