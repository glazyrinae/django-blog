#!/bin/bash
set -euo pipefail

PGREST_USER=${PGREST_USER:-pgbackresthost}
PGREST_GROUP=${PGREST_GROUP:-pgbackresthost}
SSH_DIR="/home/${PGREST_USER}/.ssh"
SSH_SOURCE_DIR=${PGREST_SSH_SOURCE_DIR:-/config/pgbackrest-ssh}

sync_ssh_dir() {
    mkdir -p "${SSH_DIR}"

    if [ -d "${SSH_SOURCE_DIR}" ] && [ -n "$(ls -A "${SSH_SOURCE_DIR}" 2>/dev/null)" ]; then
        rsync -a --delete "${SSH_SOURCE_DIR}/" "${SSH_DIR}/"
    fi

    if [ "${PGREST_SSH_FIX_PERMS:-1}" = "1" ]; then
        chown -R "${PGREST_USER}:${PGREST_GROUP}" "${SSH_DIR}" || true
        chmod 700 "${SSH_DIR}" || true
        find "${SSH_DIR}" -type f -not -perm 600 -exec chmod 600 {} \; || true
    fi
}

prepare_host_keys() {
    ssh-keygen -A
}

sync_ssh_dir

if [ "${1:-}" = "sshd" ] || [ "${1:-}" = "/usr/sbin/sshd" ]; then
    shift
    prepare_host_keys
    if [ "$#" -eq 0 ]; then
        set -- -D -e
    fi
    exec /usr/sbin/sshd "$@"
fi

if [[ "${1:-}" == -* ]]; then
    set -- pgbackrest "$@"
fi

if [ "${1:-}" = "pgbackrest" ]; then
    shift
    exec gosu "${PGREST_USER}:${PGREST_GROUP}" pgbackrest "$@"
fi

exec gosu "${PGREST_USER}:${PGREST_GROUP}" "$@"
