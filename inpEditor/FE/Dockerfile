FROM node:22-alpine AS build

WORKDIR /app

COPY front/package.json front/yarn.lock front/.yarnrc.yml ./
RUN corepack enable && yarn install --immutable

COPY front/ ./

ARG VITE_PROFILE=dev
ENV VITE_PROFILE=$VITE_PROFILE

RUN yarn build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 30090
