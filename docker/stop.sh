#!/bin/bash

containers="phpmyadmin nginx-iwegarde iwe_pki iwegarde-server mysql-iwegarde"

for container in $containers; do
	docker stop $container
done

if [[ "$1" == "--rm" ]];then
	for container in $containers; do
		docker rm $container
	done
fi
