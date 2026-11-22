#!/bin/bash
# Check out Anki's source at ANKI_TAG (shared/versions.env) into <dir> and
# apply shared/patches/anki-*.patch. Run again after ANKI_TAG changes: a
# checkout of another tag is replaced (its target/ is kept, so Rust rebuilds
# incrementally), and the patches are reapplied onto clean sources when they
# changed.
# Usage: anki_source.sh <dir>
set -euo pipefail
SHARED=$(cd "$(dirname "$0")/.." && pwd)
source "$SHARED/versions.env"
DIR=$1

repo=https://github.com/ankitects/anki
ref=refs/tags/$ANKI_TAG
current=refs/tags/$(git -C "$DIR" describe --tags --exact-match 2>/dev/null || true)
if [ -n "${KIOKU_ANKI_REV:-}" ]; then
    repo=https://github.com/JSchoreels/anki
    ref=$KIOKU_ANKI_REV
    current=$(git -C "$DIR" rev-parse HEAD 2>/dev/null || true)
fi
refspec=$ref
[[ $ref == refs/tags/* ]] && refspec="$ref:$ref"
if [ "$current" != "$ref" ]; then
    # $DIR may hold an older checkout, or target/ alone (restored by CI's
    # Rust cache)
    rm -rf "$DIR.new"
    git init -q "$DIR.new"
    git -C "$DIR.new" remote add origin "$repo"
    git -C "$DIR.new" fetch -q --depth 1 origin "${refspec:-$ref}"
    git -C "$DIR.new" checkout -q --detach FETCH_HEAD
    git -C "$DIR.new" submodule update -q --init --depth 1
    [ -d "$DIR/target" ] && mv "$DIR/target" "$DIR.new/"
    rm -rf "$DIR" && mv "$DIR.new" "$DIR"
fi

applied() {
    for patch in "$SHARED"/patches/anki-*.patch; do
        git -C "$DIR" apply -R --check "$patch" 2> /dev/null || return 1
    done
}
if ! applied; then
    # back to the release's sources (target/ and out/ are ignored, so kept)
    git -C "$DIR" checkout -q -- .
    git -C "$DIR" clean -fdq
    for patch in "$SHARED"/patches/anki-*.patch; do
        if ! git -C "$DIR" apply "$patch"; then
            echo "$patch does not apply to Anki $ANKI_TAG; see shared/patches/README.md" >&2
            exit 1
        fi
    done
fi
