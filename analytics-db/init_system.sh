#!/bin/bash
## ======================================================================
## Container initialization script (runs as a systemd oneshot service)
## ======================================================================
set -e

sudo ln -sf /usr/bin/python2.7 /usr/bin/python

# ----------------------------------------------------------------------
# Remove /run/nologin to allow logins
# ----------------------------------------------------------------------
sudo rm -rf /run/nologin

# ## Change ownership to gpadmin
sudo chown -R gpadmin.gpadmin /usr/local/greenplum-db \
                              /tmp/gpinitsystem_config \
                              /tmp/hostfile_gpinitsystem \
                              /tmp/gpdb-hosts

if [ $HOSTNAME == "cdw" ]; then
  sudo chown -R gpadmin.gpadmin /data
else
  sudo chown -R gpadmin.gpadmin /data1
  sudo chown -R gpadmin.gpadmin /data2
fi

# ----------------------------------------------------------------------
# Configure passwordless SSH access for 'gpadmin' user
# ----------------------------------------------------------------------
mkdir -p /home/gpadmin/.ssh
chmod 700 /home/gpadmin/.ssh

if [ ! -f /home/gpadmin/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 4096 -C gpadmin -f /home/gpadmin/.ssh/id_rsa -P "" > /dev/null 2>&1
fi

cat /home/gpadmin/.ssh/id_rsa.pub >> /home/gpadmin/.ssh/authorized_keys
chmod 600 /home/gpadmin/.ssh/authorized_keys

# Add the container's hostname to the known_hosts file to avoid SSH warnings
ssh-keyscan -t rsa cdw > /home/gpadmin/.ssh/known_hosts 2>/dev/null

# Source environment variables and set MASTER_DATA_DIRECTORY
source /usr/local/greenplum-db/greenplum_path.sh
export MASTER_DATA_DIRECTORY=/data/master/gpseg-1

# Initialize multi node WarehousePG cluster
sshpass -p "changeme@123" ssh-copy-id -o StrictHostKeyChecking=no sdw1
sshpass -p "changeme@123" ssh-copy-id -o StrictHostKeyChecking=no sdw2
gpinitsystem -a \
             -c /tmp/gpinitsystem_config \
             -h /tmp/hostfile_gpinitsystem \
             --max_connections=100

printf "sdw1\nsdw2\n" >> /tmp/gpdb-hosts

if [ $HOSTNAME == "cdw" ]; then
     ## Allow any host access the WarehousePG Cluster
     echo 'host all all 0.0.0.0/0 trust' >> /data/master/gpseg-1/pg_hba.conf
     # for host in sdw1 sdw2; do
     #   ssh "$host" 'for d in /data1/primary/gpseg* /data2/primary/gpseg* /data1/mirror/gpseg* /data2/mirror/gpseg*; do
     #     [ -f "$d/pg_hba.conf" ] && echo "host all all 0.0.0.0/0 trust" >> "$d/pg_hba.conf"
     #   done'
     # done
     gpstop -u

     psql -d template1 \
          -c "ALTER USER gpadmin PASSWORD 'changeme@123'"

     cat <<-'EOF'

======================================================================
Sandbox: WarehousePG Database Cluster details
======================================================================

EOF

     echo "Current time: $(date)"
     source /etc/os-release
     echo "OS Version: ${NAME} ${VERSION}"

     ## Set gpadmin password, display version and cluster configuration
     psql -P pager=off -d template1 -c "SELECT VERSION()"
     psql -P pager=off -d template1 -c "SELECT * FROM gp_segment_configuration ORDER BY dbid"
     psql -P pager=off -d template1 -c "SHOW optimizer"

     sudo touch /gpinitsystem_complete

     # Start Seafowl via systemd (same as production RHEL hosts)
     if [ -x /usr/local/greenplum-db/bin/seafowl ] && [ -f /etc/edb/pgaa/seafowl.toml ]; then
       echo "Starting Seafowl service..."
       sudo systemctl start seafowl.service
       sudo systemctl status seafowl.service || true
     fi
fi

echo "
===========================
=  DEPLOYMENT SUCCESSFUL  =
===========================


======================================================================
 __          __            _                          _____   _____
 \ \        / /           | |                        |  __ \ / ____|
  \ \  /\  / /_ _ _ __ ___| |__   ___  _   _ ___  ___| |__) | |  __
   \ \/  \/ / _\` | '__/ _ \ '_ \ / _ \| | | / __|/ _ \  ___/| | |_ |
    \  /\  / (_| | | |  __/ | | | (_) | |_| \__ \  __/ |    | |__| |
     \/  \/ \__,_|_|  \___|_| |_|\___/ \__,_|___/\___|_|     \_____|

======================================================================"
