#!/bin/sh
# PhishGuard AI container entrypoint.
#   api      -> run migrations, then serve the API with uvicorn
#   worker   -> Celery worker (scans + reports)
#   beat     -> Celery beat scheduler
#   flower   -> Celery monitoring UI (protect it with FLOWER_BASIC_AUTH)
#   anything else is executed verbatim (e.g. "python -m app.cli create-admin")
set -e

case "$1" in
  api)
    if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
      python -m app.cli migrate
    fi
    exec uvicorn app.main:app \
      --host 0.0.0.0 --port 8000 \
      --workers "${WEB_CONCURRENCY:-2}" \
      --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
      --no-server-header
    ;;
  worker)
    export PHISHGUARD_WORKER=1
    exec celery -A app.workers.celery_app worker --loglevel="${LOG_LEVEL:-info}" \
      --concurrency="${WORKER_CONCURRENCY:-4}" -Q default,scans,reports
    ;;
  beat)
    export PHISHGUARD_WORKER=1
    exec celery -A app.workers.celery_app beat --loglevel="${LOG_LEVEL:-info}" --schedule /tmp/celerybeat-schedule
    ;;
  flower)
    if [ -z "${FLOWER_BASIC_AUTH}" ]; then
      echo "Refusing to start Flower without FLOWER_BASIC_AUTH=user:password" >&2
      exit 1
    fi
    exec celery -A app.workers.celery_app flower --port=5555 --basic-auth="${FLOWER_BASIC_AUTH}"
    ;;
  *)
    exec "$@"
    ;;
esac
