#!/usr/bin/dumb-init /bin/sh

set -e
set -o errexit
set -o pipefail

if [[ -z "$FRUITSTAND_NO_AUTO_MIGRATE" ]]; then
    echo "Waiting for database to be ready..." >&2
    flask util test-db
    echo "Autorunning migrations..." >&2
    flask db upgrade
    echo "Starting app..." >&2
else
    echo "FRUITSTAND_NO_AUTO_MIGRATE=\"$FRUITSTAND_NO_AUTO_MIGRATE\", not autorunning migrations" >&2
fi

exec uwsgi "$@"