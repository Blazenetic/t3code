#!/usr/bin/env bash
# Dependency-free regression tests for the downstream wrapper surface.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT_DIR="$ROOT/scripts/blazenetic"
COMMON="$SCRIPT_DIR/lib/common.sh"
pass=0

ok() { printf 'ok %d - %s\n' "$((++pass))" "$1"; }
fail() { printf 'not ok - %s\n' "$1" >&2; exit 1; }
assert_contains() { [[ "$1" == *"$2"* ]] || fail "expected output to contain: $2"; }
assert_eq() { [[ "$1" == "$2" ]] || fail "expected '$2', got '$1'"; }

test_otlp() {
  local out
  out="$(env -u T3CODE_OTLP_TRACES_URL -u T3CODE_OTLP_METRICS_URL -u T3CODE_OTLP_SERVICE_NAME \
    T3B_OTLP=1 bash -c 'source "$1"; t3b::apply_otlp_env >/dev/null; printf "%s|%s|%s" "$T3CODE_OTLP_TRACES_URL" "$T3CODE_OTLP_METRICS_URL" "$T3CODE_OTLP_SERVICE_NAME"' _ "$COMMON" 2>/dev/null)"
  assert_eq "$out" "http://127.0.0.1:4318/v1/traces|http://127.0.0.1:4318/v1/metrics|t3-blazenetic"

  out="$(T3B_OTLP=yes T3CODE_OTLP_TRACES_URL=https://trace.example/v1 T3CODE_OTLP_METRICS_URL=https://metric.example/v1 T3CODE_OTLP_SERVICE_NAME=custom \
    bash -c 'source "$1"; t3b::apply_otlp_env >/dev/null; printf "%s|%s|%s" "$T3CODE_OTLP_TRACES_URL" "$T3CODE_OTLP_METRICS_URL" "$T3CODE_OTLP_SERVICE_NAME"' _ "$COMMON" 2>/dev/null)"
  assert_eq "$out" "https://trace.example/v1|https://metric.example/v1|custom"
  T3B_OTLP=off bash -c 'source "$1"; t3b::apply_otlp_env' _ "$COMMON" >/dev/null 2>&1 || fail "false OTLP value rejected"
  if T3B_OTLP=maybe bash -c 'source "$1"; t3b::apply_otlp_env' _ "$COMMON" >/dev/null 2>&1; then fail "invalid OTLP value accepted"; fi
  ok "OTLP defaults, overrides, false values, and validation"
}

test_risks() {
  local out
  out="$(bash -c 'source "$1"; printf "%s|%s|%s|%s" "$(t3b::conflict_risk scripts/blazenetic/t3b)" "$(t3b::conflict_risk apps/web/src/components/settings/SettingsSidebarNav.tsx)" "$(t3b::conflict_risk apps/web/src/components/ChatView.tsx)" "$(t3b::conflict_risk packages/contracts/src/server.ts)"' _ "$COMMON")"
  assert_eq "$out" "LOW|MEDIUM|HIGH|VERY HIGH"
  ok "conflict-risk classifier"
}

test_help() {
  local wrapper
  for wrapper in t3b t3b-web t3b-server t3b-desktop t3b-obs t3b-upstream t3b-sync t3b-publish t3b-feature t3b-check t3b-doctor t3b-shell; do
    "$SCRIPT_DIR/$wrapper" --help >/dev/null 2>&1 || fail "$wrapper --help"
  done
  ok "all wrapper help entry points"
}

test_obs() {
  local temp fake state args out
  temp="$(mktemp -d)"
  trap 'rm -rf "$temp"' RETURN
  state="$temp/state"
  args="$temp/args"
  fake="$temp/fake-engine"
  cat > "$fake" <<'EOF'
#!/usr/bin/env bash
set -u
state=${FAKE_ENGINE_STATE:?}
args=${FAKE_ENGINE_ARGS:?}
printf '%s\n' "$*" >> "$args"
cmd=${1:-}; shift || true
case "$cmd" in
  inspect)
    [[ -f "$state/exists" ]] || exit 1
    if [[ "${1:-}" == "--format" ]]; then
      format=$2
      case "$format" in
        *Config.Labels*) cat "$state/managed" ;;
        *State.Running*) [[ -f "$state/running" ]] && echo true || echo false ;;
        *State.Status*) [[ -f "$state/running" ]] && echo running || echo exited ;;
        *State.Health*) echo healthy ;;
        *NetworkSettings.Ports*) echo '{"3000/tcp":[{"HostIp":"127.0.0.1","HostPort":"3000"}]}' ;;
      esac
    fi
    ;;
  run) mkdir -p "$state"; touch "$state/exists" "$state/running"; echo true > "$state/managed" ;;
  start) touch "$state/running" ;;
  stop) rm -f "$state/running" ;;
  logs) echo fake-logs ;;
