#!/usr/bin/env bash
set -eu
# Lifecycle debugging must never echo Codespaces secret values.
set +x

workspace_dir="$(cd "$(dirname "$0")/.." && pwd)"
runtime_dir="$workspace_dir/.codespaces-runtime"
mkdir -p "$runtime_dir"

wait_for_url() {
  name="$1"
  url="$2"
  log_file="$3"
  attempts=0
  while [ "$attempts" -lt 60 ]; do
    if curl --silent --fail "$url" >/dev/null 2>&1; then
      return 0
    fi
    attempts=$((attempts + 1))
    sleep 1
  done

  echo "$name did not start: $url" >&2
  if [ -f "$log_file" ]; then
    echo "----- $name log -----" >&2
    tail -n 80 "$log_file" >&2
  fi
  return 1
}

stt_provider="${STT_PROVIDER:-gemini}"
analysis_provider="${ANALYSIS_PROVIDER:-gemini}"
if { [ "$stt_provider" = "gemini" ] || [ "$analysis_provider" = "gemini" ]; } && \
  [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "GEMINI_API_KEY is required for the Codespaces demo." >&2
  exit 1
fi

if ! curl --silent --fail http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
  : >"$runtime_dir/api.log"
  (
    cd "$workspace_dir/apps/api"
    STT_PROVIDER="$stt_provider" \
      ANALYSIS_PROVIDER="$analysis_provider" \
      nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
      >"$runtime_dir/api.log" 2>&1 &
    echo $! >"$runtime_dir/api.pid"
  )
fi
wait_for_url "FastAPI" "http://127.0.0.1:8000/api/v1/health" "$runtime_dir/api.log"

if ! curl --silent --fail http://127.0.0.1:3000 >/dev/null 2>&1; then
  : >"$runtime_dir/web.log"
  (
    cd "$workspace_dir/apps/web"
    API_INTERNAL_BASE_URL=http://127.0.0.1:8000 \
      nohup npm run dev -- --hostname 0.0.0.0 \
      >"$runtime_dir/web.log" 2>&1 &
    echo $! >"$runtime_dir/web.pid"
  )
fi
wait_for_url "Next.js" "http://127.0.0.1:3000" "$runtime_dir/web.log"

if [ -n "${CODESPACE_NAME:-}" ] && [ -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]; then
  echo "ACRC-Call-Log: https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
else
  echo "ACRC-Call-Log: http://localhost:3000"
fi
echo "STT Provider: $stt_provider"
echo "Analysis Provider: $analysis_provider"
echo "Share: PORTS > 3000 > Port Visibility > Public"
echo "Logs: tail -f $runtime_dir/api.log $runtime_dir/web.log"
