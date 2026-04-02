#!/usr/bin/env bash

cd analytics-db

attempts=0
until docker compose exec -it whpg7_cdw cat /gpinitsystem_complete; do
  if (( attempts == 60 )); then
    echo "Timed out waiting for cluster!"
    exit 1
  fi
  attempts=$((attempts + 1))
  echo "Waiting for cluster to come online..."
  sleep 2
done

docker compose exec -u gpadmin -e USER=gpadmin -it whpg7_cdw bash -ic "gpstate"

# We can't set PGAA GUCs in WHPG until PGAA registers them,
# so we need to first add PGAA to SPL, restart, then configure, and restart again.
# Seafowl is managed by systemd (started by init_system.sh after cluster init).
docker compose exec -u gpadmin -e USER=gpadmin -it whpg7_cdw bash -ic "
  gpconfig -c shared_preload_libraries -v pgaa && \
  gpstop -a -M fast -r && \
  gpconfig -c pgaa.enable_maintenance_worker -v true && \
  gpconfig -c pgaa.maintenance_worker_sleep_interval -v 1s && \
  gpconfig -c pgaa.spark_connect_url -v sc://spark-connect:15002 && \
  psql postgres -c 'CREATE EXTENSION IF NOT EXISTS PGAA CASCADE' && \
  psql postgres -c 'SELECT pgaa.pgaa_version()' && \
  gpstop -a -M fast -r
"

# Verify Seafowl is running via systemd
docker compose exec -it whpg7_cdw bash -c "systemctl status seafowl.service"
for i in $(seq 1 30); do
  if docker compose exec whpg7_cdw ss -tlnp 2>/dev/null | grep -q ':47470'; then
    echo "Seafowl is listening on port 47470"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Timed out waiting for Seafowl!"
    docker compose exec whpg7_cdw journalctl -u seafowl.service --no-pager -n 50
    exit 1
  fi
  echo "Waiting for Seafowl... ($i/30)"
  sleep 1
done
