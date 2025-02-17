#!/bin/bash

echo "=== Checking Docker containers ==="
docker ps -a

echo -e "\n=== Checking nginx container logs ==="
docker logs nginx_server

echo -e "\n=== Checking nginx container file permissions ==="
docker exec nginx_server ls -la /staticfiles /media

echo -e "\n=== Checking nginx configuration ==="
docker exec nginx_server nginx -T

echo -e "\n=== Checking backend logs ==="
docker logs django_backend

echo -e "\n=== Checking Docker network ==="
docker network ls
docker network inspect app-network
