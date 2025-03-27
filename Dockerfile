FROM nginx
COPY dashboard/index.html /usr/share/html/index.html
COPY dashboard /usr/share/