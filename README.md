# prozorro-cli

CLI.

## 🧭 Navigation

- [📦 Installation](#installation)
- [⌨️ Commands](#commands)
- [🛠️ Development](#development)
- [🚀 Release](#release)

<a id="installation"></a>

## 📦 Installation

```powershell
pip install prozorro-cli
prozorro-cli --help
```

For an isolated global CLI installation, you can also use
`pipx install prozorro-cli`.

<a id="commands"></a>

## ⌨️ Commands

```powershell
# Print the full Public API JSON URL
prozorro-cli tender UA-2026-06-15-003439-a --link

# Print the tender HTML page URL
prozorro-cli tender UA-2026-06-15-003439-a --link-html

# Print and open the Public API JSON in a browser
prozorro-cli tender UA-2026-06-15-003439-a --link --open

# Print and open the HTML page in a browser
prozorro-cli tender UA-2026-06-15-003439-a --link-html --open

# Short alias for --link-html
prozorro-cli tender UA-2026-06-15-003439-a --linkhtml --open

# Internal Prozorro ID
prozorro-cli tender UA-2026-06-15-003439-a --guid

# The same ID in standard UUID format
prozorro-cli tender UA-2026-06-15-003439-a --guid-normal

# Full JSON from public-api.prozorro.gov.ua
prozorro-cli tender UA-2026-06-15-003439-a

# Full JSON by GUID without hyphens
prozorro-cli tender 5d2590ef8a1b455f8d09ceeae474b21f

# Full JSON by standard UUID
prozorro-cli tender 5d2590ef-8a1b-455f-8d09-ceeae474b21f

# Full JSON by tender page URL
prozorro-cli tender https://prozorro.gov.ua/tender/UA-2026-06-15-003439-a

# Full JSON by Public API URL
prozorro-cli tender https://public-api.prozorro.gov.ua/api/2.5/tenders/5d2590ef8a1b455f8d09ceeae474b21f

# Download all files from data.documents using a Public API URL
prozorro-cli documents https://public-api.prozorro.gov.ua/api/2.5/tenders/5d2590ef8a1b455f8d09ceeae474b21f --output /temp

# Download the same files using a UA-ID
prozorro-cli documents UA-2026-06-15-003439-a --output /temp
```

For a UA-ID or tender page URL, the CLI first retrieves the internal `id` from
the public `https://prozorro.gov.ua/api/tenders/<UA-ID>/summary` endpoint.
This step is skipped for GUIDs, UUIDs, and Public API URLs. The full JSON is
downloaded from
`https://public-api.prozorro.gov.ua/api/2.5/tenders/<id>`.

The `documents` command creates the directory specified by `--output` if it
does not exist, then downloads all files from `data.documents`. File names are
taken from `title`; duplicate names are not overwritten and receive suffixes
such as `(2)`, `(3)`, and so on.

<a id="development"></a>

## 🛠️ Development

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m prozorro_cli tender UA-2026-06-15-003439-a --guid
```

<a id="release"></a>

## 🚀 Release

1. Update `version` in `pyproject.toml` and `__version__` in
   `src/prozorro_cli/__init__.py`.
2. Create and publish a GitHub Release with a tag matching the version, for
   example `v0.1.0`.
3. GitHub Actions will run the tests, build the wheel and sdist, attach them to
   the Release, and publish the package to PyPI.

Publishing requires the `PYPI_API_TOKEN` GitHub Actions secret containing a
PyPI API token. The publishing job runs in the `pypi` GitHub environment.
