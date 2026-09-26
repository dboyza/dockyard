#!/bin/sh
set -eu
mkdir -p "$DOCKYARD_STORAGE"
chmod 700 "$DOCKYARD_STORAGE"
if [ ! -f "$DOCKYARD_STORAGE/tls.crt" ]; then
  openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj '/CN=dispatch.test' \
    -addext 'subjectAltName=DNS:dispatch.test' \
    -keyout "$DOCKYARD_STORAGE/tls.key" -out "$DOCKYARD_STORAGE/tls.crt" 2>/dev/null
  chmod 600 "$DOCKYARD_STORAGE/tls.key"
fi
kubectl create secret tls dispatch-tls --cert="$DOCKYARD_STORAGE/tls.crt" \
  --key="$DOCKYARD_STORAGE/tls.key" --dry-run=client -o yaml | kubectl apply -f -
