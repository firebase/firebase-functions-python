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
"""A light wrapper around the Functions Framework for the purpose of emulator support."""

import os
from functions_framework import create_app
from functions_framework._http.gunicorn import GunicornApplication

# Environment variables:
#   FUNCTION_TARGET
#   FUNCTION_SOURCE
#   FUNCTION_SIGNATURE_TYPE  = "http", "event", "cloudevent" - default "http"
#   HOST


def create_server(bind):
    app = create_app()
    GunicornApplication(app, "", "", False, options={"host": bind}).run()


def main():
    create_server(os.environ["HOST"])


if __name__ == "__main__":
    main()
