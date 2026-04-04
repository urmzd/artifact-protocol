Create a git pre-commit hook script that runs linting and formatting checks.
Check for: trailing whitespace, large files (>5MB), secrets/API keys, then run the project's linter.
Exit with non-zero on failure.
