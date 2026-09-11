import json, tempfile, unittest, sqlite3, time
from pathlib import Path
from unittest.mock import patch
from server import Tail, Monitor

class MonitorTests(unittest.TestCase):
    def test_incremental_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'events.jsonl';p.touch();tail=Tail(p)
            def add(kind, **kw):
                with p.open('a') as f:f.write(json.dumps({'type':'event_msg','timestamp':'2026-09-11T15:00:00Z','payload':{'type':kind,**kw}})+'\n')
                tail.update()
            add('task_started',turn_id='a');self.assertTrue(tail.active)
            add('token_count',info={'total_token_usage':{'total_tokens':100}})
            add('token_count',info={'total_token_usage':{'total_tokens':150}})
            self.assertEqual(tail.total,150)
            add('task_complete',turn_id='old');self.assertTrue(tail.active)
            add('task_complete',turn_id='a');self.assertFalse(tail.active)
            self.assertGreater(tail.ended,0)
            add('task_started',turn_id='b');add('turn_aborted');self.assertFalse(tail.active)
            record=json.dumps({'type':'event_msg','payload':{'type':'task_started','turn_id':'c'}})
            with p.open('a') as f:f.write(record[:20])
            tail.update();self.assertFalse(tail.active)
            with p.open('a') as f:f.write(record[20:]+'\n')
            tail.update();self.assertTrue(tail.active)
            p.write_text('');tail.update();self.assertFalse(tail.active)

    def test_previous_turn_and_week_delta(self):
        tail=Tail('/tmp/not-read')
        def event(kind, stamp, **kw):
            tail.apply({'type':'event_msg','timestamp':stamp,'payload':{'type':kind,**kw}})
        event('token_count','2026-09-06T23:00:00+08:00',info={'total_token_usage':{'total_tokens':1000}})
        event('task_started','2026-09-07T01:00:00+08:00',turn_id='a')
        event('token_count','2026-09-07T01:01:00+08:00',info={'total_token_usage':{'total_tokens':1100}})
        event('token_count','2026-09-07T01:02:00+08:00',info={'total_token_usage':{'total_tokens':1300}})
        event('task_complete','2026-09-07T01:03:00+08:00',turn_id='a')
        self.assertEqual(tail.previous_turn,300)
        event('task_started','2026-09-07T01:04:00+08:00',turn_id='b')
        event('token_count','2026-09-07T01:05:00+08:00',info={'total_token_usage':{'total_tokens':1400}})
        self.assertEqual(tail.previous_turn,300)
        self.assertEqual(tail.current_turn_usage,100)
        from datetime import datetime
        cutoff=datetime.fromisoformat('2026-09-07T00:00:00+08:00').timestamp()
        self.assertEqual(sum(v for k,v in tail.week_events.items() if k[0]>=cutoff),400)

    def test_completion_removal_and_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sessions').mkdir();p=root/'sessions'/'test.jsonl'
            now=time.time()
            from datetime import datetime, timezone
            stamp=datetime.fromtimestamp(now,timezone.utc).isoformat()
            p.write_text(json.dumps({'type':'event_msg','timestamp':stamp,'payload':{'type':'task_complete'}})+'\n')
            with sqlite3.connect(root/'state_5.sqlite') as c:
                c.execute('CREATE TABLE threads(id,title,name,cwd,source,rollout_path,archived,updated_at)')
                c.execute('INSERT INTO threads VALUES(?,?,?,?,?,?,?,?)',('a','Test',None,'/tmp/work','cli',str(p),0,now))
                c.execute('INSERT INTO threads VALUES(?,?,?,?,?,?,?,?)',('b','Private',None,'/tmp/excluded-demo','cli',str(p),0,now))
            m=Monitor(root)
            self.assertEqual(m.snapshot()['tasks'],[])
            with patch('server.time.time',return_value=now+10):self.assertEqual(m.snapshot()['tasks'],[])

class RankingTests(unittest.TestCase):
    def test_cycle_ranking_excludes_running_and_limits_to_five(self):
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'sessions').mkdir();now=time.time()
            with sqlite3.connect(root/'state_5.sqlite') as c:
                c.execute('CREATE TABLE threads(id,title,name,cwd,source,rollout_path,archived,updated_at)')
                for i in range(8):
                    p=root/'sessions'/f'{i}.jsonl'
                    def ev(kind, seconds, **kw):
                        return json.dumps({'type':'event_msg','timestamp':datetime.fromtimestamp(now+seconds,timezone.utc).isoformat(),'payload':{'type':kind,**kw}})+'\n'
                    # Large pre-cycle baseline must not affect ranking.
                    lines=ev('token_count',-604900,info={'total_token_usage':{'total_tokens':100000}})
                    lines+=ev('task_started',-20,turn_id='a')
                    lines+=ev('token_count',-10-i,info={'total_token_usage':{'total_tokens':100000+(i+1)*100}},rate_limits={'limit_id':'codex','primary':{'window_minutes':10080,'resets_at':now+100}})
                    if i!=7:lines+=ev('task_complete',-1,turn_id='a')
                    p.write_text(lines)
                    c.execute('INSERT INTO threads VALUES(?,?,?,?,?,?,?,?)',(str(i),f'Task {i}',None,'/tmp/work','cli',str(p),0,now))
            d=Monitor(root).snapshot()
            self.assertEqual([t['id'] for t in d['tasks']],['7'])
            self.assertEqual([t['id'] for t in d['ranking']],['6','5','4','3','2'])
            self.assertEqual(d['period_tokens'],3600)
            self.assertAlmostEqual(d['tasks'][0]['period_percent'],800/3600*100)
            self.assertEqual(d['ranking'][0]['period_tokens'],700)
            self.assertAlmostEqual(d['cycle']['end'],now+100)

if __name__=='__main__':unittest.main()
