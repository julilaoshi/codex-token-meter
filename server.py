#!/usr/bin/env python3
"""Local-only token panel. No model calls, no third-party dependencies."""
import json, os, re, sqlite3, time, threading
from datetime import datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent
HOME = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).expanduser()
PORT = int(os.environ.get('TOKEN_PANEL_PORT', '8793'))


def display_title(row, names=None):
    # Metadata can contain the full first input, including attachment scaffolding.
    for raw in (row['name'], (names or {}).get(row['id']), row['title']):
        if not raw:
            continue
        text = raw.strip()
        if 'Files mentioned by the user' in text or 'in-app-browser-context' in text:
            parts = re.split(r'##\s*My request:\s*', text)
            if len(parts) < 2:
                continue
            text = parts[-1].strip()
        if not text or any(marker in text for marker in (
            '/Users/', '/var/', '/private/', 'codex-clipboard-',
            '<environment_context', '<system', '<image', 'Distinguish instructions',
            'AGENTS.md instructions', 'Files mentioned by the user')):
            continue
        text = re.sub(r'\s+', ' ', text).strip('# *\t')
        if text:
            return text[:77] + '…' if len(text) > 80 else text
    return '未命名任务 · ' + row['id'][:8]

def saved_names(home, ids):
    names = {}
    try:
        data = json.loads((home/'.codex-global-state.json').read_text())
        titles = data.get('thread-titles', {}).get('titles', {})
        names.update({i:t for i,t in titles.items() if i in ids and isinstance(t,str)})
    except (OSError, ValueError, AttributeError):
        pass
    try:
        with (home/'session_index.jsonl').open() as f:
            for line in f:
                try:
                    item=json.loads(line)
                    if item.get('id') in ids and isinstance(item.get('thread_name'),str) and item['thread_name'].strip():
                        names[item['id']]=item['thread_name']
                except (ValueError, AttributeError):
                    continue
    except OSError:
        pass
    return names

def select_cycle(cycles, period, now):
    # Latest observed reset is authoritative; do not extrapolate expired records.
    records=[x for x in cycles if x['observed'] <= now]
    if not records:return None
    latest=max(records,key=lambda x:x['observed'])
    if period == 'current':return latest
    older=[x for x in records if x['start'] < latest['start'] and x['observed'] < latest['observed']]
    if not older:return None
    previous=dict(max(older,key=lambda x:x['observed']))
    # A reset card can end a cycle before its originally scheduled expiry.
    previous['end']=min(previous['end'],latest['start'])
    return previous if previous['end'] > previous['start'] else None

