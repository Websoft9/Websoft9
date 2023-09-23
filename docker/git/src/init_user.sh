#!/bin/bash

echo "start  create user shell" >> /tmp/user
set -e

# Confirm gitea is running
count=1
response=""
while [ "$response" != "200" ]; do
  response=$(curl -s -o /dev/null -w "%{http_code}" localhost:3000)
  if [ "$response" = "200" ]; then
    echo "gitea is runing"
    break
  fi
  count=$((count+1))
  if [ $count -gt 10 ]; then
    echo "gitea is not runing"
    break
  fi
done

cred_path="/var/websoft9/credential"
admin_username="websoft9"
admin_email="help@websoft9.com"

if [ -e "$cred_path" ]; then
  echo "File $cred_path exists. Exiting script."
  exit 1
fi

echo "create diretory"
mkdir -p "$(dirname "$cred_path")"

echo "Create admin credential by admin cli"
su -c "
    gitea admin user create --admin --username '$admin_username' --random-password --email '$admin_email' > /tmp/credential
" git

echo "Read credential from tmp"
username=$(grep -o "New user '[^']*" /tmp/credential | sed "s/New user '//")
if [ -z "$username" ]; then
  username="websoft9"
fi
password=$(grep -o "generated random password is '[^']*" /tmp/credential | sed "s/generated random password is '//")

echo "Save to credential"
json="{\"username\":\"$admin_username\",\"password\":\"$password\",\"email\":\"$admin_email\"}"
echo "$json" > "$cred_path"