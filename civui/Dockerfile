# Stage 1: Build the React app
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY --from=build /app/build .

# Custom nginx config for port 8000
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8000

CMD ["nginx", "-g", "daemon off;"] 