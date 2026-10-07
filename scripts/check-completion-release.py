"""Public-only deployment evidence; no privileged sessions or hiring mutations."""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import httpx

API = 'https://jobjugaad-api.onrender.com'
FRONT = 'https://jobjugaad.vercel.app'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--version', default='0.19.0')
    parser.add_argument('--nlp', action='store_true')
    args = parser.parse_args()
    result = {'source_commit': args.commit, 'checked_at': datetime.now(timezone.utc).isoformat(),
        'checks': [], 'authenticated_walkthrough': False, 'emails_sent': False, 'production_records_changed': False}
    def check(name, value):
        result['checks'].append({'check': name, 'passed': bool(value)})
    with httpx.Client(timeout=45, follow_redirects=True) as client:
        spec = client.get(API + '/openapi.json').json()
        check('API ' + args.version, spec['info']['version'] == args.version)
        health = client.get(API + '/health').json()
        isolation = health.get('isolation', {})
        result['policies'] = isolation.get('tables', [])
        check('36 ENABLE/FORCE read-write scoped policies and restricted role',
            health.get('database') == 'connected' and isolation.get('status') == 'verified'
            and isolation.get('runtime_role_restricted') is True and len(result['policies']) == 36
            and all(row['enabled'] and row['forced'] and row['read_write_scoped']
                and row['status'] == 'verified' for row in result['policies']))
        check('public-data models still ready', health.get('placement_model') == 'ready' and health.get('btech_model') == 'ready')
        routes = {'/admin/students': 'get', '/admin/students/1/profile': 'get',
            '/admin/jobs': 'get', '/admin/jobs/1/matching': 'post', '/admin/jobs/1/matches': 'get',
            '/admin/jobs/1/matches/1/override': 'post', '/admin/jobs/1/applications': 'get',
            '/admin/jobs/1/applications/1/profile': 'get', '/admin/jobs/1/state': 'post',
            '/admin/analytics/demand': 'get', '/admin/reminders/run': 'post',
            '/recruiters/analytics/demand': 'get', '/recruiters/jobs/description/review': 'post'}
        if args.nlp:
            routes.update({'/students/1/resume/suggestions': 'get', '/students/1/semantic-match/1': 'post',
                '/recruiters/jobs/1/applications/1/semantic': 'post', '/admin/jobs/1/applications/1/semantic': 'post'})
        for route, method in routes.items():
            documented = re.sub(r'/1(?=/|$)', '/{id}', route)
            available = any(re.sub(r'\{[^}]+\}', '{id}', path) == documented
                and method in operations for path, operations in spec['paths'].items())
            check('documented ' + method + ' ' + route, available)
            response = client.request(method.upper(), API + route, json={} if method == 'post' else None)
            check('anonymous denied ' + route, response.status_code == 401)
        for origin, allowed in ((FRONT, True), (FRONT + '.evil.example', False)):
            response = client.options(API + '/admin/jobs', headers={'Origin': origin,
                'Access-Control-Request-Method': 'GET', 'Access-Control-Request-Headers': 'authorization'})
            check('exact CORS ' + origin, response.headers.get('access-control-allow-origin') == FRONT
                if allowed else 'access-control-allow-origin' not in response.headers)
        response = client.get(FRONT)
        check('frontend served', response.status_code == 200)
        for header, expected in (('x-frame-options', 'DENY'), ('x-content-type-options', 'nosniff'), ('referrer-policy', 'no-referrer')):
            check('browser header ' + header, response.headers.get(header) == expected)
        check('CSP restricts scripts and framing', "script-src 'self'" in response.headers.get('content-security-policy', '')
            and "frame-ancestors 'none'" in response.headers.get('content-security-policy', ''))
        entry = re.search(r'src="(/assets/[^" ]+\.js)"', response.text).group(1)
        result['frontend_entry'] = entry
        bundle = client.get(FRONT + entry).text
        check('production API configured', API in bundle)
        if args.nlp:
            check('semantic evidence controls served', 'Compare semantic evidence' in bundle and 'does not alter eligibility' in bundle)
            check('review-only resume suggestions served', 'Preview extracted fields' in bundle and 'Nothing is selected or saved automatically' in bundle)
        check('new recruiter/profile controls served', 'Reopen drive' in bundle and 'Separate lexical comparison' in bundle)
        admin = re.search(r'AdminPage-[\w-]+\.js', bundle)
        check('admin chunk referenced', admin is not None)
        if admin:
            result['frontend_admin'] = '/assets/' + admin.group(0)
            content = client.get(FRONT + result['frontend_admin']).text
            check('college directory and drive review served', 'College student directory' in content and 'Run explained matching' in content + bundle)
        statuses = client.get('https://api.github.com/repos/Kamana5812/JobJugaad/commits/'
            + args.commit + '/status', headers={'User-Agent': 'JobJugaad-release-check'}).json()
        check('Vercel commit deployment successful', any(row.get('context') == 'Vercel' and row.get('state') == 'success'
            for row in statuses.get('statuses', [])))
    result['passed'] = sum(row['passed'] for row in result['checks'])
    result['total'] = len(result['checks'])
    result['all_passed'] = result['passed'] == result['total']
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('passed', 'total', 'all_passed', 'frontend_entry')}))
    return 0 if result['all_passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
