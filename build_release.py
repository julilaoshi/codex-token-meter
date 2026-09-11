"""Build a release ZIP from explicit public files, never from a workspace glob."""
import hashlib, zipfile
from pathlib import Path
FILES=('checksums.json','meter.py','server.py','index.html','install.sh','LICENSE','README.md','README.zh-CN.md',
       'CONTRIBUTING.md','CONTRIBUTING.zh-CN.md','BRAND_NOTICE.md','PUBLIC_RELEASE_CHECKLIST.md',
       'test_monitor.py','test_lifecycle.py','build_release.py','docs/demo.png','docs/launch-copy.md','docs/release-notes.md')
if __name__=='__main__':
    root=Path(__file__).resolve().parent;out=root/'dist';out.mkdir(exist_ok=True)
    archive=out/'codex-token-meter-1.0.2.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            p=root/name
            if p.is_symlink() or not p.is_file():raise SystemExit('Unexpected release input: '+name)
            info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o100755 if name=='install.sh' else 0o100644)<<16
            z.writestr(info,p.read_bytes())
    (out/'SHA256SUMS').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    print('Built checksummed release archive.')
