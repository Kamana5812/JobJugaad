"""Cutover gate prevents handler side effects and retains the exact CORS boundary."""
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from operations.maintenance import MigrationMaintenanceMiddleware


class MigrationMaintenanceTests(unittest.TestCase):
    def setUp(self):
        app=FastAPI();self.calls=[]
        @app.get('/health')
        def health():
            return {'status':'ok'}
        @app.api_route('/records',methods=['GET','POST'])
        def records():
            self.calls.append('called')
            return {'status':'recorded'}
        app.add_middleware(MigrationMaintenanceMiddleware)
        app.add_middleware(CORSMiddleware,allow_origins=['https://jobjugaad.vercel.app'],allow_methods=['GET','POST','OPTIONS'])
        self.client=TestClient(app)

    def test_enabled_blocks_reads_and_writes_without_handler_side_effects(self):
        with patch.dict('os.environ',{'MIGRATION_MAINTENANCE':'yes'}):
            for method in ('get','post'):
                response=getattr(self.client,method)('/records',headers={'Origin':'https://jobjugaad.vercel.app'})
                self.assertEqual(response.status_code,503)
                self.assertEqual(response.headers['retry-after'],'60')
                self.assertEqual(response.headers['access-control-allow-origin'],'https://jobjugaad.vercel.app')
            self.assertEqual(self.calls,[])
            self.assertEqual(self.client.get('/health').status_code,200)
            response=self.client.get('/records',headers={'Origin':'https://untrusted.invalid'})
            self.assertNotIn('access-control-allow-origin',response.headers)

    def test_disabled_preserves_normal_routes(self):
        with patch.dict('os.environ',{'MIGRATION_MAINTENANCE':'no'}):
            self.assertEqual(self.client.post('/records').status_code,200)
            self.assertEqual(self.calls,['called'])
