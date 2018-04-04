#!/bin/sh

cd ..
docker build -t iwegarde:latest . -f docker/iwegarde/Dockerfile

cd docker/nginx-iwegarde
docker build -t nginx-iwegarde:latest .
