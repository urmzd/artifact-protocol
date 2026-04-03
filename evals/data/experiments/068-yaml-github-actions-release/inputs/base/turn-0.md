Create a GitHub Actions release workflow for a Rust CLI tool.

Include:
- Trigger on tag push (v*)
- Build matrix: Linux (x86_64, aarch64), macOS (x86_64, aarch64), Windows (x86_64)
- Cross-compilation setup, cargo build --release
- Create GitHub Release with changelog from git log
- Upload binary artifacts for each platform
- Publish to crates.io
- Notification step (Slack webhook)

Use section IDs: triggers, build-matrix, publish, notifications

Use AAP section markers to delineate each major block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.