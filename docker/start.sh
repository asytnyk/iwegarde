#!/bin/sh

DATABASE_PASSWORD=V96vBX5apwvO8s3eu
DATABASE_USER=iwegarde
IWEGARDE_SECRET=4iCyF4zG3bxwueOFP32u
PKI_PASSWORD=dt7ltvQew97XJt4uQF
VPN_CLIENT_CONNECT_SECRET_KEY=BF9guWTBFEyrUKX2Go6twtQt
SERVERS_QUERY_BY_TAG=4htwt6MCV9oGTOpaTS0

FULL_LIST='mysql_iwegarde iwe_pki iwegarde_server phpmyadmin nginx_iwegarde'

# This is for development only
function iwegarde_exports {
	echo
	echo "export SECRET_KEY=$IWEGARDE_SECRET;export DATABASE_URL=mysql+pymysql://iwegarde:$DATABASE_PASSWORD@localhost/iwegarde"
	echo
}

function mysql_iwegarde {

	if $1;then
		local='-p 3306:3306'
	else
		local=''
	fi

#		--mount type=bind,src=/home/peter/mysql-iwegarde,dst=/var/lib/mysql # For newer dockers...
	docker run \
		--name mysql_iwegarde \
		-d \
		--restart unless-stopped \
		-v /mnt/stateful_partition/iwe/mysql-iwegarde:/var/lib/mysql \
		-e MYSQL_RANDOM_ROOT_PASSWORD=yes \
		-e MYSQL_DATABASE=iwegarde \
		-e MYSQL_USER=$DATABASE_USER \
		-e MYSQL_PASSWORD=$DATABASE_PASSWORD \
		$local \
		mysql/mysql-server:5.7
}

function iwe_pki {
	docker run \
		-d \
		--restart unless-stopped \
		--name iwe_pki \
		-v /mnt/stateful_partition/iwe/pki/pki:/home/iwepki/easy-rsa3/pki \
		-e SECRET_KEY=$PKI_PASSWORD \
		iwe_pki:latest
}

function iwegarde_server {
#		-p 443:5000 \
#		-it --entrypoint /bin/sh \
	docker run \
		-d \
		--restart unless-stopped \
		--name iwegarde_server \
		-v /mnt/stateful_partition/iwe/client_vpn_config:/home/iwegarde/iwe_client_vpn_config \
		--link mysql_iwegarde:dbserver \
		--link iwe_pki:pkiserver \
		-e SECRET_KEY=$IWEGARDE_SECRET \
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
}

function phpmyadmin {
docker run \
	-d \
	--restart unless-stopped \
	--name phpmyadmin \
	--link mysql_iwegarde:db \
	-e MYSQL_USER=$DATABASE_USER \
	-e PMA_ABSOLUTE_URI="https://beta.iwe.cloud/phpmyadmin_8ojYYBSSzagA8Hk1v/" \
	phpmyadmin/phpmyadmin

}

function nginx_iwegarde {
#	-e NGINX_PROXY_PASS=http://webserver \
docker run \
	-d \
	--restart unless-stopped \
	-v /mnt/stateful_partition/iwe/static-content:/static-content \
	-v /mnt/stateful_partition/iwe/letsencrypt:/letsencrypt \
	--name nginx_iwegarde \
	-p 443:5000 \
	-p 80:5080 \
	--link iwegarde_server:webserver \
	--link phpmyadmin:phpmyadmin \
	nginx-iwegarde:latest
}
if [[ ! -z "$1" ]];then
	echo "Starting only $@ instead of ($FULL_LIST)"
	for func in $@;do
		$func local
	done
	iwegarde_exports
	exit
fi

for func in $FULL_LIST; do
	$func
done
