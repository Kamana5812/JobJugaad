"""Prepare a disposable loopback CI database; never alters a hosted database."""
import os
import psycopg2
connection=psycopg2.connect(os.environ['CI_ADMIN_DATABASE_URL'])
if connection.info.host not in ('127.0.0.1','localhost'): raise RuntimeError('Loopback CI database required.')
connection.autocommit=True
with connection.cursor() as cursor:
    cursor.execute("CREATE ROLE jobjugaad_app LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD 'ci-only-disposable-password'")
    cursor.execute('CREATE DATABASE jobjugaad_test_utf8 OWNER jobjugaad_app')
    cursor.execute('CREATE DATABASE jobjugaad_restore_ci OWNER jobjugaad_app')
connection.close()
print('Disposable CI databases prepared with a non-bypass runtime role.')