class Tail:
    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self.inode = None
        self.active = False
        self.turn = None
        self.ended = 0
        self.total = None
        self.raw_total = None
        self.stamp = 0
        self.turn_base = None
        self.previous_turn = None
        self.current_turn_usage = 0
        self.week_events = {}
        self.cycle = None
        self.cycles = {}
        self.completed_turns = []

    def apply(self, d):
        if d.get('type') != 'event_msg':
            return
        p = d.get('payload', {})
        kind = p.get('type')
        if kind == 'task_started':
            if self.active and p.get('turn_id') == self.turn:
                return
            self.active, self.turn, self.ended = True, p.get('turn_id'), 0
            self.turn_base = self.total
            self.current_turn_usage = 0
        elif kind in ('task_complete', 'turn_aborted', 'task_aborted'):
            if not p.get('turn_id') or not self.turn or p['turn_id'] == self.turn:
                if self.active:
                    self.previous_turn = self.current_turn_usage if self.turn_base is not None else None
                self.active = False
                try:
                    self.ended = datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')).timestamp()
                    self.completed_turns.append((self.ended, self.previous_turn))
                except (KeyError, ValueError):
                    self.ended = 0
        elif kind == 'token_count':
            limits = p.get('rate_limits') or {}
            if limits.get('limit_id') in (None, 'codex'):
                for w in (limits.get('primary'), limits.get('secondary')):
                    if w and w.get('window_minutes') == 10080 and w.get('resets_at'):
                        try:
                            observed = datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')).timestamp()
                            self.cycle = {'start':w['resets_at']-604800, 'end':w['resets_at'], 'observed':observed}
                            self.cycles[self.cycle['end']] = self.cycle
                        except (KeyError, ValueError):
                            pass
            usage = (p.get('info') or {}).get('total_token_usage') or {}
            if isinstance(usage.get('total_tokens'), int):
                new_total = usage['total_tokens']
                delta = new_total - self.raw_total if self.raw_total is not None and new_total >= self.raw_total else new_total
                if self.active:
                    self.current_turn_usage += delta
                    if self.turn_base is None and self.total is None:
                        self.turn_base = 0
                self.total = (self.total or 0) + delta
                self.raw_total = new_total
                try:
                    stamp = datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')).timestamp()
                    key = (stamp, new_total)
                    self.week_events[key] = delta
                except (KeyError, ValueError):
                    pass

    def update(self):
        st = self.path.stat()
        if st.st_ino != self.inode or st.st_size < self.offset:
            self.__init__(self.path)
            self.inode = st.st_ino
        if st.st_size == self.offset:
            return
        with self.path.open('rb') as f:
            f.seek(self.offset)
            for line in f:
                if not line.endswith(b'\n'):
                    break  # Retry a partially written event next poll.
                self.offset += len(line)
                # Avoid decoding conversational messages/tool outputs.
                if b'"event_msg"' not in line[:180]:
                    continue
                if not any(x in line[:350] for x in (b'"task_started"', b'"task_complete"', b'"turn_aborted"', b'"task_aborted"', b'"token_count"')):
                    continue
                try:
                    self.apply(json.loads(line))
                except (ValueError, TypeError):
                    continue
        self.stamp = st.st_mtime

class Monitor:
    def __init__(self, home=HOME):
        self.home, self.tails = Path(home), {}
        self.lock = threading.Lock()
        self.cached, self.at = None, 0

    def snapshot(self, period="current"):
        with self.lock:
            now = time.time()
            if self.cached is not None and now-self.at < 2 and self.cached.get("period") == period:
                return self.cached
            candidates = sorted(self.home.glob('state_*.sqlite'), key=lambda p:int(p.stem.split('_')[-1]) if p.stem.split('_')[-1].isdigit() else -1)
            if not candidates:
                raise ValueError('Codex metadata not found')
            db = candidates[-1]
            with sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=2) as c:
                c.row_factory = sqlite3.Row
                rows = c.execute('SELECT id,rollout_path,title,name,cwd,source,archived FROM threads WHERE updated_at>? ORDER BY id', (int(now-22*86400),)).fetchall()
            loaded, failed, valid = [], 0, set()
            for row in rows:
                excluded = [Path(x).expanduser().resolve() for x in os.environ.get('TOKEN_METER_EXCLUDE', '').split(os.pathsep) if x]
                if any(Path(row['cwd']).resolve().is_relative_to(x) for x in excluded) or 'subagent' in row['source']:
                    continue
                path = Path(row['rollout_path'])
                try:
                    if not any(path.resolve().is_relative_to((self.home/folder).resolve()) for folder in ('sessions', 'archived_sessions')):
                        continue
                    valid.add(row['id'])
                    tail = self.tails.setdefault(row['id'], Tail(path))
                    if tail.path != path:
                        tail = self.tails[row['id']] = Tail(path)
                    tail.update()
                    loaded.append((row, tail))
                except OSError:
                    failed += 1
            names = saved_names(self.home, {row['id'] for row,_ in loaded})
            cycles = [x for _,t in loaded for x in t.cycles.values()]
            cycle = select_cycle(cycles, period, now)
            known = bool(cycle and (period == 'previous' or cycle['start'] <= now < cycle['end']))
            seen, total, tasks, ranking = set(), 0, [], []
            for row, tail in loaded:
                period_tokens = 0
                if known:
                    for key, value in tail.week_events.items():
                        if cycle['start'] <= key[0] < cycle['end'] and key[0] <= now and key not in seen:
                            seen.add(key)
                            period_tokens += value
                total += period_tokens
                running = period == 'current' and not row['archived'] and tail.active and now-tail.stamp < 1800
                item = {'id':row['id'], 'title':display_title(row, names),
                        'tokens':sum(v for k,v in tail.week_events.items() if k[0] < cycle['end']) if period == 'previous' and known else tail.total, 'status':'running' if running else 'idle',
                        'previous_turn_tokens':next((v for t,v in reversed(tail.completed_turns) if cycle['start'] <= t < cycle['end']), None) if period == 'previous' and known else tail.previous_turn,
                        'period_tokens':period_tokens if known else None}
                if running:
                    tasks.append(item)
                elif (period == 'previous' or not tail.active) and period_tokens > 0:
                    ranking.append(item)
            for item in tasks+ranking:
                item['period_percent'] = item['period_tokens']/total*100 if known and total and not failed else None
            ranking.sort(key=lambda x:(-x['period_tokens'], x['id']))
            self.tails = {k:v for k,v in self.tails.items() if k in valid}
            warning = '部分本地记录暂时无法读取' if failed else None
            if not known:
                warning = '未找到可核验的上周期记录，暂不计算历史用量' if period == 'previous' else '等待 Codex 写入当前周期信息；暂不计算占比和排行'
            self.cached = {'period':period, 'period_tokens':total if known else None, 'cycle':cycle,
                           'tasks':tasks, 'ranking':ranking[:5] if known and not failed else [],
                           'updated':now, 'warning':warning}
            self.at = now
            return self.cached

