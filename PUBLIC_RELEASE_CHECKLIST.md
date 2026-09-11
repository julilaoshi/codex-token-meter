# v1.0.2 release checks

- [x] New standalone source repository; no inherited private history.
- [x] English and Chinese README and contribution guides.
- [x] MIT license and independent-project brand notice.
- [x] Fictional demo mode and screenshot; no real account or usage data.
- [x] Local-only HTTP server; no runtime model calls or analytics.
- [x] Tests: lifecycle, cycles, ranking, completion, partial logs, counter increments.
- [x] Install, repeated start, port collision, update, stop and uninstall tested in temporary directories.
- [x] Fixed-tag installer verifies each installed file against a SHA-256 manifest.

Release artifacts are built from an explicit allowlist. Generated state, runtime logs, credentials, caches and developer backups are excluded. The commit author uses a GitHub noreply address. Runtime statistics remain local and are not included in the distribution.

The public tagged installer has been downloaded and executed in an isolated demo installation. Python HTTPS bootstrap avoids an extra curl dependency. Local-only usage counts are not subscription quota or billing estimates. Compatibility is initially limited to macOS with Python 3.9+; the UI currently uses Chinese labels.
