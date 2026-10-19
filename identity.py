"""Separate local accounts, OIDC Code + PKCE, or a trusted identity gateway."""
import hashlib,hmac,json,os,secrets,time
from flask import g,request,session,abort,redirect
from werkzeug.security import check_password_hash,generate_password_hash
def install(r):
 app=r.app;mode=r.config['auth']['mode'];prefix=r.PREFIX
 with r.db() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS experience_users(subject TEXT PRIMARY KEY,name TEXT NOT NULL,password_hash TEXT NOT NULL,roles TEXT NOT NULL,auth_version INTEGER NOT NULL DEFAULT 1);
  CREATE TABLE IF NOT EXISTS login_attempts(key TEXT NOT NULL,at INTEGER NOT NULL);
  CREATE INDEX IF NOT EXISTS login_attempt_time ON login_attempts(at);''')
  for u in json.loads(os.environ.get('EXPERIENCE_BOOTSTRAP_ACCOUNTS','[]')):
   if not u.get('password_hash','').startswith(('scrypt:','pbkdf2:')):raise ValueError('Bootstrap accounts require password hashes')
   c.execute('INSERT OR IGNORE INTO experience_users(subject,name,password_hash,roles) VALUES(?,?,?,?)',(u['subject'],u['name'],u['password_hash'],json.dumps(u['roles'])))
 oauth=None
 if mode=='oidc':
  from authlib.integrations.flask_client import OAuth
  issuer=r.config['auth']['issuer'].rstrip('/')
  if not issuer.startswith('https://'):raise ValueError('OIDC issuer must use HTTPS')
  oauth=OAuth(app).register('client_sso',client_id=r.config['auth']['client_id'],client_secret=os.environ.get('EXPERIENCE_OIDC_CLIENT_SECRET',''),server_metadata_url=issuer+'/.well-known/openid-configuration',client_kwargs={'scope':'openid profile email','code_challenge_method':'S256'})
 class Identity:
  def current_user(self):
   if mode=='gateway':
    secret=os.environ.get('EXPERIENCE_GATEWAY_SECRET','');token=request.headers.get('X-Experience-Gateway','')
    if len(secret)>=32 and token and hmac.compare_digest(secret,token):
     sub=request.headers.get('X-Experience-Subject','').strip()
     if sub:return {'sub':'gateway:'+sub,'name':request.headers.get('X-Experience-Name',sub),'roles':[x.strip() for x in request.headers.get('X-Experience-Roles','').split(',') if x.strip()]}
    return None
   u=session.get('identity')
   if not u or session.get('login_until',0)<time.time():return None
   if mode=='local':
    row=r.one('SELECT * FROM experience_users WHERE subject=?',(u['sub'],))
    if not row or row['auth_version']!=session.get('auth_version'):return None
    return {'sub':row['subject'],'name':row['name'],'roles':json.loads(row['roles'])}
   return u
 app.extensions['identity']=Identity()
 @app.route(prefix+'/login',methods=['GET','POST'])
 def login():
  if mode=='oidc':return oauth.authorize_redirect(r.config['public_base_url'].rstrip('/')+'/auth/callback')
  if mode=='gateway':return r.page('login.html',mode=mode,error=None)
  error=None
  if request.method=='POST':
   username=request.form.get('username','').strip();key=hashlib.sha256((str(request.remote_addr)+'|'+username).encode()).hexdigest();now=int(time.time());ipkey=hashlib.sha256(str(request.remote_addr).encode()).hexdigest()
   with r.db() as c:
    c.execute('BEGIN IMMEDIATE');c.execute('DELETE FROM login_attempts WHERE at<?',(now-3600,))
    if c.execute('SELECT COUNT(*) FROM login_attempts WHERE key=? AND at>?',(key,now-900)).fetchone()[0]>=8 or c.execute('SELECT COUNT(*) FROM login_attempts WHERE key=? AND at>?',(ipkey,now-900)).fetchone()[0]>=40:abort(429,'Too many attempts; wait 15 minutes')
    c.executemany('INSERT INTO login_attempts VALUES(?,?)',[(key,now),(ipkey,now)])
   row=r.one('SELECT * FROM experience_users WHERE subject=?',(username,))
   if 'DUMMY_PASSWORD_HASH' not in app.config:app.config['DUMMY_PASSWORD_HASH']=generate_password_hash(secrets.token_hex(16))
   valid=check_password_hash(row['password_hash'] if row else app.config['DUMMY_PASSWORD_HASH'],request.form.get('password',''))
   if row and valid:
    session.clear();session['identity']={'sub':row['subject'],'name':row['name'],'roles':json.loads(row['roles'])};session['auth_version']=row['auth_version'];session['login_until']=time.time()+3600;session.permanent=True
    with r.db() as c:c.execute('DELETE FROM login_attempts WHERE key=?',(key,))
    return redirect(prefix+'/')
   error='Sign-in failed. Check your username and password.'
  return r.page('login.html',mode=mode,error=error)
 @app.get(prefix+'/auth/callback')
 def callback():
  if mode!='oidc':abort(404)
  try:
   token=oauth.authorize_access_token();claims=token.get('userinfo')
   if not claims or claims.get('iss','').rstrip('/')!=r.config['auth']['issuer'].rstrip('/') or not claims.get('sub'):abort(403)
   roles=[];mapping=r.config['auth'].get('claim_to_roles',{});values=claims
   for part in r.config['auth'].get('roles_claim','realm_access.roles').split('.'):values=values.get(part,{}) if isinstance(values,dict) else {}
   if not isinstance(values,list):values=[]
   for val in values:roles.extend(mapping.get(str(val),[]))
   session.clear();session['identity']={'sub':claims['iss']+'|'+claims['sub'],'name':claims.get('name',claims['sub']),'roles':sorted(set(roles))};session['login_until']=time.time()+3600;session.permanent=True
   return redirect(prefix+'/')
  except Exception:abort(403,'SSO validation failed. Check the client configuration and identity provider; token details are not exposed.')
 @app.post(prefix+'/logout')
 def logout():session.clear();return redirect(prefix+'/')
 @app.route(prefix+'/account/password',methods=['GET','POST'])
 def password():
  r.require_user()
  if mode!='local':abort(404)
  error=None
  if request.method=='POST':
   row=r.one('SELECT * FROM experience_users WHERE subject=?',(g.user['sub'],));new=request.form.get('new_password','')
   if not check_password_hash(row['password_hash'],request.form.get('current_password','')):error='Current password is incorrect.'
   elif len(new)<12 or len(new)>256:error='Use a password of 12–256 characters.'
   elif new!=request.form.get('confirm_password'):error='New passwords do not match.'
   else:
    with r.db() as c:c.execute('UPDATE experience_users SET password_hash=?,auth_version=auth_version+1 WHERE subject=?',(generate_password_hash(new),g.user['sub']))
    session.clear();return redirect(prefix+'/login')
  return r.page('password.html',error=error)
