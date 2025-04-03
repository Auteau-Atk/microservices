FROM nginx
COPY dashboard /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/

CMD nginx -s reload && nginx -g "daemon off;"