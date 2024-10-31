#!/usr/bin/env sh

set -ex

cleanup() {
  current_dir_name=$(basename "$PWD")

  if [ "$current_dir_name" = ".tmp" ]; then
    cd ..
  fi

  if [ -z "$DEBUG" ]; then
    rm -rf .tmp
  fi
}

trap cleanup EXIT

if [ -d ".tmp" ]; then
  rm -rf .tmp
fi

mkdir .tmp
cd .tmp

git init
git remote add origin https://github.com/firebase/firebase-functions.git
git config core.sparseCheckout true
mkdir -p .git/info
echo 'integration_test/**/*' > .git/info/sparse-checkout
git fetch origin v2-integration-tests
git pull origin v2-integration-tests
git checkout v2-integration-tests

rm -rf integration_test/functions
rm -f integration_test/.env.example

mv integration_test/* ../
for file in integration_test/.[!.]* integration_test/..?*; do
  [ -e "$file" ] && mv "$file" ../
done

cd ..
rm -rf tests/v1
rm -rf .tmp
