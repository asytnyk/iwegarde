#!/bin/sh

DATABASE_PASSWORD=V96vBX5apwvO8s3eu
PKI_PASSWORD=dt7ltvQew97XJt4uQF

docker run \
	--name mysql-iwegarde \
	-d \
	--restart unless-stopped \
	-v /mnt/stateful_partition/iwe/mysql-iwegarde:/var/lib/mysql \
	-p 3306:3306 \
	-e MYSQL_RANDOM_ROOT_PASSWORD=yes \
	-e MYSQL_DATABASE=iwegarde \
	-e MYSQL_USER=iwegarde \
	-e MYSQL_PASSWORD=$DATABASE_PASSWORD \
	mysql/mysql-server:5.7

docker run \
	-d \
	--restart unless-stopped \
	--name iwe_pki \
	-v /mnt/stateful_partition/iwe/pki/pki:/home/iwepki/easy-rsa3/pki \
	-p 4000:5000 \
	-e SECRET_KEY=$PKI_PASSWORD \
	iwe_pki:latest

echo mount /mnt/stateful_partition/iwe/client_vpn_config/ $HOME/iwe_client_vpn_config/ ...
sudo umount $HOME/iwe_client_vpn_config/
sudo mount -o bind /mnt/stateful_partition/iwe/client_vpn_config/ $HOME/iwe_client_vpn_config/

echo "export DATABASE_URL=mysql+pymysql://iwegarde:$DATABASE_PASSWORD@localhost/iwegarde"
echo "export PKI_SECRET=$PKI_PASSWORD"

echo "docker run --name myadmin -d --link mysql-iwegarde:db -p 8080:80 phpmyadmin/phpmyadmin"
echo "Then use iwegarde / $DATABASE_PASSWORD on the web interface"
