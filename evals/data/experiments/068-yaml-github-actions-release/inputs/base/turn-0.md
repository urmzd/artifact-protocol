Create a GitHub Actions release workflow for a Rust CLI tool.

Include:
- Trigger on tag push (v*)
- Build matrix: Linux (x86_64, aarch64), macOS (x86_64, aarch64), Windows (x86_64)
- Cross-compilation setup, cargo build --release
- Create GitHub Release with changelog from git log
- Upload binary artifacts for each platform
- Publish to crates.io
- Notification step (Slack webhook)
