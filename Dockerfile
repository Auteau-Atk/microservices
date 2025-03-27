FROM nginx

RUN rm -rf /usr/share/nginx/html/*

COPY dashboard /usr/share/nginx/html
