import json, os, subprocess, sys, tempfile, unittest, urllib.error, urllib.request
from pathlib import Path

class LifecycleTests(unittest.TestCase):
    def test_install_repeat_collision_stop_and_uninstall(self):
        root=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)/'installation';other=Path(tmp)/'other'
            def cmd(action,target=home,*extra):
                return subprocess.run([sys.executable,str(root/'meter.py'),action,'--home',str(target),'--port','8913',*extra],check=True,capture_output=True,text=True).stdout
            try:
                cmd('install',home,'--demo')
                first=json.loads((home/'state.json').read_text())
                cmd('start',home,'--demo')
                self.assertEqual(first,json.loads((home/'state.json').read_text()))
                cmd('start',other,'--demo')
                second=json.loads((other/'state.json').read_text())
                self.assertNotEqual(first['port'],second['port'])
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                url=f"http://127.0.0.1:{first['port']}"
                data=json.loads(opener.open(url+'/api/status').read())
                self.assertTrue(data['demo']);self.assertEqual(len(data['tasks']),2)
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    opener.open(urllib.request.Request(url+'/api/stop',method='POST'))
                self.assertEqual(denied.exception.code,403)
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    opener.open(urllib.request.Request(url+'/api/status',headers={'Origin':'https://example.org'}))
                self.assertEqual(denied.exception.code,403)
                cmd('install',home,'--demo')
                self.assertNotEqual(first['key'],json.loads((home/'state.json').read_text())['key'])
                cmd('uninstall');self.assertFalse(home.exists())
            finally:
                for target in (home,other):
                    subprocess.run([sys.executable,str(root/'meter.py'),'stop','--home',str(target)],capture_output=True)

if __name__=='__main__':unittest.main()
