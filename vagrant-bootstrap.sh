#!/usr/bin/env bash

apt-get update
apt-get install -y python python-pip python-dev
cd /vagrant
sudo python setup.py develop
