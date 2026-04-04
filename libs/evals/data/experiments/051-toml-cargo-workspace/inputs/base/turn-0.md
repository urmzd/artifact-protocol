Create a Cargo.toml for a Rust workspace with a CLI app and two library crates.

Include:
- Workspace members: cli, core, utils
- Package metadata for the CLI: name "dataforge", version, edition, description, license, authors, repository
- Dependencies: clap, serde, tokio, anyhow, tracing, reqwest
- Dev-dependencies: criterion, tempfile, mockito
- Features: default, full, minimal
- Binary and library targets
- Profile settings for release (LTO, strip)
