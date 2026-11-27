#!/usr/bin/env bash
# Run every automatic check on one model and keep each report as evidence.
#   check.sh SLUG [OUT]       checks models/SLUG/model.mpd into OUT (default .verify/model-SLUG)
#   check.sh FILE.mpd [OUT]   checks a variant file (default .verify/model-FILE); skips lc validate, which needs a slug
# Prints one summary line per check. Exits 1 when lc validate reports an error, 0 otherwise:
# the other checks point at places to look at, they do not decide.
set -euo pipefail

repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
[[ $# -ge 1 ]] || { sed -n 3,4p "$0" | sed 's/^# *//'; exit 2; }
target=$1
if [[ $target == *.mpd ]]; then
  [[ -f $target ]] || { echo "no file $target" >&2; exit 2; }
  target=$(realpath "$target")
  name=$(basename "$target" .mpd) slug=
else
  [[ -f $repo/models/$target/model.mpd ]] || { echo "no model at models/$target" >&2; exit 2; }
  name=$target slug=$target
fi
out=$(realpath -m "${2:-$repo/.verify/model-$name}")
mkdir -p "$out"
cd "$repo"

# run NAME COMMAND...: OUT/NAME.txt gets the command, its output and its exit code; prints the report's last line.
run() {
  local f=$out/$1.txt code
  shift
  echo "\$ $*" >"$f"
  set +e
  "$@" >>"$f" 2>&1
  code=$?
  set -e
  echo "--- exit $code" >>"$f"
  printf '%-9s %s\n' "$(basename "$f" .txt)" "$(tail -2 "$f" | head -1)"
  return $code
}

failed=0
if [[ -n $slug ]]; then
  run validate uv run lc validate "$slug" || failed=1
  run insertions uv run lc insertions "$slug"
else
  echo "validate  skipped: $name is a file, not a slug"
  echo "insertions skipped: $name is a file, not a slug"
fi
for check in pins overlap axles assembly balance steps; do
  run "$check" uv run python scripts/ldraw_measure.py "$check" "$target"
done
echo "evidence: $out"
exit $failed
