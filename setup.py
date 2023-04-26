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
"""
Setup for Firebase Functions Python.
"""
from os import path
from setuptools import find_packages, setup

install_requires = [
    'flask>=2.1.2', 'functions-framework>=3.0.0', 'firebase-admin>=6.0.0',
    'pyyaml>=6.0', 'typing-extensions>=4.4.0', 'cloudevents==1.9.0',
    'flask-cors>=3.0.10', 'pyjwt[crypto]>=2.5.0', 'google-events>=0.5.0',
    'google-cloud-firestore>=2.11.0'
]

dev_requires = [
    'pytest>=7.1.2', 'setuptools>=63.4.2', 'pylint>=2.16.1',
    'pytest-cov>=3.0.0', 'mypy>=1.0.0', 'sphinx>=6.1.3',
    'sphinxcontrib-napoleon>=0.7', 'yapf>=0.32.0', 'toml>=0.10.2',
    'google-cloud-tasks>=2.13.1'
]

# Read in the package metadata per recommendations from:
# https://packaging.python.org/guides/single-sourcing-package-version/
init_path = path.join(path.dirname(path.abspath(__file__)), 'src',
                      'firebase_functions', '__init__.py')
version = {}
with open(init_path) as fp:
    exec(fp.read(), version)  # pylint: disable=exec-used

long_description = (
    'The Firebase Functions Python SDK provides an SDK for defining'
    ' Cloud Functions for Firebase.')

setup(
    name='firebase_functions',
    version=version['__version__'],
    description='Firebase Functions Python SDK',
    long_description=long_description,
    url='https://github.com/firebase/firebase-functions-python',
    author='Firebase Team',
    keywords=['firebase', 'functions', 'google', 'cloud'],
    license='Apache License 2.0',
    install_requires=install_requires,
    extras_require={'dev': dev_requires},
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
