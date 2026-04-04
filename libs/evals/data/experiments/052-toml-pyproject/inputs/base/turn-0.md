Create a pyproject.toml for a Python library called "dataforge" for data transformation.

Include:
- Project metadata: name, version, description, authors, license, requires-python, classifiers
- Dependencies: pandas, pydantic, click, rich, httpx
- Optional dependencies: dev (pytest, ruff, mypy), docs (mkdocs, mkdocstrings)
- Scripts/entry points: dataforge CLI command
- Tool configs: ruff (rules, line-length), mypy (strict), pytest (testpaths, markers)
- Build system: hatchling
