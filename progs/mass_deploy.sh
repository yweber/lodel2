#!/bin/bash

conffile="[@]LODEL2_CONFDIR[@]/mass_deploy.cfg"

badconf() {
	echo -e "Either the file $conffile cannot be found or it didn't contains expected informations\n\nThe conffile is expected to define MONGODB_ADMIN_USER and MONGODB_ADMIN_PASSWORD variables" >&2
	exit 1
}

mongodb_connfail() {
	echo -e "Credential from $conffile seems to be incorrect. Unable to connect on admin db" >&2
	exit 2
}

test -f $conffile || badconf
#Load conffile
. $conffile
test -z "$MONGODB_ADMIN_USER" && badconf
test -z "$MONGODB_ADMIN_PASSWORD" && badconf


#Check for the presence of /usr/share/dict/words to generate random names
if [ -f '/usr/share/dict/words' ]
then
	random_name=$(sed -nE 's/^([A-Za-z0-9]+)$/\1/p' /usr/share/dict/words |shuf|head -n1)
else
	random_name=$RANDOM
fi

#Check for the presence of mongo and its conf
if hash mongo 2>/dev/null
then
	echo "Mongo found"
else
	echo "You need mongo on this host to do a mass deploy !" >&2
	exit
fi

if [ -f "/etc/mongodb.conf" ]
then
	if cat /etc/mongodb.conf  |grep -E '^ *auth *= *true *$' >/dev/null
	then
		echo "OK, auth enabled"
	else
		echo "WARNING : auth seems disabled on mongod !" >&2
	fi
else
	echo "/etc/mongodb.conf not found. Unable to check if auth is on"
fi

echo "exit" | mongo $MONGODB_HOST --quiet -u "$MONGODB_ADMIN_USER" -p "$MONGODB_ADMIN_PASSWORD" admin &>/dev/null || mongodb_connfail

#Check for the presence of pwgen for password generation
if hash pwgen 2>/dev/null
then
	echo "Using pwgen to generate passwords"
	rnd_pass_cmd='pwgen 25 1'
else
	echo "pwgen not found !!! Using \$RANDOM to generate passwords"
	rnd_pass_cmd='$RANDOM'
fi

ninstance=$1
instance=${ninstance:=50}

echo -n "You are going to create $ninstance lodel2 instances. Are you sure ? Y/n "
read rep
if [ "$rep" = "Y" ]
then
	echo "GO ! (you have 3 secs to cancel)"
	sleep 3
else
	echo "You didn't answer 'Y' (yeah, case matter =P), exiting"
	exit
fi

echo "Creating instances"
for i in $(seq $ninstance)
do
	iname="${random_name}_$(printf "%05d" $i)"
	slim -n $iname -c
	slim -n $iname -s --interface web
	slim -n $iname -m

	#Mongo db database creation
	dbname="${MONGODB_DB_PREFIX}_$iname"
	dbuser="lodel2_$i"
	dbpass=$($rnd_pass_cmd)
	mongo $MONGODB_HOST -u "$MONGODB_ADMIN_USER" -p "$MONGODB_ADMIN_PASSWORD" admin <<EOF
use $dbname
db.addUser('$dbname', '$dbpass', ['readWrite', '$dbname'])
exit
EOF
	#Append created db to instance conf
	slim -n $iname -s --datasource_connectors mongodb --host localhost --user $dbuser --password $dbpass --db_name $dbname

done
