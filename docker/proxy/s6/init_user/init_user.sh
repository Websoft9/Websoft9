#!/bin/bash

echo "Start to change nginxproxymanage users" >> /tmp/userlog

set +e 
username="help@websoft9.com"
password=$(openssl rand -base64 16 | tr -d '/+' | cut -c1-16)
token=""
cred_path="/var/websoft9/credential"

if [ -e "$cred_path" ]; then
  echo "File $cred_path exists. Exiting script."
  exit 0
fi

echo "create diretory"
mkdir -p "$(dirname "$cred_path")"

while [ -z "$token" ]; do
    sleep 5
    login_data=$(curl -X POST -H "Content-Type: application/json" -d '{"identity":"admin@example.com","scope":"user", "secret":"changeme"}' http://localhost:81/api/tokens)
    token=$(echo $login_data | jq -r '.token')
done

echo "Change username(email)" >> /tmp/userlog
while true; do
    response=$(curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d '{"email": "'$username'", "nickname": "admin", "is_disabled": false, "roles": ["admin"]}'  http://localhost:81/api/users/1)
    if [ $? -eq 0 ]; then
        echo "HTTP call successful"
        break
    else
        echo "HTTP call Change username failed, retrying..." >> /tmp/userlog
        sleep 5
    fi
done

echo "Update password" >> /tmp/userlog
while true; do
    response=$(curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d '{"type":"password","current":"changeme","secret":"'$password'"}'  http://localhost:81/api/users/1/auth)
    if [ $? -eq 0 ]; then
        echo "HTTP call successful"
        break
    else
        echo "HTTP call  Update password failed, retrying..." >> /tmp/userlog
        sleep 5
    fi
done

echo "Save to credential"
json="{\"username\":\"$username\",\"password\":\"$password\"}"
echo "$json" > "$cred_path"

set -e

s6-svc -D /etc/s6-overlay/s6-rc.d/init_user