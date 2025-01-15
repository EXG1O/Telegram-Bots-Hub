#!/bin/bash

pip install -U pip
pip install poetry
poetry install

read -p "Enter microservice URL: " SELF_URL
read -p "Enter microservice token: " SELF_TOKEN
read -p "Enter service URL: " SERVICE_URL
read -p "Enter service token: " SERVICE_TOKEN

cat << EOF > .env
DEBUG=True

SELF_URL=$SELF_URL
SELF_TOKEN=$SELF_TOKEN

SERVICE_URL=$SERVICE_URL
SERVICE_TOKEN=$SERVICE_TOKEN
EOF
