FROM nginx
COPY dashboard/index.html /usr/share/nginx.html
COPY dashboard /usr/share/