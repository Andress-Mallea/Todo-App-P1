#!/usr/bin/env bash
set -Eeuo pipefail

# Preparacion inicial de Ubuntu en EC2 para La Carta 2.0.
# Ejecutar: sudo bash preparar_ec2.sh
if [[ $EUID -ne 0 ]]; then
  echo 'Ejecuta este script con sudo: sudo bash preparar_ec2.sh' >&2
  exit 1
fi

. /etc/os-release
if [[ "${ID:-}" != 'ubuntu' ]]; then
  echo 'Este script solo admite Ubuntu.' >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

cat > /etc/apt/sources.list.d/docker.sources <<DOCKER_REPO
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
DOCKER_REPO

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

# Para no dar acceso equivalente a root al usuario SSH, se utiliza sudo docker.
# No se modifica el firewall, puertos AWS, .env, repositorio ni PostgreSQL.

echo '=== Preparacion completada ==='
git --version
docker --version
docker compose version
systemctl is-active docker

echo 'Siguiente paso: configurar el repositorio y el archivo .env, y despues desplegar.'
