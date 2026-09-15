# Unreleased — Period history and task names

- Add current/previous account-period switching and historical top-five usage ranking.
- Read saved Codex names from database, session index and legacy desktop metadata; filter attachment scaffolding.
- Refresh locally observed reset dates, including early resets, and truncate the preceding period at the new boundary.
- Keep previous-period cumulative totals and last completed turn within the selected historical boundaries.
- Expand metadata discovery to 22 days. Missing/expired records remain unavailable rather than fabricated.
- Keep manual startup, stop and uninstall. No login startup is installed.

The service needs Codex to write the new reset information locally before it can detect a reset. No live account API or model calls are added. Tagged installer and latest Release remain v1.0.3 until a new release is published.

# v1.0.3 — Four usage metrics

- Show lifetime usage, current-period usage, period token share and previous-turn usage together for every task, including rankings.
- Preserve lifetime totals across resets of the source token counter.
- Adapt the four-metric layout to narrow panels without overlapping values.
- Refresh the fictional demo screenshot and installation checksums.

macOS and Python 3.9+. Period shares describe observed local token usage, not subscription allowance consumption. Monitoring does not call a model. Existing users can rerun the tagged installer in the README to update.
