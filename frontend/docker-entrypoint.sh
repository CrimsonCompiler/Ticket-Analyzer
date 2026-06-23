#!/bin/sh
# Substitute BACKEND_HOST / BACKEND_PORT placeholders into the nginx
# template, then exec whatever CMD was provided (typically
# `nginx -g daemon off;`).
#
# IMPORTANT: the placeholders in nginx.conf MUST be written as
# `${BACKEND_HOST}` / `${BACKEND_PORT}` — same syntax as envsubst.
# That lets nginx see a literal upstream address after substitution,
# so it does NOT need a `resolver` directive.
set -eu

envsubst '${BACKEND_HOST} ${BACKEND_PORT}' \
    < /etc/nginx/templates/default.conf.template \
    > /etc/nginx/conf.d/default.conf

exec "$@"
