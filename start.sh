#!/bin/sh

DATABASE_PASSWORD=V96vBX5apwvO8s3eu

docker run \
	--name mysql-iwegarde \
	-d --rm \
	-v /home/peter/mysql-iwegarde:/var/lib/mysql
#	--mount type=bind,src=/home/peter/mysql-iwegarde,dst=/var/lib/mysql # For newer dockers...
	-e MYSQL_RANDOM_ROOT_PASSWORD=yes \
	-e MYSQL_DATABASE=iwegarde \
	-e MYSQL_USER=iwegarde \
	-e MYSQL_PASSWORD=$DATABASE_PASSWORD \
	mysql/mysql-server:5.7

sleep 15

docker run \
	-d -rm \
	--name iwegarde-server \
	-p 443:443 \
	-e SECRET_KEY=4iCyF4zG3bxwueOFP32u \
	-e MAIL_SERVER=smtp.googlemail.com \
	-e MAIL_PORT=587 \
	-e MAIL_USE_TLS=true \
	-e MAIL_USERNAME=peter.senna.bot \
	-e MAIL_PASSWORD=5qtn1MGljhAYvq \
	--link mysql:dbserver \
	-e DATABASE_URL=mysql+pymysql://iwegarde:$DATABASE_PASSWORD@dbserver/iwegarde \
	iwegarde:latest
