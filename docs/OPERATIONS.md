# Backups, upgrades, offline delivery and Kubernetes

## Back up

Windows Docker Desktop: double-click `Backup.cmd`; WSL2 Ubuntu-22.04: `Backup-WSL.cmd`. Linux: `bash backup.sh`. The kit uses SQLite's online backup API and verifies `PRAGMA integrity_check`. Backups are under `backups/` with SHA256 files. The tool does not back up OpenG2P databases.

Separately retain the release files, `config/deployment.json`, `.env`, `config/connectors.env`, any CA certificates and the installed container image. Secrets and backups must be kept private, outside public source control and release ZIPs. The SQLite backup includes local password hashes, knowledge content/history and usage data. Backups are self-contained SQLite snapshots in DELETE journal mode. The helper assigns files to app UID 10001 with mode 0600 on Linux. An approved administrator may be needed to transfer them. Windows-mounted folders require appropriate Windows ACLs; Linux chmod alone is insufficient.

## Restore only this kit

Restoring replaces the kit's knowledge, accounts and analytics state with a backup. Changes after that backup are not retained. Choose the intended backup and first take a current backup. Stop both kit services before restoring; the tools do not stop or restore existing OpenG2P services.

Linux example, run from the extracted kit folder:

```sh
bash backup.sh
docker compose stop collector experience
docker compose run --rm --no-deps restore \
  --backup /restore/EXACT-BACKUP-FILENAME.sqlite --services-stopped
docker compose up -d --wait experience collector
docker compose exec -T experience python tools/healthcheck.py
```

In PowerShell put the restore command on one line. The restore service already mounts the backups directory and runs as app UID 10001. Keep the checksum file beside the backup. The helper validates integrity and checksum when present, creates a clean temporary SQLite copy, restores app ownership on Linux, atomically replaces the destination and removes stale WAL/SHM files. Do not invoke it while any application or collector still holds the database open. If a check fails, keep the original data and inspect the error before restarting.

## Upgrade and rollback

1. Record the currently deployed image digest/version; take a database backup and private configuration/secret copy.
2. Extract the new release into a new directory. Retain the same Compose project name (`sathvick-experience`) so its named data volume is reused. Copy the approved client configuration and secrets separately.
3. Build/import the new versioned image, review release notes, then run the new installer. Do not use `down -v`; that removes persistent storage.
4. Run staging/production health and acceptance checks.
5. For rollback, stop both kit services and use the previous image/configuration. If a schema changed, restore its matching backup using the controlled process above after assessing newer writes. This release creates additive schema version 1 and rejects a database marked with a newer version. Core OpenG2P data is not involved.

Stopping without deleting data: `docker compose stop collector experience`, or `Stop.cmd`. Starting again: normal installer or `docker compose up -d --wait experience collector`.

## Offline delivery

The full deployment ZIP contains source, the prebuilt frontend and the prebuilt container TAR with its SHA256 checksum. The smaller source-only ZIP omits the TAR. Neither includes Docker Engine. Only a source build needs internet access for the pinned base image and dependencies.

On an approved internet-connected machine with Docker, run `bash prepare-offline.sh` or `Prepare-Offline.cmd`. This builds the runtime and saves `offline/sathvick-experience-1.0.0-rc1.tar`. Transfer the release and that TAR to the client through the agreed channel. Do not accidentally include generated credentials, existing databases or backups.

On the offline target:

```sh
docker load -i offline/sathvick-experience-1.0.0-rc1.tar
bash install.sh
```

Manual import above is optional: `install.sh`, `Start.cmd` and `Start-WSL.cmd` automatically verify/import the supplied TAR when no cached image exists. Windows Docker Desktop: `Start.cmd`; Windows WSL2 Ubuntu-22.04: `Start-WSL.cmd`. The installer detects an already available image and does not build it. Verify the image/TAR checksums through the agreed delivery process. Docker itself must already be installed; this kit does not bootstrap a container engine offline.

## Kubernetes / Helm

The chart uses **one application pod with a collector sidecar**, one local-compatible PVC, a ConfigMap and an existing Secret. Both containers share the same volume; Recreate deployment prevents overlapping SQLite application pods. It is a single-instance deployment, not HA. No HPA or automatic OpenG2P namespace, ingress, database or RBAC changes are supplied. Use a client-approved namespace, storage class, registry and ingress.

1. Build the image on an approved machine. Tag and push it to the client's private registry using their existing process, or import it into the cluster's approved image cache. Do not assume the example `sathvick/…` image exists in a public registry.
2. Run guided configuration using the setup container. You can run setup without starting the application:

```sh
docker compose build experience
docker compose run --rm --no-deps setup
```

On Linux set `SETUP_UID=$(id -u)` and `SETUP_GID=$(id -g)` for that invocation so generated host files belong to the operator. Helm-only setups still need this configuration step or an equivalent operator-prepared JSON/Secret.

3. Export a private Secret manifest. Replace `CLIENT_NAMESPACE` with an existing approved namespace:

```sh
docker compose run --rm --no-deps --entrypoint python setup \
  tools/export_kubernetes.py --root /kit --namespace CLIENT_NAMESPACE
kubectl apply -f config/kubernetes-secret.json
```

This file contains base64-encoded secrets; base64 is not encryption. Keep it private. Normal Kubernetes RBAC/secret-management controls apply. An existing managed Secret can be used instead if it supplies the same environment variable keys.

4. Install the chart with the actual client registry image:

```sh
helm upgrade --install sathvick-experience deploy/helm \
  --namespace CLIENT_NAMESPACE \
  --set-file deploymentConfig=config/deployment.json \
  --set image.repository=CLIENT_REGISTRY/openg2p-experience \
  --set image.tag=1.0.0-rc1 \
  --wait --timeout 5m
```

Set `storage.className`, `storage.size` and `imagePullSecrets` in a client values file as needed. For a private database CA, add public PEM certificates under the `certificates` map in a values file. Each key is mounted as `/app/config/KEY`; use that exact path in the DSN. These are public CA certificates, not client private keys. Do not place password/token values in ConfigMaps or public values files.

5. The Service is ClusterIP on port 18110. Add the client ingress mapping for `/experience/` without URI rewriting, terminating HTTPS at the client's approved gateway. Validate network access to IdP and allowed source endpoints. Configure the public HTTPS URL accordingly.
6. Inspect rollout, readiness and logs. Verify the assigned storage and test backups/restoration. A Kubernetes backup can run `tools/backup.py --directory /tmp/backup` inside the application container and then be copied to approved storage with the client's normal tooling. Do not back up the PVC by blindly copying a live WAL database.

Changes to the ConfigMap trigger a pod restart via its checksum. Changes to an externally managed Secret require an explicit rollout restart. Source collection begins after the application-created analytics schema is ready.
