FROM nginx:latest

# Установка временной зоны
ENV TZ=Asia/Aqtau
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./nginx.conf /etc/nginx/nginx.conf

COPY ./certs /etc/nginx/certs

RUN chmod -R 755 /staticfiles && \
    chown -R nginx:nginx /staticfiles