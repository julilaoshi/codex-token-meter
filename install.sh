#!/bin/sh
# Fixed-version installation with per-file checksums. No sudo or model calls.
set -eu
command -v python3 >/dev/null 2>&1 || { echo 'Python 3.9+ is required.' >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,9), "Python 3.9+ required"'
task_tmp=$(mktemp -d)
trap 'rm -rf "$task_tmp"' EXIT HUP INT TERM
python3 - "$task_tmp" <<'PY'
import concurrent.futures,hashlib,json,pathlib,sys,urllib.request
root=pathlib.Path(sys.argv[1]);base='https://raw.githubusercontent.com/julilaoshi/codex-token-meter/v1.0.1/'
files=('meter.py','server.py','index.html','LICENSE','README.md','README.zh-CN.md')
def fetch(name):
 for attempt in range(2):
  try:return urllib.request.urlopen(base+name,timeout=25).read()
  except OSError:
   if attempt:raise
manifest=json.loads(fetch('checksums.json'))
if set(manifest)!=set(files):raise SystemExit('Unexpected install manifest')
def download(name):
 data=fetch(name)
 if hashlib.sha256(data).hexdigest()!=manifest[name]:raise SystemExit('Checksum mismatch: '+name)
 (root/name).write_bytes(data)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:list(executor.map(download,files))
print('Verified fixed-version source files.')
PY
python3 "$task_tmp/meter.py" install "$@"
