#!/bin/sh
# Enables TLS when TLS_CERT_B64 and TLS_KEY_B64 hold a base64 PEM certificate and key
# (prod: the Cloudflare Origin CA certificate, set in Openship). Without them nginx
# serves plain HTTP only, as in local compose.
set -eu
mkdir -p /etc/nginx/tls.d
if [ -n "${TLS_CERT_B64:-}" ] && [ -n "${TLS_KEY_B64:-}" ]; then
  umask 077
  echo "$TLS_CERT_B64" | base64 -d > /etc/nginx/tls.d/cert.pem
  echo "$TLS_KEY_B64" | base64 -d > /etc/nginx/tls.d/key.pem
  cat > /etc/nginx/tls.d/listen.conf <<'CONF'
listen 443 ssl;
listen [::]:443 ssl;
ssl_certificate /etc/nginx/tls.d/cert.pem;
ssl_certificate_key /etc/nginx/tls.d/key.pem;
ssl_protocols TLSv1.2 TLSv1.3;
CONF
  echo "tls.sh: TLS on 443"
else
  : > /etc/nginx/tls.d/listen.conf
  echo "tls.sh: no certificate, HTTP only"
fi
