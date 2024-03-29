#!/bin/bash

# Copyright 2023 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e
set -u

function printChangelog() {
  local TITLE=$1
  shift
  # Skip the sentinel value.
  local ENTRIES=("${@:2}")
  if [ ${#ENTRIES[@]} -ne 0 ]; then
    echo "### ${TITLE}"
    echo ""
    for ((i = 0; i < ${#ENTRIES[@]}; i++))
    do
        echo "* ${ENTRIES[$i]}"
    done
    echo ""
  fi
}

if [[ -z "${GITHUB_SHA}" ]]; then
  GITHUB_SHA="HEAD"
fi

LAST_TAG=`git describe --tags $(git rev-list --tags --max-count=1) 2> /dev/null` || true
if [[ -z "${LAST_TAG}" ]]; then
  echo "[INFO] No tags found. Including all commits up to ${GITHUB_SHA}."
  VERSION_RANGE="${GITHUB_SHA}"
else
  echo "[INFO] Last release tag: ${LAST_TAG}."
  COMMIT_SHA=`git show-ref -s ${LAST_TAG}`
  echo "[INFO] Last release commit: ${COMMIT_SHA}."
  VERSION_RANGE="${COMMIT_SHA}..${GITHUB_SHA}"
  echo "[INFO] Including all commits in the range ${VERSION_RANGE}."
fi

echo ""

# Older versions of Bash (< 4.4) treat empty arrays as unbound variables, which triggers
# errors when referencing them. Therefore we initialize each of these arrays with an empty
# sentinel value, and later skip them.
CHANGES=("")
FIXES=("")
FEATS=("")
MISC=("")

while read -r line
do
  COMMIT_MSG=`echo ${line} | cut -d ' ' -f 2-`
  if [[ $COMMIT_MSG =~ ^change(\(.*\))?: ]]; then
    CHANGES+=("$COMMIT_MSG")
  elif [[ $COMMIT_MSG =~ ^fix(\(.*\))?: ]]; then
    FIXES+=("$COMMIT_MSG")
  elif [[ $COMMIT_MSG =~ ^refactor(\(.*\))?: ]]; then
    FIXES+=("$COMMIT_MSG")
  elif [[ $COMMIT_MSG =~ ^feat(\(.*\))?: ]]; then
    FEATS+=("$COMMIT_MSG")
  else
    MISC+=("${COMMIT_MSG}")
  fi
done < <(git log ${VERSION_RANGE} --oneline)

printChangelog "Breaking Changes" "${CHANGES[@]}"
printChangelog "New Features" "${FEATS[@]}"
printChangelog "Bug Fixes" "${FIXES[@]}"