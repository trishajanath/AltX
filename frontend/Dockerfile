# --- Stage 1: Build the React application ---
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Stage 2: Serve the built files with Nginx ---
FROM nginx:stable-alpine

# Copy the final, built files from the 'builder' stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Tell Docker that the container listens on port 80
EXPOSE 80

# The command to start the Nginx server
CMD ["nginx", "-g", "daemon off;"]