#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
docker compose build experience
mkdir -p offline
docker save -o offline/sathvick-experience-1.0.0-rc1.tar sathvick/openg2p-experience:1.0.0-rc1
(cd offline
  if command -v sha256sum >/dev/null; then
    sha256sum sathvick-experience-1.0.0-rc1.tar
  else
    shasum -a 256 sathvick-experience-1.0.0-rc1.tar
  fi > sathvick-experience-1.0.0-rc1.tar.sha256
)
printf '%s\n' 'Copy this kit and offline/sathvick-experience-1.0.0-rc1.tar to the client.' 'On the client: docker load -i offline/sathvick-experience-1.0.0-rc1.tar, then run the normal installer.' 'Keep .env, connectors.env, generated Kubernetes secrets and database/backups private; transfer them separately only when specifically intended.'
