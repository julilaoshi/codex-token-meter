#!/bin/sh
# Install a fixed, checksummed release. No sudo, no model calls.
set -eu
command -v python3 >/dev/null 2>&1 || { echo 'Python 3.9+ is required.' >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,9), "Python 3.9+ required"'
task_tmp=$(mktemp -d)
trap 'rm -rf "$task_tmp"' EXIT HUP INT TERM
base=https://github.com/julilaoshi/codex-token-meter/releases/download/v1.0.0
curl -fLsS "$base/codex-token-meter-1.0.0.zip" -o "$task_tmp/package.zip"
curl -fLsS "$base/SHA256SUMS" -o "$task_tmp/SHA256SUMS"
python3 - "$task_tmp" <<'PY'
import hashlib,pathlib,sys,zipfile
root=pathlib.Path(sys.argv[1]);archive=root/'package.zip'
expected=[line.split()[0] for line in (root/'SHA256SUMS').read_text().splitlines() if line.split()[-1]=='codex-token-meter-1.0.0.zip']
if len(expected)!=1 or hashlib.sha256(archive.read_bytes()).hexdigest()!=expected[0]:raise SystemExit('Checksum mismatch')
with zipfile.ZipFile(archive) as z:
 for item in z.infolist():
  p=pathlib.PurePosixPath(item.filename)
  if p.is_absolute() or '..' in p.parts or (item.external_attr>>16)&0o170000==0o120000:raise SystemExit('Unsafe archive path')
 z.extractall(root/'source')
PY
python3 "$task_tmp/source/meter.py" install
