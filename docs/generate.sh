#!/bin/bash
# Copyright 2022 Google Inc.
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
#
# generate.sh --- Produces HTML documentation from Python modules
#
# Arguments:
#   --out=path/to/copy/output
#   [--pypath=path/to/add/to/pythonpath]
#   [--sphinx-build=path/to/sphinx-build]
#   [--themepath=path/to/sphinx/themes]
#   TARGET
#
# Prerequisites:
#   Install the required Python modules:
#     pip install sphinx sphinxcontrib-napoleon
# . On OSX, install getopt:
# .   :brew install gnu-getopt
#
# Example:
#   generate.sh \
#     --out=./docs/dist/

SPHINXBIN=sphinx-build
THEMEPATH=$(dirname $0)/theme
THEMEPATH=$(realpath "$THEMEPATH")

if [[ $(uname) == "Darwin" ]]; then
  TEMPARGS=$($(brew --prefix)/opt/gnu-getopt/bin/getopt -o o:p:b:t: --long out:,pypath:,sphinx-build:,themepath: -- "$@")
else
  TEMPARGS=$(getopt -o o:p:b:t: --long out:,pypath:,sphinx-build:,themepath: -- "$@")
  getopt = getopt
fi
eval set -- "$TEMPARGS"

while true; do
  case "$1" in
  -o | --out)
    OUTDIR=$(realpath "$2")
    shift 2
    ;;
  -p | --pypath)
    PYTHONPATH=$(realpath "$2"):"$PYTHONPATH"
    shift 2
    ;;
  -b | --sphinx-build)
    SPHINXBIN=$(realpath "$2")
    shift 2
    ;;
  -t | --themepath)
    THEMEPATH=$(realpath "$2")
    shift 2
    ;;
  --)
    shift
    break
    ;;
  *)
    echo Error
    exit 1
    ;;
  esac
done

TARGET="$1"
PYTHONPATH="$THEMEPATH":"$PYTHONPATH"

if [[ "$OUTDIR" == "" ]]; then
  echo Output directory not specified.
  exit 1
fi

TITLE="Firebase Python SDK for Cloud Functions"
PY_MODULES='firebase_functions.core
            firebase_functions.alerts_fn
            firebase_functions.alerts.app_distribution_fn
            firebase_functions.alerts.billing_fn
            firebase_functions.alerts.crashlytics_fn
            firebase_functions.alerts.performance_fn
            firebase_functions.db_fn
            firebase_functions.eventarc_fn
            firebase_functions.firestore_fn
            firebase_functions.https_fn
            firebase_functions.identity_fn
            firebase_functions.options
            firebase_functions.params
            firebase_functions.pubsub_fn
            firebase_functions.remote_config_fn
            firebase_functions.scheduler_fn
            firebase_functions.storage_fn
            firebase_functions.tasks_fn
            firebase_functions.test_lab_fn'
DEVSITE_PATH='/docs/reference/functions/2nd-gen/python'

#
# Set up temporary project
#
PROJDIR=$(mktemp -d)
echo Created project directory: "$PROJDIR"
pushd "$PROJDIR" >/dev/null
mkdir _build

cat >conf.py <<EOL
import devsite_translator.html

exclude_patterns = ['venv/**']
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']
source_suffix = '.rst'
master_doc = 'index'
todo_include_todos = False
html_theme = "devsite_sphinx_theme"
html_theme_path = ["$THEMEPATH"]
html_permalinks = False
smartquotes = False
project = u'$TITLE'
copyright = u'2022, Google'
author = u'Google'
def setup(app):
  app.set_translator('html', devsite_translator.html.FiresiteHTMLTranslator)
EOL

for m in ${PY_MODULES}; do
  cat >"$m".rst <<EOL
${m} module
===============================================================================

.. automodule:: ${m}
    :members:
    :undoc-members:
    :show-inheritance:
    :member-order: groupwise
EOL
done

cat >index.rst <<EOL
${TITLE}
===============================================================================

.. toctree::
   :maxdepth: 2

EOL

for m in ${PY_MODULES}; do
  echo "   ${m}" >>index.rst
done

#
# Run sphinx-build
#

echo Building HTML...
echo "$PYTHONPATH"
PYTHONPATH="$PYTHONPATH" "$SPHINXBIN" -W -v -b html . _build/
if [ "$?" -ne 0 ]; then
  exit 1
fi

#
# Copy output
#

echo Copying output to "$OUTDIR"...
mkdir -p $OUTDIR
for m in ${PY_MODULES}; do
  cp _build/"$m".html "$OUTDIR"
done
cp _build/index.html "$OUTDIR"
cp _build/objects.inv "$OUTDIR"

#
# Create _toc.yaml
#

TOC="$OUTDIR"/_toc.yaml
cat >"$TOC" <<EOL
toc:
EOL
for m in ${PY_MODULES}; do
  echo "- title: ${m}" >>"$TOC"
  echo "  path: ${DEVSITE_PATH}/${m}" >>"$TOC"
done

popd >/dev/null
