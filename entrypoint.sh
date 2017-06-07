#!/bin/bash

export HOSTNAME=`hostname`
export THIS_CONTAINER_IP=`cat /etc/hosts | grep $HOSTNAME | cut  -f 1`
export DJANGO_LIVE_TEST_SERVER_ADDRESS=$THIS_CONTAINER_IP:9015

export PYTHONPATH=/usr/src/app

exec $*
