#!/usr/bin/env bash
set -eu

workspace_dir="$(cd "$(dirname "$0")/.." && pwd)"
runtime_dir="$workspace_dir/.codespaces-runtime"
mkdir -p "$runtime_dir"

analysis_provider="${ANALYSIS_PROVIDER:-mock}"
if [ -n "${GEMINI_API_KEY:-}" ]; then
  analysis_provider="${ANALYSIS_PROVIDER:-gemini}"
fi

if ! curl --silent --fail http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
  (
    cd "$workspace_dir/apps/api"
    STT_PROVIDER="${STT_PROVIDER:-mock}" \
      ANALYSIS_PROVIDER="$analysis_provider" \
      nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
      >"$runtime_dir/api.log" 2>&1 &
    echo $! >"$runtime_dir/api.pid"
  )
fi

if ! curl --silent --fail http://127.0.0.1:3000 >/dev/null 2>&1; then
  (
    cd "$workspace_dir/apps/web"
    API_INTERNAL_BASE_URL=http://127.0.0.1:8000 \
      nohup npm run dev -- --hostname 0.0.0.0 \
      >"$runtime_dir/web.log" 2>&1 &
    echo $! >"$runtime_dir/web.pid"
  )
fi

if [ -n "${CODESPACE_NAME:-}" ] && [ -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]; then
  echo "ACRC-Call-Log: https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
else
  echo "ACRC-Call-Log: http://localhost:3000"
fi
echo "Analysis Provider: $analysis_provider"
