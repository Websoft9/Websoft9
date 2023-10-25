#!/bin/bash

set +e 

nginx_proxy(){
    if [ $(stat -c %Y /etc/shadow) -gt $(stat -c %Y /data/nginx/proxy_host/initproxy.conf) ]
    then
        cp /etc/initproxy.conf /data/nginx/proxy_host/
        echo "Update initproxy.conf to Nginx"
    else
        echo "Don't need to update initproxy.conf to Nginx"
    fi
}

nginx_proxy

set -e