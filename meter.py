#!/usr/bin/env python3
"""Dependency-free lifecycle commands for Codex Token Meter."""
import argparse, json, os, secrets, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

VERSION = '1.0.3'
FILES = ('meter.py', 'server.py', 'index.html', 'LICENSE', 'README.md', 'README.zh-CN.md')
MARKER = 'codex-token-meter-owned-v1'

def request(state, stop=False):
    url = 'http://127.0.0.1:%s/api/%s' % (state['port'], 'stop' if stop else 'health')
    req = urllib.request.Request(url, method='POST' if stop else 'GET')
    if stop: req.add_header('X-Token-Meter-Key', state['key'])
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=10) as r:
        data = r.read()
        if not stop and json.loads(data).get('app') != 'codex-token-meter':
            raise OSError('Port belongs to a different service')
        return data

def state_path(home): return home/'state.json'
def read_state(home):
    try:return json.loads(state_path(home).read_text())
    except (OSError, ValueError):return None

def stop(home):
    state=read_state(home)
    if not state:return
    try:request(state, True)
    except OSError:return
    for _ in range(50):
        try:request(state)
        except OSError:
            if read_state(home) != state:
                return
        time.sleep(.1)
    raise RuntimeError('Server did not stop; installation unchanged.')

def serve(args, home):
    import server
    from http.server import ThreadingHTTPServer
    server.DEMO=args.demo
    server.STOP_TOKEN=secrets.token_urlsafe(32)
    httpd=None
    for port in range(args.port, min(args.port+20,65536)):
        try:httpd=ThreadingHTTPServer(('127.0.0.1',port),server.Handler);break
        except OSError:continue
    if httpd is None:raise RuntimeError('No available local port.')
    server.PORT=port
    state={'port':port,'key':server.STOP_TOKEN,'pid':os.getpid(),'version':VERSION,'demo':args.demo}
    tmp=home/'state.tmp'
    with os.fdopen(os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),'w') as f:json.dump(state,f)
    tmp.replace(state_path(home))
    try:httpd.serve_forever()
    finally:
        httpd.server_close()
        if read_state(home)==state:state_path(home).unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser(description='Codex Token Meter: local only, no model calls.')
    p.add_argument('command',choices=['install','start','status','stop','uninstall','serve'])
    p.add_argument('--home',type=Path,default=Path.home()/'.local/share/codex-token-meter')
    p.add_argument('--port',type=int,default=8793)
    p.add_argument('--demo',action='store_true',help='Use fictional data, never read Codex files.')
    args=p.parse_args();home=args.home.expanduser()
    if home.is_symlink():raise RuntimeError('Refusing a symlink installation directory.')
    home=home.resolve()
    if args.command=='install':
        if home.exists() and (not (home/'.owned').exists() or (home/'.owned').read_text()!=MARKER):
            raise RuntimeError('Destination is not owned by Token Meter; choose an empty path.')
        source=Path(__file__).resolve().parent
        if source==home:raise RuntimeError('Run install from a downloaded release, not the installed directory.')
        for name in FILES:
            if not (source/name).is_file():raise RuntimeError('Release file missing: '+name)
        stop(home)
        home.mkdir(parents=True,exist_ok=True,mode=0o700)
        (home/'.owned').write_text(MARKER)
        for name in FILES:shutil.copyfile(source/name,home/name)
        print('Installed '+VERSION+'. Starting local panel…')
        subprocess.run([sys.executable,str(home/'meter.py'),'start','--home',str(home),'--port',str(args.port)]+(['--demo'] if args.demo else []),check=True)
        return
    if args.command=='serve':
        home.mkdir(parents=True,exist_ok=True,mode=0o700);serve(args,home);return
    if args.command=='stop':stop(home);print('Stopped.');return
    if args.command=='uninstall':
        if not (home/'.owned').is_file() or (home/'.owned').read_text()!=MARKER:
            raise RuntimeError('Refusing to remove an unrecognized directory.')
        permitted=set(FILES)|{'.owned','state.json','state.tmp','server.log','.start.lock','__pycache__'}
        if any(x.name not in permitted for x in home.iterdir()):
            raise RuntimeError('Unexpected files found; inspect the installation before uninstalling.')
        stop(home);shutil.rmtree(home);print('Uninstalled. Codex data was not modified.');return
    state=read_state(home)
    if state:
        try:
            request(state);print('http://127.0.0.1:%s/'%state['port']);return
        except OSError:pass
    if args.command=='status':print('Not running.');return
    home.mkdir(parents=True,exist_ok=True,mode=0o700)
    # Serialize concurrent starts without third-party dependencies.
    import fcntl
    with (home/'.start.lock').open('a') as lock, (home/'server.log').open('ab') as log:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=read_state(home)
        if state:
            try:request(state);print('http://127.0.0.1:%s/'%state['port']);return
            except OSError:pass
        proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'serve','--home',str(home),'--port',str(args.port)]+(['--demo'] if args.demo else []),stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        for _ in range(100):
            state=read_state(home)
            if state and state.get('pid')==proc.pid:
                try:request(state);print('http://127.0.0.1:%s/'%state['port']);return
                except OSError:pass
            if proc.poll() is not None:break
            time.sleep(.1)
    raise RuntimeError('Could not start; inspect the local installation log.')

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError,subprocess.CalledProcessError) as e:
        print('Token Meter: '+str(e),file=sys.stderr);sys.exit(1)
