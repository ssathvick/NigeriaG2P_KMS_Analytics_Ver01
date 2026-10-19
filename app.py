"""Single-instance OpenG2P experience companion. Does not modify OpenG2P data."""
import hmac,json,os,re,secrets,sqlite3
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask,g,request,abort,session,render_template,redirect
import knowledge_management
ROOT=Path(__file__).parent
VERSION='1.0.0-rc1'
class KnowledgeConnection(sqlite3.Connection):
 def __exit__(self,*args):
  try:return super().__exit__(*args)
  finally:self.close()
def load_config(path=None):
 config=json.loads(Path(path or os.environ.get('EXPERIENCE_CONFIG',ROOT/'config/deployment.json')).read_text(encoding='utf-8'))
 prefix=config['prefix'].rstrip('/')
 if not re.fullmatch(r'/[A-Za-z0-9_/-]+',prefix) or '//' in prefix:raise ValueError('Invalid URL prefix')
 if any(c in config['public_base_url'] for c in ['<','>','"',"'",'\\','\r','\n','\t',' ']):raise ValueError('Invalid characters in public URL')
 base=urlparse(config['public_base_url']);local=base.hostname in ['localhost','127.0.0.1','::1']
 if base.username or base.password or base.query or base.fragment or not base.hostname or base.path.rstrip('/')!=prefix:raise ValueError('Base URL must match the prefix, with no credentials, query or fragment')
 if base.scheme!='https' and not (base.scheme=='http' and local):raise ValueError('HTTPS is required except on localhost')
 if config.get('auth',{}).get('mode') not in ['local','oidc','gateway']:raise ValueError('Choose local, oidc or gateway authentication')
 for service in config['services']:
  u=service['url'];p=urlparse(u)
  if any(c in u for c in ['<','>','"',"'",'\\','\r','\n','\t',' ']):raise ValueError('Invalid characters in service URL')
  if not (u.startswith('/') and not u.startswith('//') and '\\' not in u) and not (p.scheme=='https' and p.hostname and not p.username and not p.password):raise ValueError('Service URLs must be relative paths or HTTPS')
 return config
def create_app(config_path=None,database_path=None):
 config=load_config(config_path);prefix=config['prefix'].rstrip('/');secret=os.environ.get('EXPERIENCE_SESSION_SECRET','')
 if len(secret)<32:raise ValueError('Run setup first: a persistent session secret of at least 32 characters is required')
 app=Flask(__name__,static_url_path=prefix+'/static');app.secret_key=secret
 app.config.update(EXPERIENCE=config,MAX_CONTENT_LENGTH=100000,PERMANENT_SESSION_LIFETIME=timedelta(hours=1),SESSION_COOKIE_NAME='sathvick-experience',SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=urlparse(config['public_base_url']).scheme=='https',SESSION_COOKIE_PATH=prefix)
 database=Path(database_path or os.environ.get('EXPERIENCE_DATABASE',ROOT/'data/knowledge.sqlite'));database.parent.mkdir(parents=True,exist_ok=True)
 class Adapter:
  PREFIX=prefix
  def __init__(self):self.app=app;self.config=config;self.database=database;self.ROOT=ROOT
  def db(self):
   c=sqlite3.connect(database,timeout=20,factory=KnowledgeConnection);c.row_factory=sqlite3.Row;c.execute('PRAGMA busy_timeout=20000');return c
  def rows(self,sql,args=()):
   with self.db() as c:return [dict(x) for x in c.execute(sql,args)]
  def one(self,sql,args=()):
   rows=self.rows(sql,args);return rows[0] if rows else None
  def stamp(self):return datetime.now(timezone.utc).isoformat()
  def require_user(self):
   if not g.user:abort(401,'Sign in using the Sign in link.')
  def page(self,name,**values):return render_template(name,brand=config['brand']['name'],prefix=prefix,user=g.user,csrf=session['csrf'],**values)
 adapter=Adapter()
 with adapter.db() as c:
  if c.execute('PRAGMA user_version').fetchone()[0]>1:raise ValueError('Database schema is newer than this release; do not downgrade without a matching backup')
  c.execute('PRAGMA journal_mode=WAL')
 from identity import install as identity_install
 identity_install(adapter)
 @app.before_request
 def identity_and_csrf():
  g.user=app.extensions['identity'].current_user();g.staff=bool(g.user);g.session={'mode':'staff' if g.user else 'public'}
  subject=g.user['sub'] if g.user else None
  if session.get('subject')!=subject:
   for key in ['csrf','usage_sid']:session.pop(key,None)
   session['subject']=subject
  if 'csrf' not in session:session['csrf']=secrets.token_urlsafe(32)
  if 'usage_sid' not in session:session['usage_sid']=secrets.token_urlsafe(32)
  g.sid=session['usage_sid']
  if request.method in ['POST','PUT','PATCH','DELETE']:
   supplied=request.form.get('csrf','')
   if not supplied or not hmac.compare_digest(supplied,session['csrf']):abort(403,'Invalid CSRF token; reload the form')
 @app.after_request
 def security_headers(response):
  response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='same-origin'
  if not request.path.startswith(prefix+'/static/') and request.path!=prefix+'/api/config' and request.path!=prefix+'/embed/config.js':response.headers['Cache-Control']='no-store'
  return response
 @app.get('/')
 def root():return redirect(prefix+'/')
 @app.get(prefix+'/health')
 def health():
  adapter.one('SELECT 1 AS ok');return {'status':'ok','component':'experience-layer','version':VERSION}
 @app.get(prefix+'/')
 def home():return adapter.page('home.html')
 @app.get(prefix+'/api/config')
 def public_config():return {k:config[k] for k in ['prefix','brand','personas','services']}
 @app.get(prefix+'/embed/config.js')
 def embed_config():
  p={'baseUrl':config['public_base_url'].rstrip('/'),'knowledgeUrl':config['public_base_url'].rstrip('/')+'/api/knowledge','screenMappings':config.get('screen_mappings',[]),'brand':config['brand'],'personas':config['personas']}
  return app.response_class('window.OpenG2PExperience='+json.dumps(p)+';',mimetype='application/javascript')
 with app.app_context():
  knowledge_management.install(adapter)
  from analytics import install as analytics_install
  analytics_install(adapter)
 with adapter.db() as c:c.execute('PRAGMA user_version=1')
 app.extensions['experience_adapter']=adapter
 return app
if __name__=='__main__':create_app().run(host='127.0.0.1',port=18110,debug=False)
