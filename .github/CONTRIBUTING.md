# How to contribute

We'd love to accept your patches and contributions to this project. There are
just a few small guidelines you need to follow.

## Contributor License Agreement

Contributions to this project must be accompanied by a Contributor License
Agreement. You (or your employer) retain the copyright to your contribution,
this simply gives us permission to use and redistribute your contributions as
part of the project. Head over to <https://cla.developers.google.com/> to see
your current agreements on file or to sign a new one.

You generally only need to submit a CLA once, so if you've already submitted one
(even if it was for a different project), you probably don't need to do it
again.

## Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult [GitHub Help] for more
information on using pull requests.

## Setup local environment

Clone the project and install [uv](https://github.com/astral-sh/uv) (our package manager):

```sh
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup the project
git clone https://github.com/firebase/firebase-functions-python.git
cd firebase-functions-python
uv sync --dev
```

This will automatically:
- Create a virtual environment
- Install all runtime and development dependencies
- Use the Python version specified in `.python-version` (3.10)

(For samples, you can use the same approach but run `uv sync` in each sample directory)

### Running tests

Without coverage:
```bash
uv run pytest
```

With coverage:
```bash
uv run pytest --cov=src --cov-report term --cov-report html --cov-report xml -vv
```

### Formatting code

```bash
uv run ruff format .
```

### Running lints & type checking

```bash
# Type checking
uv run mypy .
# Linting
uv run ruff check .
```

### Generating Docs

Prerequisites:
  - On OSX, install getopt:
    -  `brew install gnu-getopt`

```sh
./docs/generate.sh --out=./docs/build/ --pypath=src/
```

### Deploying a sample for testing

Example:

```sh
cd samples/basic_https
firebase deploy --only=functions
```

Note to test your local changes of `firebase-functions` when deploying you should push your changes to a branch on GitHub and then locally in the `sample/*/requirements.txt` change `firebase-functions` dependency line to instead come from git, e.g. :

```
git+https://github.com/YOUR_USERNAME/firebase-functions-python.git@YOURBRANCH#egg=firebase-functions
```

[github help]: https://help.github.com/articles/about-pull-requests/