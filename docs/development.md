# Development

[Back to the README](../README.md) · [Usage guide](usage.md) · [Changelog](../CHANGELOG.md)

Contributions should target `main` in [Mins95/ha-remi](https://github.com/Mins95/ha-remi). Run tests in an isolated Linux environment; use WSL on Windows. The release runtime is **Python 3.14.10 with Home Assistant 2026.11.0**.

## Python tests

From the repository root, create a fresh environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install uv==0.13.7
python -m uv pip install -r requirements-test.txt
python scripts/run_tests.py --cov --cov-report=term-missing
```

The requirements pair the official `pytest-homeassistant==2026.11.0` fixtures with `homeassistant==2026.11.0`. Do not keep `pytest-homeassistant-custom-component` installed alongside them: the plugins register overlapping fixtures. The runner checks both exact versions, rejects the older plugin and loads Home Assistant before pytest plugins.

Pass a test path or pytest options to the same runner for a targeted check:

```sh
python scripts/run_tests.py tests/test_api.py -q
```

CI installs the same requirements with `python -m uv pip install --system -r requirements-test.txt` in its disposable Python environment. For a local virtual environment, use the command without `--system` shown above.

## Card and loader tests

With Node.js available, run the bundled frontend tests from the repository root:

```sh
node --test tests/*.test.mjs
```

These tests cover the card and its resource loader. They do not replace checking layout and interaction in a real Home Assistant dashboard, or testing the physical effect of a command on REMI.

## Continuous integration and releases

- [Tests](https://github.com/Mins95/ha-remi/actions/workflows/tests.yml) run the Python suite against Home Assistant 2026.11.0 and the Node.js card tests.
- [Hassfest](https://github.com/Mins95/ha-remi/actions/workflows/hassfest.yml) validates the integration's Home Assistant metadata.
- [HACS validation](https://github.com/Mins95/ha-remi/actions/workflows/hacs.yml) checks repository compatibility.
- [Release](https://github.com/Mins95/ha-remi/actions/workflows/release.yml) checks the requested version against the manifest and changelog and runs validation before publishing. Tags containing a pre-release suffix are published as pre-releases rather than becoming the latest stable release.

Starting with 0.5.0, releases provide `urbanhello_remi_unofficial.zip`, containing the integration files directly at its root. Marketplace and HACS use this packaged asset; [manual installation](usage.md#manual-installation) explains its destination directory. Older releases retain their original packaging configuration.

The README's download badge counts downloads of GitHub release assets, introduced here with 0.5.0. It is not a count of installations or unique users, and it does not include past downloads of GitHub's automatically generated source archives.

Describe behavior changes and relevant validation in the pull request. Keep protocol findings factual and distinguish automated payload tests from confirmed physical behavior. Use synthetic examples in tests and documentation; never include credentials, session tokens or personal device data.
