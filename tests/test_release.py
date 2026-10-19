import copy,json,os,re,sqlite3,sys,tempfile,time,unittest,uuid
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['EXPERIENCE_SESSION_SECRET']='isolated-test-secret-not-for-deployment-0123456789'
from werkzeug.security import generate_password_hash
from app import create_app,load_config
from collector import refresh,normalize,collect_source
from tools.backup import backup
from tools.configure import configure,write_env
from tools.export_kubernetes import read_env
from tools.restore import restore
HASH=generate_password_hash('Isolated-test-password-123')
ACCOUNTS=[{'subject':u,'name':u,'password_hash':HASH,'roles':roles} for u,roles in [('author',['knowledge-editor']),('reviewer',['knowledge-reviewer']),('publisher',['knowledge-publisher','analytics-viewer','analytics-exporter']),('viewer',['analytics-viewer']),('officer',['registration-officer']),('citizen',[])]]

class Release(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=self.root/'knowledge.sqlite';self.cfg=json.loads((ROOT/'config/deployment.example.json').read_text());self.cfg['seed_mode']='none';self.path=self.root/'config.json';self.path.write_text(json.dumps(self.cfg));self.env=patch.dict(os.environ,{'EXPERIENCE_BOOTSTRAP_ACCOUNTS':json.dumps(ACCOUNTS)});self.env.start();self.app=create_app(self.path,self.db);self.app.testing=True;self.client=self.app.test_client();self.r=self.app.extensions['experience_adapter']
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def csrf(self):
  self.client.get('/experience/')
  with self.client.session_transaction(path='/experience/') as s:return s['csrf']
 def post(self,url,data={}):return self.client.post(url,data={**data,'csrf':self.csrf()})
 def login(self,user):
  with self.client.session_transaction(path='/experience/') as s:s.clear()
  res=self.post('/experience/login',{'username':user,'password':'Isolated-test-password-123'});self.assertEqual(res.status_code,302)
 def draft(self,visibility='public',audience='all'):
  self.login('author');data={'module':'intake','stage':'Review','audience':audience,'title':'Test guidance','purpose':'Purpose','steps':'One\nTwo','requirements':'Evidence','next_step':'Review','issues':'Contact support','visibility':visibility}
  res=self.post('/experience/knowledge/admin/save',data);self.assertEqual(res.status_code,302);return int(res.location.rsplit('/',1)[1]),data
 def action(self,aid,action,version=1,**extra):return self.post(f'/experience/knowledge/admin/{aid}/{action}',{'version':str(version),**extra})
 def publish(self,visibility='public',audience='all'):
  aid,data=self.draft(visibility,audience);self.action(aid,'submit');self.login('reviewer');self.assertEqual(self.action(aid,'review').status_code,302);self.login('publisher');self.assertEqual(self.action(aid,'publish').status_code,302);return aid,data
 def anon(self):
  with self.client.session_transaction(path='/experience/') as s:s.clear()
 def test_health_launcher_static(self):
  for url in ['/experience/health','/experience/','/experience/api/config','/experience/embed/config.js','/experience/static/workspace.js','/experience/knowledge']:
   response=self.client.get(url);self.assertEqual(response.status_code,200,url);response.close()
 def test_startup_requires_secret(self):
  with patch.dict(os.environ,{'EXPERIENCE_SESSION_SECRET':''}):
   with self.assertRaises(ValueError):create_app(self.path,self.db)
 def test_untrusted_headers_do_not_sign_in(self):
  self.assertEqual(self.client.get('/experience/knowledge/admin',headers={'X-Experience-Subject':'bad','X-Experience-Roles':'knowledge-publisher'}).status_code,401)
 def test_csrf_required_for_login_and_mutations(self):self.assertEqual(self.client.post('/experience/login',data={'username':'author'}).status_code,403)
 def test_roles_are_enforced(self):
  self.login('citizen');self.assertEqual(self.client.get('/experience/knowledge/admin').status_code,403);self.assertEqual(self.client.get('/experience/analytics').status_code,403)
 def test_independent_lifecycle(self):
  aid,_=self.draft();self.assertEqual(self.action(aid,'publish').status_code,403);self.action(aid,'submit');self.login('reviewer');self.action(aid,'review');self.assertEqual(self.action(aid,'publish').status_code,403);self.login('publisher');self.action(aid,'publish');self.assertEqual(len(self.client.get('/experience/api/knowledge').json['articles']),1)
 def test_self_review_rejected_even_with_both_roles(self):
  aid,_=self.draft();self.action(aid,'submit')
  with self.r.db() as c:c.execute('UPDATE experience_users SET roles=? WHERE subject=?',(json.dumps(['knowledge-editor','knowledge-reviewer']),'author'))
  self.assertEqual(self.action(aid,'review').status_code,403)
 def test_staff_guidance_not_exposed_by_audience_filter(self):
  aid,_=self.publish('staff','officer');self.anon();self.assertEqual(self.client.get('/experience/api/knowledge?include_roles=1&audience=officer').json['articles'],[]);self.assertEqual(self.client.get(f'/experience/knowledge/articles/{aid}').status_code,404);self.login('citizen');self.assertEqual(self.client.get('/experience/api/knowledge?audience=officer').json['articles'],[]);self.login('officer');self.assertEqual(len(self.client.get('/experience/api/knowledge?audience=officer').json['articles']),1)
 def test_public_guide_is_public(self):
  aid,_=self.publish();self.anon();self.assertEqual(self.client.get(f'/experience/knowledge/articles/{aid}').status_code,200)
 def test_old_published_version_survives_edit_and_conflicts(self):
  aid,data=self.publish();self.login('author');data.update(id=aid,version=1,title='Unreviewed change',visibility='staff');self.assertEqual(self.post('/experience/knowledge/admin/save',data).status_code,302);self.assertEqual(self.post('/experience/knowledge/admin/save',data).status_code,409);self.anon();self.assertEqual(self.client.get('/experience/api/knowledge').json['articles'][0]['title'],'Test guidance')
 def test_archive_restore_does_not_republish(self):
  aid,_=self.publish();self.action(aid,'archive');self.assertEqual(self.client.get('/experience/api/knowledge').json['articles'],[]);self.action(aid,'restore');self.assertEqual(self.client.get('/experience/api/knowledge').json['articles'],[])
 def test_return_reason_validation(self):
  aid,_=self.draft();self.action(aid,'submit');self.login('reviewer');self.assertEqual(self.action(aid,'return',reason='bad').status_code,400);self.assertEqual(self.action(aid,'return',reason='Correct the procedure reference').status_code,302)
 def test_seed_content_is_unpublished_drafts(self):
  self.cfg['seed_mode']='draft';self.path.write_text(json.dumps(self.cfg));app=create_app(self.path,self.root/'seed.sqlite');r=app.extensions['experience_adapter'];self.assertEqual(r.one('SELECT COUNT(*) AS n FROM km_articles')['n'],54);self.assertEqual(r.one('SELECT COUNT(*) AS n FROM km_articles WHERE published IS NOT NULL')['n'],0)
 def test_no_seed_overwrite_on_restart(self):
  aid,_=self.draft();create_app(self.path,self.db);self.assertEqual(self.r.one('SELECT version FROM km_articles WHERE id=?',(aid,))['version'],1)
 def test_search_does_not_store_search_text(self):
  self.client.get('/experience/knowledge?q=PRIVATE-QUERY-EXAMPLE');rows=self.r.rows('SELECT * FROM analytics_events');self.assertEqual(rows[0]['event_name'],'search_completed');self.assertNotIn('PRIVATE-QUERY-EXAMPLE',json.dumps(rows))
 def test_feedback_deduplication_and_stale_versions(self):
  aid,_=self.publish();self.anon();self.client.get(f'/experience/knowledge/articles/{aid}');form={'article_id':aid,'version':1,'event_id':str(uuid.uuid4()),'helpful':1};self.assertEqual(self.post('/experience/api/analytics/feedback',form).status_code,302);self.post('/experience/api/analytics/feedback',{**form,'event_id':str(uuid.uuid4())});self.assertEqual(self.r.one("SELECT COUNT(*) AS n FROM analytics_events WHERE event_name='feedback_submitted'")['n'],1);self.assertEqual(self.post('/experience/api/analytics/feedback',{**form,'version':9}).status_code,409)
 def test_analytics_access_and_csv_export(self):
  self.assertEqual(self.client.get('/experience/api/analytics').status_code,401);self.login('viewer');self.assertEqual(self.client.get('/experience/analytics').status_code,200);self.assertEqual(self.client.get('/experience/api/analytics/export.csv').status_code,403);self.login('publisher');self.assertEqual(self.client.get('/experience/api/analytics/export.csv').status_code,200)
 def test_analytics_filters_and_empty_sources(self):
  self.login('publisher');self.assertEqual(self.client.get('/experience/api/analytics?start=bad').status_code,400);self.assertEqual(self.client.get('/experience/api/analytics?module=bad').status_code,400);self.assertEqual(self.client.get('/experience/api/analytics').json['sources'],[])
 def test_failed_source_preserves_last_valid_metrics(self):
  config=copy.deepcopy(self.cfg);config['analytics']['sources']=[{'id':'registry','enabled':True,'adapter':'postgres','dsn_env':'NOT_SET','profile':'registry-1.2'}]
  with patch('collector.collect_source',return_value=[{'metric':'records','label':'Households','value':7}]):self.assertEqual(refresh(config,self.db),{'registry':'ok'})
  with patch('collector.collect_source',side_effect=ValueError('secret connection detail')):self.assertEqual(refresh(config,self.db),{'registry':'failed'})
  row=self.r.one('SELECT * FROM analytics_source_cache');self.assertEqual(json.loads(row['payload'])[0]['value'],7);self.assertEqual(row['error'],'refresh_failed');self.assertNotIn('secret',json.dumps(row))
 def test_collector_rejects_payloads_and_insecure_connections(self):
  for payload in [[{'metric':'x','label':'x','value':float('nan')}],[{'metric':'x','label':'x','value':True}],[{'metric':'x','label':'x','value':1,'beneficiary':'private'}]]:
   with self.assertRaises(ValueError):normalize(payload)
  with self.assertRaises(ValueError):collect_source({'adapter':'https-json','url':'http://example.org','allowed_hosts':['example.org']})
  with patch.dict(os.environ,{'TEST_DSN':'postgresql://x:x@localhost/x?sslmode=disable'}):
   with self.assertRaises(ValueError):collect_source({'adapter':'postgres','dsn_env':'TEST_DSN','profile':'registry-1.2'})
 def test_backup_integrity_and_contents(self):
  aid,_=self.draft();out=backup(self.db,self.root/'backups')
  with closing(sqlite3.connect(out)) as c:self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertEqual(c.execute('PRAGMA journal_mode').fetchone()[0],'delete');self.assertEqual(c.execute('SELECT COUNT(*) FROM km_articles').fetchone()[0],1)
 def test_restore_requires_stopped_services_and_restores_snapshot(self):
  aid,_=self.draft();out=backup(self.db,self.root/'backups');destination=self.root/'restored.sqlite'
  with self.assertRaises(ValueError):restore(out,destination)
  restore(out,destination,True)
  with closing(sqlite3.connect(destination)) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM km_articles').fetchone()[0],1)
 def test_restore_checksum_rejects_corruption(self):
  out=backup(self.db,self.root/'backups');out.with_suffix('.sha256').write_text('0'*64)
  with self.assertRaises(ValueError):restore(out,self.root/'bad.sqlite',True)
 def test_guided_configuration_and_idempotence(self):
  root=self.root/'kit';(root/'config').mkdir(parents=True);(root/'config/deployment.example.json').write_text((ROOT/'config/deployment.example.json').read_text())
  answers=iter(['Client test','http://127.0.0.1:18110/experience']+['']*6+['local','author','reviewer','publisher','no'])
  with patch('builtins.input',side_effect=lambda _:next(answers)),patch('getpass.getpass',return_value='Setup-test-password-123'):configure(root)
  env=read_env(root/'.env');self.assertGreaterEqual(len(env['EXPERIENCE_SESSION_SECRET']),32);self.assertEqual(len(json.loads(env['EXPERIENCE_BOOTSTRAP_ACCOUNTS'])),3);old=(root/'.env').read_bytes()
  with patch('builtins.input',side_effect=AssertionError('Unexpected reconfiguration')):configure(root)
  self.assertEqual((root/'.env').read_bytes(),old);self.assertTrue((root/'config/EMBED-SNIPPET.html').exists())
 def test_oidc_mode_maps_only_validated_claims(self):
  from unittest.mock import Mock
  oauth=Mock();oauth.authorize_access_token.return_value={'userinfo':{'iss':'https://idp.example/realms/client','sub':'test-sub','name':'Test','realm_access':{'roles':['external-reviewer','not-mapped']}}}
  self.cfg['auth'].update(mode='oidc',issuer='https://idp.example/realms/client',client_id='client',claim_to_roles={'external-reviewer':['knowledge-reviewer']});self.path.write_text(json.dumps(self.cfg))
  with patch('authlib.integrations.flask_client.OAuth.register',return_value=oauth):app=create_app(self.path,self.root/'oidc.sqlite')
  client=app.test_client();self.assertEqual(client.get('/experience/auth/callback').status_code,302)
  with client.session_transaction(path='/experience/') as s:self.assertEqual(s['identity']['roles'],['knowledge-reviewer'])
  oauth.authorize_access_token.return_value={'userinfo':{'iss':'https://wrong.example','sub':'bad'}};self.assertEqual(client.get('/experience/auth/callback').status_code,403)
 def test_authentication_screen_has_no_help_injection(self):
  self.assertNotIn(b'static/help.js',self.client.get('/experience/login').data)
 def test_local_password_change_revokes_other_session(self):
  self.login('author');other=self.app.test_client();other.get('/experience/login')
  with other.session_transaction(path='/experience/') as s:token=s['csrf']
  other.post('/experience/login',data={'csrf':token,'username':'author','password':'Isolated-test-password-123'})
  self.post('/experience/account/password',{'current_password':'Isolated-test-password-123','new_password':'Replacement-password-123','confirm_password':'Replacement-password-123'});self.assertEqual(other.get('/experience/knowledge/admin').status_code,401)
 def test_login_rate_limit(self):
  for _ in range(8):self.post('/experience/login',{'username':'unknown','password':'wrong'})
  self.assertEqual(self.post('/experience/login',{'username':'unknown','password':'wrong'}).status_code,429)
 def test_dotenv_roundtrip_special_characters(self):
  p=self.root/'.env';values={'KEY':'abc$def#x\'y\\z'};write_env(p,values);self.assertEqual(read_env(p),values)
 def test_bad_service_and_public_url(self):
  self.cfg['public_base_url']='http://client.example/experience';self.path.write_text(json.dumps(self.cfg))
  with self.assertRaises(ValueError):load_config(self.path)
  self.cfg['public_base_url']='http://127.0.0.1:18110/experience';self.cfg['services'][0]['url']='javascript:alert(1)';self.path.write_text(json.dumps(self.cfg))
  with self.assertRaises(ValueError):load_config(self.path)
 def test_html_escaped_and_sensitive_pages_not_cached(self):
  aid,data=self.draft();data.update(id=aid,version=1,title='<script>alert(1)</script>');self.post('/experience/knowledge/admin/save',data);res=self.client.get(f'/experience/knowledge/admin/{aid}');self.assertIn(b'&lt;script&gt;',res.data);self.assertEqual(res.headers['Cache-Control'],'no-store')

if __name__=='__main__':unittest.main(verbosity=2)
