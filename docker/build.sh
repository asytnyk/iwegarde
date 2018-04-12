#!/bin/sh

DIR=$HOME/dev

cd $DIR/iwegarde
git pull
if [[ "$?" != "0" ]];then
	echo ARGH!
	exit 1
fi
docker build -t iwegarde:latest . -f docker/iwegarde/Dockerfile

cd $DIR/iwegarde/docker/nginx-iwegarde
docker build -t nginx-iwegarde:latest .

cd $DIR/iwe_pki
git pull
if [[ "$?" != "0" ]];then
	echo ARGH!
	exit 1
fi
docker build -t iwe_pki:latest . -f docker/Dockerfile
