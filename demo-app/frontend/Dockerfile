FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy the build output (Your existing line)
COPY --from=build /app/dist /usr/share/nginx/html

# --- ADD THIS NEW LINE ---
# Replace default Nginx config with our custom proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf
# -------------------------

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]