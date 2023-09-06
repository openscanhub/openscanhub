#!/bin/bash
set -e
set -x
SELF="$0"
TAG="$1"
TOKEN="$2"

PROJ="openscanhub/openscanhub"

usage() {
    printf "Usage: %s TAG TOKEN\n" "$SELF" >&2
    exit 1
}

# check arguments
test "$TAG" = "$(git describe --tags "$TAG")" || usage
test -n "$TOKEN" || usage

# create a new release on GitHub
curl "https://api.github.com/repos/${PROJ}/releases" \
    --fail --verbose \
    --header "Authorization: token ${TOKEN}" \
    --data '{
    "tag_name": "'"${TAG}"'",
    "target_commitish": "main",
    "name": "'"${TAG}"'",
    "draft": false,
    "prerelease": false
}'
