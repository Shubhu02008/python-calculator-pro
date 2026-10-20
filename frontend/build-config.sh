#!/bin/sh
set -eu
: "${API_BASE_URL:?Render must provide API_BASE_URL}"
case "$API_BASE_URL" in
  https://*) ;;
  *) echo "API_BASE_URL must be an HTTPS URL" >&2; exit 1 ;;
esac
printf 'window.CALCULATOR_API_BASE_URL = "%s";\n' "$API_BASE_URL" > frontend/config.js
