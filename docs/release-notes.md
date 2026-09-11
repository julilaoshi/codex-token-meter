# v1.0.2 — Codex Token Meter

A compact local dashboard for Codex usage on macOS.

- Active tasks with animated indicators, cumulative tokens and previous-turn usage.
- Current-period token shares and top-five completed-task rankings.
- Three-second refresh with no model calls or runtime telemetry.
- Fixed-version installer with checksum verification, local service controls and safe installation ownership checks.
- Fictional-data demo, bilingual documentation and contribution guides.

Requires Python 3.9+. The interface currently uses Chinese labels. Counts reflect available local records, not billing or subscription allowance attribution. Local schema changes may require a parser update; missing/expired cycle metadata is shown as unavailable.

Install from the README, or download the ZIP and run `python3 meter.py install`. SHA256SUMS covers the attached distribution archive.

Installation update: fetches fixed-tag source files with per-file SHA-256 verification, avoiding the separate Release asset download host. The ZIP remains available for manual installation.

The recommended one-line entry uses Python HTTPS directly, matching the sole required runtime and avoiding curl-specific proxy behavior.
