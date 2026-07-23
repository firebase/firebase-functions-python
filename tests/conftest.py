# Copyright 2026 Google Inc.
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
"""
Pytest configuration and shared fixtures for the test suite.
"""

import pytest

from firebase_functions import params

# pylint: disable=protected-access


@pytest.fixture(autouse=True)
def _cleanup_params():
    """Clear the global params registry so each test runs with a clean state."""
    params._params.clear()
    yield
    params._params.clear()
