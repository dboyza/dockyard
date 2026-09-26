#!/bin/sh
set -eu
mkdir -p backups
chmod 700 backups
DB_POD=$(kubectl get pods -l app=db -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$DB_POD" -- pg_dump -U dispatch -d dispatch --no-owner --no-acl > backups/dispatch.sql
chmod 600 backups/dispatch.sql
python render.py restore.yaml | kubectl apply -f -
kubectl rollout status statefulset/db-restore --timeout=120s
kubectl exec -i db-restore-0 -- psql -U dispatch -d dispatch -v ON_ERROR_STOP=1 -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
kubectl exec -i db-restore-0 -- psql -U dispatch -d dispatch -v ON_ERROR_STOP=1 < backups/dispatch.sql
