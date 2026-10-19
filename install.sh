#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v docker >/dev/null || { echo "Install Docker Engine and Compose v2.24+ first."; exit 1; }
docker info >/dev/null
export SETUP_UID="$(id -u)" SETUP_GID="$(id -g)"
if ! docker image inspect sathvick/openg2p-experience:1.0.0-rc1 >/dev/null 2>&1; then
  if [[ -f offline/sathvick-experience-1.0.0-rc1.tar ]]; then
    (cd offline
      if command -v sha256sum >/dev/null; then
        sha256sum -c sathvick-experience-1.0.0-rc1.tar.sha256
      else
        shasum -a 256 -c sathvick-experience-1.0.0-rc1.tar.sha256
      fi
    )
    docker load -i offline/sathvick-experience-1.0.0-rc1.tar
  else
    docker compose build experience
  fi
fi
if [[ ! -f .env ]]; then
  docker compose run --rm --no-deps setup
fi
docker compose up -d --wait --wait-timeout 180 experience collector
printf '%s\n' 'Local entry: http://127.0.0.1:18110/experience/' 'For remote access configure an HTTPS reverse proxy as described in docs/CLIENT-INTEGRATION.md.'
