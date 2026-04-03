Create a Cargo.toml for a Rust workspace with a CLI app and two library crates.

Include:
- Workspace members: cli, core, utils
- Package metadata for the CLI: name "dataforge", version, edition, description, license, authors, repository
- Dependencies: clap, serde, tokio, anyhow, tracing, reqwest
- Dev-dependencies: criterion, tempfile, mockito
- Features: default, full, minimal
- Binary and library targets
- Profile settings for release (LTO, strip)

Use section IDs: package, dependencies, workspace

Use AAP section markers to delineate each major code block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.