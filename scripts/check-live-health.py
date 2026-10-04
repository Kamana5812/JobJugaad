"""Public point-in-time health and isolation check; no secrets, tenant reads or messages."""
import json
import time
from urllib.request import urlopen
for attempt in range(2):
    try:
        with urlopen('https://jobjugaad-api.onrender.com/health',timeout=65) as response: data=json.load(response)
        isolation=data.get('isolation',{})
        assert data.get('database')=='connected' and isolation.get('status')=='verified' and isolation.get('runtime_role_restricted') is True
        assert len(isolation.get('tables', [])) == 34
        assert all(r['status']=='verified' and r['enabled'] and r['forced'] and r['read_write_scoped'] for r in isolation['tables'])
        assert data.get('placement_model')=='ready' and data.get('btech_model')=='ready'
        with urlopen('https://jobjugaad.vercel.app/',timeout=35) as response: assert response.status==200 and b'<html' in response.read(2000).lower()
        print(json.dumps({'status':'healthy','tenant_policies':len(isolation['tables']),'note':'Not an uptime or latency benchmark.'}));break
    except Exception as error:
        if attempt==1:
            print(json.dumps({'status':'failed','error_type':type(error).__name__}));raise SystemExit(1)
        time.sleep(5)
