#!/bin/bash

# PRODUCTION
git reset --hard
git checkout master
git pull origin master
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d