def demo_snapshot(period="current"):
    def item(name, total, period, previous, running=True):
        return {'id':name, 'title':name, 'tokens':total, 'period_tokens':period,
                'period_percent':period/10000000*100, 'previous_turn_tokens':previous,
                'status':'running' if running else 'idle'}
    result = {'tasks':[item('Design system / 设计系统',2340000,1800000,126000),
                      item('Documentation / 文档整理',860000,720000,42000)],
            'ranking':[item('Interface prototype / 界面原型',3200000,2270000,96000,False),
                       item('Data cleanup / 数据整理',1800000,1540000,78000,False),
                       item('Unit tests / 单元测试',1200000,930000,64000,False)],
            'cycle':{'start':0,'end':604800},'period_tokens':10000000,
            'warning':None,'demo':True,'updated':time.time(),'period':period}
    if period == 'previous':
        result['tasks']=[]
        result['cycle']={'start':-604800,'end':0}
    return result

MONITOR = Monitor()
DEMO = False
STOP_TOKEN = None
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get('Host', '')
        if host not in (f'127.0.0.1:{PORT}', f'localhost:{PORT}'):
            self.send_error(403)
            return
        if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}'):
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        status = 200
        if path == '/api/health':
            data = json.dumps({'app':'codex-token-meter','version':'1.0.3'}).encode()
            content_type = 'application/json; charset=utf-8'
        elif path == '/api/status':
            if self.headers.get('Sec-Fetch-Site') == 'cross-site':
                self.send_error(403)
                return
            try:
                period = parse_qs(urlsplit(self.path).query).get('period', ['current'])[0]
                if period not in ('current', 'previous'):
                    self.send_error(400);return
                payload = demo_snapshot(period) if DEMO else MONITOR.snapshot(period)
            except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
                status = 503
                payload = {'error':'本地统计暂不可用，请检查 Codex 数据文件。'}
            data = json.dumps(payload, ensure_ascii=False).encode()
            content_type = 'application/json; charset=utf-8'
        elif path in ('/', '/index.html'):
            data = (ROOT/'index.html').read_bytes()
            content_type = 'text/html; charset=utf-8'
        else:
            self.send_error(404)
            return
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'self'")
        self.end_headers()
        self.wfile.write(data)
    def do_POST(self):
        import secrets
        if self.path != '/api/stop' or not STOP_TOKEN or not secrets.compare_digest(self.headers.get('X-Token-Meter-Key', ''), STOP_TOKEN):
            self.send_error(403)
            return
        self.send_response(200)
        self.end_headers()
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    print(f'Token panel: http://127.0.0.1:{PORT}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
