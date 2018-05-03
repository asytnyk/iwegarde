#!/bin/sh

DATABASE_PASSWORD=V96vBX5apwvO8s3eu
DATABASE_USER=iwegarde
PKI_PASSWORD=dt7ltvQew97XJt4uQF
VPN_CLIENT_CONNECT_SECRET_KEY=BF9guWTBFEyrUKX2Go6twtQt
SERVERS_QUERY_BY_TAG=4htwt6MCV9oGTOpaTS0

#	--mount type=bind,src=/home/peter/mysql-iwegarde,dst=/var/lib/mysql # For newer dockers...
docker run \
	--name mysql-iwegarde \
	-d \
	--restart unless-stopped \
	-v /mnt/stateful_partition/iwe/mysql-iwegarde:/var/lib/mysql \
	-e MYSQL_RANDOM_ROOT_PASSWORD=yes \
	-e MYSQL_DATABASE=iwegarde \
	-e MYSQL_USER=$DATABASE_USER \
	-e MYSQL_PASSWORD=$DATABASE_PASSWORD \
	mysql/mysql-server:5.7

docker run \
	-d \
	--restart unless-stopped \
	--name iwe_pki \
	-v /mnt/stateful_partition/iwe/pki/pki:/home/iwepki/easy-rsa3/pki \
	-e SECRET_KEY=$PKI_PASSWORD \
	iwe_pki:latest

#	-p 443:5000 \
#	-it --entrypoint /bin/sh \
docker run \
	-d \
	--restart unless-stopped \
	--name iwegarde-server \
	-v /mnt/stateful_partition/iwe/client_vpn_config:/home/iwegarde/iwe_client_vpn_config \
	--link mysql-iwegarde:dbserver \
	--link iwe_pki:pkiserver \
	-e SECRET_KEY=4iCyF4zG3bxwueOFP32u \
	-e MAIL_SERVER=smtp.googlemail.com \
	-e MAIL_PORT=587 \
	-e MAIL_USE_TLS=true \
	-e MAIL_USERNAME=peter.senna.bot \
	-e MAIL_PASSWORD=5qtn1MGljhAYvq \
	-e DATABASE_URL=mysql+pymysql://iwegarde:$DATABASE_PASSWORD@dbserver/iwegarde \
	-e PKI_URL="https://pkiserver:5000/build_client_full" \
	-e PKI_SECRET=$PKI_PASSWORD \
	-e VPN_CLIENT_CONNECT_SECRET_KEY=$VPN_CLIENT_CONNECT_SECRET_KEY \
	-e SERVERS_QUERY_BY_TAG=$SERVERS_QUERY_BY_TAG \
	iwegarde:latest

docker run \
	-d \
	--restart unless-stopped \
	--name phpmyadmin \
	--link mysql-iwegarde:db \
	-e MYSQL_USER=$DATABASE_USER \
	-e PMA_ABSOLUTE_URI="https://beta.iwe.cloud/phpmyadmin_8ojYYBSSzagA8Hk1v/" \
	phpmyadmin/phpmyadmin

#	-e NGINX_PROXY_PASS=http://webserver \
docker run \
	-d \
	--restart unless-stopped \
	-v /mnt/stateful_partition/iwe/static-content:/static-content \
	--name nginx-iwegarde \
	-p 443:5000 \
	-p 80:5080 \
	--link iwegarde-server:webserver \
	--link phpmyadmin:phpmyadmin \
	nginx-iwegarde:latest
