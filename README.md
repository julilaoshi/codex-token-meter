# Codex Token Meter

**See where your Codex tokens go. Keep the dashboard small.**

[Quick install](#quick-install) · [中文说明](README.zh-CN.md) · [Star this project](https://github.com/julilaoshi/codex-token-meter)

Public v1.0.2 · Local macOS utility · Python 3.9+ · No third-party Python dependencies · No model calls

![Token Meter preview — fictional demonstration data](docs/demo.png)

*Every task name and number in this preview is fictional.*

## What you get

- Active tasks with a spinner, lifetime tokens and previous-turn usage.
- Your current Codex allowance period, discovered from local usage records.
- Token share for each task within that period, with a compact pie chart.
- Top five other completed tasks, ranked by tokens consumed in the same period.
- Automatic refresh every three seconds, sharp corners and readable numbers.

This is an independent community tool, not an OpenAI product. The interface currently uses Chinese labels and Chinese number units (万 = 10,000; 亿 = 100,000,000).

## Quick install

Requires macOS with Python 3.9+ and local Codex session records. No sudo, subscription credentials or API key is required. Review [install.sh](install.sh) before running it.

```sh
python3 -c 'import urllib.request, subprocess; subprocess.run(["sh"], input=urllib.request.urlopen("https://raw.githubusercontent.com/julilaoshi/codex-token-meter/v1.0.2/install.sh", timeout=30).read(), check=True)'
```

The installer fetches a fixed release, verifies its SHA-256 checksum, installs into your user directory and starts the local service. Click the printed localhost URL, or ask Codex to open it in its right-side browser panel. The panel is a browser tab attached to a task, not a global extension of the Codex interface.

**Prefer asking Codex? Copy this:**

```text
Install https://github.com/julilaoshi/codex-token-meter on this Mac.
Read its README and inspect install.sh first. Install the tagged release,
verify that the service responds, and open its printed local URL in the
right-side browser panel. Do not upload my local records or register a Skill.
```

Manual fallback: download and extract the release ZIP, then run `python3 meter.py install` in that directory.

## Everyday commands

```sh
python3 ~/.local/share/codex-token-meter/meter.py status
python3 ~/.local/share/codex-token-meter/meter.py start
python3 ~/.local/share/codex-token-meter/meter.py stop
python3 ~/.local/share/codex-token-meter/meter.py uninstall
```

Re-run the installer for a published version to update. No automatic updates or login startup are installed. Start it again after a restart. The service selects an available port starting at 8793; use the URL it prints. Closing the page stops polling; the lightweight service remains available.

## What the percentages mean

**Task tokens used during this period ÷ locally observed tokens used during this period.** This is not subscription allowance consumption, a bill, remaining context or a conversion from Pro 20× into tokens.

The cycle uses the latest `codex` seven-day limit record: reset time minus seven days to reset time. The interface displays dates in Beijing time. Missing or expired cycle data makes the percentage and ranking unavailable until Codex writes a fresh record. No artificial weekly budget is assumed.

Input, cached input and output follow Codex's cumulative token records. Snapshots are converted to increments; repeated timestamp/cumulative-count events are attributed once. A turn spans a user request and the model calls made before that turn ends or is cancelled. “Previous turn” does not mean the last model request.

## Privacy and limits

- Reads local task metadata and usage events; never modifies Codex files.
- No analytics, outbound requests or model calls during normal monitoring. Installation downloads code from GitHub; normal monitoring stays local.
- Binds only to loopback. The dashboard exposes local task titles to local clients; loopback is not a sandbox against other applications on your computer.
- No credentials or chat content are returned to the browser. Session lines are scanned to select usage events; no conversation archive is saved by this tool.
- Honors `CODEX_HOME`. Optionally set `TOKEN_METER_EXCLUDE` to a colon-separated list of private directories before starting. Matching task directories and descendants are excluded.
- Only locally available records are counted. Child-agent sessions are excluded. Archived tasks can appear in the ranking. Cloud-only work and other computers are not counted.
- Running includes waiting for tools or approval. Sessions with no log changes for 30 minutes are hidden; long quiet work may also be hidden until its next log update. Stale active tasks are not reclassified as completed ranking entries.
- Recent metadata discovery covers eight days. Missing records, forks and changed log schemas may limit attribution. These are observed local counts, not an official billing audit.
- Local Codex storage is an implementation detail. Unsupported schemas produce an unavailable state rather than invented totals.

## Development and demo

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_*.py'
python3 meter.py start --demo --home /tmp/token-meter-demo --port 8893
python3 meter.py stop --home /tmp/token-meter-demo
```

Demo mode uses hard-coded fictional data and does not read Codex records. Keep real usage screenshots and session data out of contributions. See [CONTRIBUTING](CONTRIBUTING.md).

## Share it

If this helps, [star the repository](https://github.com/julilaoshi/codex-token-meter) or share its link. [Launch copy](docs/launch-copy.md) is available in English and Chinese. No social account connection is required.

[Follow the repository owner on GitHub](https://github.com/julilaoshi) for updates.

## License

[MIT](LICENSE). See [brand notice](BRAND_NOTICE.md) for the independent-project identity and trademark boundary.
