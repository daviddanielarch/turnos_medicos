# Builds the Expo app for web and serves it as a static SPA
FROM node:20-alpine AS build
WORKDIR /app

# EXPO_PUBLIC_* variables are inlined into the bundle at build time.
# Railway passes service variables as build args when they are declared here.
ARG EXPO_PUBLIC_API_HOST
ARG EXPO_PUBLIC_AUTH0_WEB_CLIENT_ID
ENV EXPO_PUBLIC_API_HOST=$EXPO_PUBLIC_API_HOST \
    EXPO_PUBLIC_AUTH0_WEB_CLIENT_ID=$EXPO_PUBLIC_AUTH0_WEB_CLIENT_ID \
    CI=1

COPY package.json package-lock.json .npmrc ./
RUN npm ci

COPY . .
RUN npx expo export --platform web --output-dir dist

FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