esac
EOF
  chmod +x "$fake"
  mkdir -p "$state"
  : > "$args"
  FAKE_ENGINE_STATE="$state" FAKE_ENGINE_ARGS="$args" T3B_OBS_ENGINE="$fake" "$SCRIPT_DIR/t3b-obs" up >/dev/null 2>&1
  out="$(cat "$args")"
  assert_contains "$out" "--label com.blazenetic.t3code.managed=true"
  assert_contains "$out" "127.0.0.1:3000:3000"
  assert_contains "$out" "127.0.0.1:4317:4317"
  assert_contains "$out" "127.0.0.1:4318:4318"
  FAKE_ENGINE_STATE="$state" FAKE_ENGINE_ARGS="$args" T3B_OBS_ENGINE="$fake" "$SCRIPT_DIR/t3b-obs" status >/dev/null
  FAKE_ENGINE_STATE="$state" FAKE_ENGINE_ARGS="$args" T3B_OBS_ENGINE="$fake" "$SCRIPT_DIR/t3b-obs" down >/dev/null
  echo false > "$state/managed"
  if FAKE_ENGINE_STATE="$state" FAKE_ENGINE_ARGS="$args" T3B_OBS_ENGINE="$fake" "$SCRIPT_DIR/t3b-obs" status >/dev/null 2>&1; then fail "unowned container accepted"; fi
  ok "managed-container construction and ownership guard"
  rm -rf "$temp"
  trap - RETURN
}

configure_git() {
  git -C "$1" config user.name Test
  git -C "$1" config user.email test@example.invalid
}

test_upstream_and_feature() {
  local temp repo upstream origin output cfg
  temp="$(mktemp -d)"
  trap 'rm -rf "$temp"' RETURN
  repo="$temp/repo"; upstream="$temp/upstream.git"; origin="$temp/origin.git"; cfg="$temp/config"
  git init -q --bare "$upstream"
  git init -q --bare "$origin"
  git init -q -b main "$repo"
  configure_git "$repo"
  printf 'base\n' > "$repo/base.txt"
  git -C "$repo" add base.txt
  git -C "$repo" commit -qm base
  git -C "$repo" remote add upstream "$upstream"
  git -C "$repo" remote add origin "$origin"
  git -C "$repo" push -q upstream main
  git -C "$repo" remote set-url --push upstream no_push
  git -C "$repo" push -q origin main
  git -C "$repo" branch blazenetic
  git -C "$repo" branch feature/blazeprovements blazenetic
  git -C "$repo" push -q origin blazenetic feature/blazeprovements
  output="$(T3B_REPO="$repo" T3B_FEATURE_BRANCH=feature/blazeprovements "$SCRIPT_DIR/t3b-upstream" --no-fetch --log 2)"
  assert_contains "$output" "main contains no downstream-only commits"
  assert_contains "$output" "feature/blazeprovements vs blazenetic"

  printf 'dirty\n' > "$repo/dirty.txt"
  output="$(T3B_REPO="$repo" T3B_FEATURE_BRANCH=feature/blazeprovements "$SCRIPT_DIR/t3b-upstream" --no-fetch 2>&1)"
  assert_contains "$output" "changed path(s)"
  rm "$repo/dirty.txt"

  git -C "$repo" switch -q main
  printf 'unsafe\n' > "$repo/unsafe.txt"
  git -C "$repo" add unsafe.txt
  git -C "$repo" commit -qm unsafe
  if T3B_REPO="$repo" T3B_FEATURE_BRANCH=feature/blazeprovements "$SCRIPT_DIR/t3b-upstream" --no-fetch >/dev/null 2>&1; then fail "unsafe main accepted"; fi
  git -C "$repo" reset -q --hard HEAD^

  git -C "$repo" update-ref -d refs/remotes/upstream/main
  if T3B_REPO="$repo" T3B_FEATURE_BRANCH=feature/blazeprovements "$SCRIPT_DIR/t3b-upstream" --no-fetch >/dev/null 2>&1; then fail "missing upstream ref accepted"; fi

  T3B_REPO="$repo" T3B_FEATURE_CONFIG_DIR="$cfg" T3B_FEATURE_CONFIG_FILE="$cfg/feature-branch" "$SCRIPT_DIR/t3b-feature" status >/dev/null
  T3B_REPO="$repo" T3B_FEATURE_CONFIG_DIR="$cfg" T3B_FEATURE_CONFIG_FILE="$cfg/feature-branch" "$SCRIPT_DIR/t3b-feature" use feature/blazeprovements >/dev/null
  assert_eq "$(cat "$cfg/feature-branch")" "feature/blazeprovements"
  T3B_REPO="$repo" T3B_FEATURE_BRANCH=feature/blazeprovements "$SCRIPT_DIR/t3b-feature" publish --dry-run >/dev/null
  ok "upstream snapshots and feature status/use/publish dry-run"
  rm -rf "$temp"
  trap - RETURN
}

test_shell_quality() {
  local files=()
  while IFS= read -r file; do files+=("$file"); done < <(find "$SCRIPT_DIR" -type f \( -name '*.sh' -o -name 't3b*' \) -print)
  bash -n "${files[@]}"
  if command -v shellcheck >/dev/null 2>&1; then
    shellcheck -S warning -x "${files[@]}"
  fi
  ok "Bash syntax and ShellCheck warning-level scan"
}

printf 'TAP version 13\n'
test_otlp
test_risks
test_help
test_obs
test_upstream_and_feature
test_shell_quality
printf '1..%d\n' "$pass"
