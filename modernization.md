# Firebase Functions Python Repository Modernization Plan

## Overview
Modernize the Firebase Functions Python SDK to use contemporary Python tooling while maintaining compatibility with existing release processes and improving developer experience.

## 1. **Migrate to Modern pyproject.toml Packaging**
- Convert setup.py to a modern pyproject.toml using setuptools build backend
- Keep dynamic version reading from `__init__.py` (required by release process)
- Preserve all metadata, classifiers, and package configuration
- Use PEP 621 standard for metadata
- Configure build backend: `[build-system]` with setuptools
- Remove setup.py entirely after migration

## 2. **Adopt uv for Development**
- Replace pip/venv with uv for faster dependency management
- Define all dependencies in pyproject.toml:
  ```toml
  [project.dependencies]  # Runtime dependencies
  [project.optional-dependencies]
  dev = [...]  # All dev dependencies
  test = [...]  # Test-only dependencies
  docs = [...]  # Documentation dependencies
  ```
- Generate uv.lock for reproducible builds
- Add .python-version file set to 3.10

## 3. **Replace pylint/YAPF with ruff**
- Configure ruff to match current Google style guide:
  - Line length: 100
  - Indentation: 4 spaces
  - Enable equivalent pylint rules
- Remove .pylintrc and yapf configuration
- Add comprehensive ruff configuration in pyproject.toml
- Set target-version = "py310" for compatibility checks

## 4. **Consider tox for Testing**
Yes, add tox for:
- Testing across Python 3.10, 3.11, 3.12
- Running different test environments (unit, integration)
- Linting/formatting environments
- Documentation building
- Type checking
- Package building verification

Benefits:
- Ensures compatibility across Python versions
- Isolated test environments
- Reproducible testing
- Can be used both locally and in CI

## 5. **Add Modern Development Tools**
### Pre-commit hooks:
- ruff format and lint checks
- mypy type checking
- Check merge conflicts
- Trailing whitespace
- End of file fixer
- Check added large files
- Validate pyproject.toml

### Development scripts:
Add convenience commands via:
- justfile for task automation
- Or pyproject.toml scripts section
- Common tasks: test, lint, format, typecheck, docs

## 6. **Update CI/CD Workflows**

### CI Workflow Updates:
- Install uv in GitHub Actions
- Use `uv sync` instead of `pip install`
- Replace pylint with `ruff check`
- Replace yapf with `ruff format --check`
- Use uv's built-in venv management
- Add dependency caching for uv

### Release Workflow Updates:
**Critical**: The release process depends on:
1. Reading version from `src/firebase_functions/__init__.py`
2. Building with `python setup.py bdist_wheel sdist`
3. Specific artifact naming patterns

**Changes needed**:
- Replace `python setup.py bdist_wheel sdist` with `python -m build`
- Ensure pyproject.toml maintains dynamic version reading
- Keep artifact names identical (firebase_functions-{version}-py3-none-any.whl)
- No changes needed to publish_preflight_check.sh

## 7. **Migration Strategy**

### Phase 1: Add new tooling (non-breaking)
1. Create comprehensive pyproject.toml
2. Install and configure uv
3. Set up ruff configuration
4. Add tox.ini
5. Configure pre-commit

### Phase 2: Update workflows
1. Update local development docs
2. Modify CI to use new tools
3. Update release workflow for modern build

### Phase 3: Remove old tooling
1. Remove setup.py
2. Delete .pylintrc
3. Remove yapf config from current pyproject.toml
4. Clean up old dependencies

## 8. **File Structure Changes**

### New files:
- `pyproject.toml` (expanded with all config)
- `uv.lock`
- `.python-version`
- `tox.ini`
- `.pre-commit-config.yaml`
- `justfile` (optional)

### Modified files:
- `.github/workflows/ci.yaml`
- `.github/workflows/release.yaml`
- `.gitignore` (add uv directories)

### Removed files:
- `setup.py`
- `.pylintrc`
- `pytest.ini` (migrate to pyproject.toml)

## 9. **Compatibility Considerations**

- Maintain Python 3.10+ requirement
- Keep all existing package metadata
- Preserve version reading mechanism
- Ensure built artifacts remain identical
- No changes to API or functionality
- Support existing installation methods

## 10. **Benefits Summary**

- **10-100x faster**: uv for dependency management
- **Faster linting**: ruff vs pylint/yapf
- **Modern standards**: PEP 517/518/621 compliance
- **Better reproducibility**: Lock files
- **Improved DX**: Pre-commit hooks, better tooling
- **Multi-version testing**: tox integration
- **Simpler configuration**: Everything in pyproject.toml

## Implementation Steps

1. Save this plan as modernization.md
2. Create new pyproject.toml with all configurations
3. Set up uv and generate lock file
4. Configure and test ruff
5. Add tox configuration
6. Set up pre-commit hooks
7. Update CI/CD workflows
8. Remove old configuration files
9. Update documentation

This plan modernizes the tooling while maintaining full compatibility with the existing release process and Firebase ecosystem requirements.