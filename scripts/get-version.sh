#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.
set -ex

PKG="osh"

# enter the top-level directory
cd "$(git rev-parse --show-toplevel)"

# resolve version
snap="$(git describe --tags)"
[[ "$snap" =~ ${PKG}- ]]
ver="${snap##"${PKG}-"}"

# include timestamp
ts="$(git log --pretty="%cd" --date=iso -1 \
    | sed -r -e 's|[:-]||g' -e 's|^([0-9]+) ([0-9]+).*$|\1.\2|')"
ver="$(echo "$ver" | sed -r "s|-[0-9]+-|.${ts}.|")"

# handle non-default branch and local changes
branch="$(git rev-parse --abbrev-ref HEAD)"
test "main" = "${branch}" || ver="${ver}.${branch//[\/-]/_}"
test -z "$(git diff HEAD > /dev/null)" || ver="${ver}.dirty"

# finally print the version string
echo "$ver"
