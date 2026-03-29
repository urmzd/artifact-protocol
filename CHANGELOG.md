# Changelog

## 0.1.0 (2026-03-29)

### Features

- add OTEL tracing and metrics; rename python/ to tools/ ([4341bf3](https://github.com/urmzd/artifact-generator/commit/4341bf38d12f501b080499823f07308e330e6407))
- replace axum web server with headless Chrome PDF renderer ([20027cd](https://github.com/urmzd/artifact-generator/commit/20027cd6c720e4f84badecdbea67eb735ccdbf1b))

### Bug Fixes

- use Ubuntu 24.04 compatible package names for Chrome deps ([26ac3b1](https://github.com/urmzd/artifact-generator/commit/26ac3b13963915f104a0033ed654b503dae41df5))
- install Chrome shared libs and poll for PDF instead of fixed sleep ([bdb9c33](https://github.com/urmzd/artifact-generator/commit/bdb9c33c8b2e2165e33dff995c97947da3b18243))
- disable Chrome sandbox in CI and install chromium for PDF test ([e76497f](https://github.com/urmzd/artifact-generator/commit/e76497ffd0e77af33d5811ac3396d734519055c8))

### Documentation

- add agent skill following agentskills.io spec ([ba278bd](https://github.com/urmzd/artifact-generator/commit/ba278bde85fd412e83f47c201ac2d8790716e5a7))
- update README for headless Chrome PDF workflow ([13134d9](https://github.com/urmzd/artifact-generator/commit/13134d91a6f689e7d0ac6647c52114788e9e95b0))
- update repo URL to https://github.com/urmzd/artifact-generator ([d88cacd](https://github.com/urmzd/artifact-generator/commit/d88cacd4238ee65303a91f26c1c933fbfb0a4a5b))

### Refactoring

- restructure Python scripts into proper package ([157b31e](https://github.com/urmzd/artifact-generator/commit/157b31ef72de0d3d97ec500a9c385a45b194c9f6))

### Miscellaneous

- standardize CI/CD — add sr.yaml, workflow_call trigger, release workflow ([cd924d7](https://github.com/urmzd/artifact-generator/commit/cd924d7a4b7288687ba4e77f0c43176b80ac1fdb))
- update justfile and CI for PDF-based workflow ([be91725](https://github.com/urmzd/artifact-generator/commit/be917256ae1e4872a43cbbd421cd4c6491598d42))
- add GitHub Actions workflow (Rust build/test + Python benchmarks) ([22ff1b9](https://github.com/urmzd/artifact-generator/commit/22ff1b9486b3358d1834f07eae5310324113c75b))
