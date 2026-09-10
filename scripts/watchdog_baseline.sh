#!/usr/bin/env bash
# Keep the baseline eval running unattended until it completes.
#
# Both the vLLM server and run_baseline.py are launched detached, so they already survive a
# disconnect. What they do not survive is crashing. This supervises them: if the server dies
# it is restarted, and if the eval exits before finishing it is relaunched -- safe because the
# eval is resumable, keyed by (sample_id, mode), so a relaunch skips completed rollouts.
#
#   setsid nohup scripts/watchdog_baseline.sh > watchdog.log 2>&1 < /dev/null & disown
#
# Exits 0 when the run is complete, 1 if it gives up after too many restarts.
set -uo pipefail
cd "$(dirname "$0")/.."

LABEL="${LABEL:-base}"
RIF_TARGET=300
CC_TARGET=2700
MAX_RESTARTS="${MAX_RESTARTS:-20}"
CHECK_EVERY="${CHECK_EVERY:-60}"
SCRATCH="${SCRATCH:-/tmp/claude-1011/-home-ola/92b1ce5e-9b14-416b-98d3-81624826762f/scratchpad}"
restarts=0

log() { echo "[$(date -Is)] $*"; }
count() { local f="results/$LABEL/$1"; if [[ -f "$f" ]]; then wc -l < "$f"; else echo 0; fi; }
server_up() { curl -s -m 10 http://localhost:8000/v1/models >/dev/null 2>&1; }
eval_running() { pgrep -f "run_[b]aseline.py --label $LABEL" >/dev/null; }

start_server() {
  log "starting vLLM server"
  setsid nohup ./scripts/serve_vllm.sh > "$SCRATCH/vllm_watchdog_$(date +%s).log" 2>&1 < /dev/null &
  for _ in $(seq 1 60); do sleep 15; server_up && { log "server up"; return 0; }; done
  log "server did NOT come up within 15 min"; return 1
}

start_eval() {
  log "starting run_baseline.py --label $LABEL (restart #$restarts)"
  setsid nohup .venv/bin/python scripts/run_baseline.py --label "$LABEL" \
    >> "$SCRATCH/baseline.log" 2>&1 < /dev/null &
  sleep 30
}

log "watchdog started (label=$LABEL, target ${RIF_TARGET}+${CC_TARGET})"
while true; do
  rif=$(count reasonif_rollouts.jsonl); cc=$(count cotcontrol_rollouts.jsonl)

  # Complete only when the summary exists too -- the eval still has judging and reporting to do
  # after the last rollout lands.
  if [[ "$rif" -ge "$RIF_TARGET" && "$cc" -ge "$CC_TARGET" ]] && ! eval_running; then
    if [[ -f "results/$LABEL/summary_${LABEL}.json" ]]; then
      log "COMPLETE: reasonif $rif/$RIF_TARGET, cotcontrol $cc/$CC_TARGET, summary written"
      exit 0
    fi
    log "rollouts complete but no summary yet -- relaunching to finish judging/reporting"
  fi

  if ! eval_running; then
    if [[ "$restarts" -ge "$MAX_RESTARTS" ]]; then
      log "GIVING UP after $restarts restarts (reasonif $rif, cotcontrol $cc)"; exit 1
    fi
    server_up || start_server || { log "server unavailable; retrying next cycle"; sleep "$CHECK_EVERY"; continue; }
    restarts=$((restarts + 1))
    start_eval
  elif ! server_up; then
    # Eval alive but server gone: its requests are failing and being recorded as errors.
    # Errored rollouts are retried on the next run, so stop the eval and bring both back.
    log "server down while eval running -- restarting both"
    pkill -f "run_[b]aseline.py --label $LABEL"
    sleep 5
    start_server && { restarts=$((restarts + 1)); start_eval; }
  fi

  sleep "$CHECK_EVERY"
done
