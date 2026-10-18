#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$HOME/.local/bin"
for name in t3b t3b-web t3b-desktop t3b-server t3b-agent t3b-check t3b-sync t3b-maintain; do
  target="$HOME/.local/bin/$name"
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ ! -L "$target" || $(readlink "$target") != "$root/$name" ]]; then
      printf 'Preserving existing command: %s\n' "$target" >&2
      exit 1
    fi
  fi
done
for name in t3b t3b-web t3b-desktop t3b-server t3b-agent t3b-check t3b-sync t3b-maintain; do
  ln -sfn "$root/$name" "$HOME/.local/bin/$name"
done
printf 'Development commands installed. Daily runtime installation is separate.\n'
