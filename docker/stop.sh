#!/bin/bash

containers="phpmyadmin nginx_iwegarde iwe_pki iwegarde_server mysql_iwegarde"

for container in $containers; do
	docker stop $container
done

if [[ "$1" == "--rm" ]];then
	for container in $containers; do
		docker rm $container
	done
fi
