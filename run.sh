#!/bin/bash
set -e

uv run alembic upgrade head

uv run python -m bin.api &
uv run python -m bin.consumer &

trap 'kill -TERM $(jobs -p) 2>/dev/null' TERM INT

status=0
wait -n || status=$?
kill -TERM $(jobs -p) 2>/dev/null || true
wait || true
exit "$status"