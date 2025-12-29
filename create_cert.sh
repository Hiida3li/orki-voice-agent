#!/bin/bash
# Create self-signed certificate for HTTPS
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
echo "Certificate created: cert.pem and key.pem"