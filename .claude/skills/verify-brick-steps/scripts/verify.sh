#!/usr/bin/env bash
# Brick Steps verification instances: build a site from a copy of chosen models, serve it, check it, stop it.
#   verify.sh launch RUN_ID [SLUG...]   build into .verify/RUN_ID and serve it on a free port (default slug: tank-1)
#   verify.sh doctor RUN_ID             read-only check that this run's instance is worth driving
#   verify.sh stop RUN_ID               stop the server this run started and delete its build; evidence/ stays
#   verify.sh cli RUN_ID -- COMMAND...  run COMMAND in the repo, record it with stdout, stderr and exit code
set -euo pipefail

repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
home=${VERIFY_HOME:-$repo/.verify}

usage() { sed -n '3,6p' "$0" | sed 's/^# *//'; exit 2; }
[[ $# -ge 2 ]] || usage
cmd=$1 id=$2
shift 2
[[ $id =~ ^[A-Za-z0-9._-]+$ ]] || { echo "RUN_ID may only use letters, digits, . _ -" >&2; exit 2; }
run=$home/$id

alive() { [[ -f $run/server.pid ]] && kill -0 "$(cat "$run/server.pid")" 2>/dev/null; }
# True when the pid is the http.server that this run started on its own port and folder.
ours() {
  ps -o args= -p "$(cat "$run/server.pid")" 2>/dev/null |
    grep -qF -- "http.server $(cat "$run/port") --bind 127.0.0.1 --directory $run/site"
}

launch() {
  if alive; then
    echo "run $id is already serving at http://127.0.0.1:$(cat "$run/port")/; stop it first" >&2
    exit 1
  fi
  local slugs=("$@")
  [[ ${#slugs[@]} -gt 0 ]] || slugs=(tank-1)
  rm -rf "$run/root" "$run/site"
  mkdir -p "$run/root/models" "$run/evidence"
  cp -r "$repo/design" "$repo/custom" "$run/root/"
  local s
  for s in "${slugs[@]}"; do
    [[ -f $repo/models/$s/model.mpd ]] || { echo "no model at models/$s" >&2; exit 1; }
    mkdir -p "$run/root/models/$s"
    cp "$repo/models/$s/model.yaml" "$repo/models/$s/model.mpd" "$run/root/models/$s/"
    if [[ -f $repo/models/$s/missions.yaml ]]; then cp "$repo/models/$s/missions.yaml" "$run/root/models/$s/"; fi
  done
  echo "building the site for: ${slugs[*]} (LeoCAD renders every step; about a minute per 30 steps)"
  if ! (cd "$repo" && uv run lc --root "$run/root" --ldraw "$repo/ldraw" site --out "$run/site" --no-pdf) \
      >"$run/evidence/build.log" 2>&1; then
    tail -20 "$run/evidence/build.log" >&2
    exit 1
  fi
  tail -1 "$run/evidence/build.log"
  local port
  port=$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  echo "$port" >"$run/port"
  nohup python3 -m http.server "$port" --bind 127.0.0.1 --directory "$run/site" >"$run/server.log" 2>&1 &
  echo $! >"$run/server.pid"
  local _
  for _ in $(seq 50); do
    if curl -fsS "http://127.0.0.1:$port/index.html" 2>/dev/null | grep -q "Brick Steps"; then
      echo "ready: http://127.0.0.1:$port/"
      echo "evidence: $run/evidence"
      return 0
    fi
    sleep 0.2
  done
  echo "the server did not answer on port $port; see $run/server.log" >&2
  exit 1
}

doctor() {
  local fail=0 port url version d s
  ok() { echo "ok    $*"; }
  bad() { echo "FAIL  $*"; fail=1; }
  if [[ -f $run/site/index.html ]]; then ok "site build at $run/site"; else bad "no site build at $run/site; run launch"; fi
  if alive && ours; then ok "server pid $(cat "$run/server.pid") is this run's http.server"
  else bad "no server started by this run is alive"; fi
  port=$(cat "$run/port" 2>/dev/null || echo 0)
  url=http://127.0.0.1:$port/
  version=$(sed -n 's/^version = "\(.*\)"/\1/p' "$repo/pyproject.toml")
  if curl -fsS "$url" 2>/dev/null | grep -qF "Brick Steps v$version"; then ok "$url serves Brick Steps v$version"
  else bad "$url does not serve Brick Steps v$version"; fi
  for d in "$run"/root/models/*/; do
    [[ -d $d ]] || continue
    s=$(basename "$d")
    if curl -fsS -o /dev/null "${url}$s/" 2>/dev/null; then ok "manual ${url}$s/"
    elif curl -fsS -o /dev/null "${url}lab/$s/" 2>/dev/null; then ok "manual ${url}lab/$s/ (draft, in the lab)"
    else bad "no manual for $s"; fi
  done
  if NODE_PATH=$(npm root -g) node -e 'require("playwright")' 2>/dev/null; then ok "playwright library loads"
  else bad "playwright does not load; npm i -g playwright && playwright install chromium"; fi
  local engine
  for engine in chromium webkit; do
    if NODE_PATH=$(npm root -g) node -e "require('playwright').$engine.launch().then((b) => b.close())" 2>/dev/null
    then ok "$engine launches"
    elif [[ $engine == chromium ]]; then bad "chromium does not launch; playwright install chromium"
    else echo "warn  webkit does not launch on this host (needs: sudo playwright install-deps webkit); use chromium"
    fi
  done
  exit $fail
}

stop() {
  if alive; then
    if ours; then
      kill "$(cat "$run/server.pid")"
      echo "stopped server pid $(cat "$run/server.pid")"
    else
      echo "pid $(cat "$run/server.pid") is not this run's server; left running" >&2
    fi
  fi
  rm -rf "$run/root" "$run/site" "$run/server.pid" "$run/server.log" "$run/port"
  echo "evidence kept: $run/evidence"
}

cli() {
  [[ ${1:-} == -- ]] && shift
  [[ $# -gt 0 ]] || usage
  mkdir -p "$run/evidence/cli"
  local n f code
  n=$(find "$run/evidence/cli" -name '*.txt' | wc -l)
  f=$(printf '%s/evidence/cli/%02d.txt' "$run" $((n + 1)))
  { echo "\$ $*"; echo "--- stdout"; } >"$f"
  set +e
  (cd "$repo" && "$@") >>"$f" 2>"$f.err"
  code=$?
  set -e
  { echo "--- stderr"; cat "$f.err"; echo "--- exit $code"; } >>"$f"
  rm -f "$f.err"
  cat "$f"
  echo "recorded: $f"
  return $code
}

case $cmd in
  launch) launch "$@" ;;
  doctor) doctor ;;
  stop) stop ;;
  cli) cli "$@" ;;
  *) usage ;;
esac
