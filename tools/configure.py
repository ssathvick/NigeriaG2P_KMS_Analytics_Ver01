"""Guided first-run configuration. Run inside the setup container; no host Python needed."""
import argparse,getpass,json,os,re,secrets,sys
from pathlib import Path
from urllib.parse import urlparse,quote
from werkzeug.security import generate_password_hash
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import load_config

def write_env(path,values):
 lines=[]
 for k,v in values.items():
  if not re.fullmatch('[A-Z][A-Z0-9_]*',k) or '\n' in str(v) or '\r' in str(v):raise ValueError('Invalid environment entry')
  lines.append(k+"='"+str(v).replace('\\','\\\\').replace("'","\\'")+"'")
 path.write_text('\n'.join(lines)+'\n',encoding='utf-8');path.chmod(0o600)
def ask(label,default=''):
 value=input(label+(f' [{default}]' if default else '')+': ').strip();return value or default
def password(label):
 while True:
  a=getpass.getpass(label+' (12–256 characters): ');b=getpass.getpass('Confirm password: ')
  if 12<=len(a)<=256 and a==b:return a
  print('Passwords must match and have 12–256 characters.')
def configure(root):
 root=Path(root).resolve();config_path=root/'config/deployment.json';env_path=root/'.env'
 if env_path.exists():
  load_config(config_path);print('Existing installation configuration retained. Edit config/deployment.json and restart to change URLs. Credentials and data were not reset.');return
 config=json.loads((root/'config/deployment.example.json').read_text(encoding='utf-8'))
 print('\nSathvick OpenG2P Experience · guided setup\nNo changes are made to the existing OpenG2P installation.\n')
 config['brand']['name']=ask('Client / platform display name','Client OpenG2P Experience')
 config['public_base_url']=ask('Public URL including /experience (HTTPS outside localhost)','http://127.0.0.1:18110/experience').rstrip('/')
 if urlparse(config['public_base_url']).path!='/experience':raise ValueError('This guided installation uses the /experience prefix')
 config['prefix']='/experience'
 print('Leave an application URL blank to disable its launcher link.')
 for service in config['services']:
  if service['id'] in ['knowledge','analytics']:continue
  url=ask(service['title']+' HTTPS URL')
  if url:
   p=urlparse(url)
   if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Provide a credential-free HTTPS application URL')
   service['url']=url;service['enabled']=True
   origin=p.scheme+'://'+p.netloc
   if origin not in config['allowed_origins']:config['allowed_origins'].append(origin)
 mode=ask('Authentication: local or oidc','local')
 if mode not in ['local','oidc']:raise ValueError('Choose local or oidc')
 config['auth']['mode']=mode;env={'EXPERIENCE_SESSION_SECRET':secrets.token_hex(32),'EXPERIENCE_GATEWAY_SECRET':secrets.token_hex(32)}
 if mode=='local':
  accounts=[];names=set()
  for default,roles in [('editor',['knowledge-editor']),('reviewer',['knowledge-reviewer']),('publisher',['knowledge-publisher','analytics-viewer','analytics-exporter'])]:
   name=ask(default.title()+' username',default)
   if not re.fullmatch('[A-Za-z0-9_.-]{1,80}',name) or name in names:raise ValueError('Use distinct usernames with letters, digits, dot, underscore or hyphen')
   names.add(name);accounts.append({'subject':name,'name':name,'roles':roles,'password_hash':generate_password_hash(password(name))})
  env['EXPERIENCE_BOOTSTRAP_ACCOUNTS']=json.dumps(accounts,separators=(',',':'))
 else:
  config['auth']['issuer']=ask('OIDC issuer (HTTPS, including realm if applicable)').rstrip('/')
  if not config['auth']['issuer'].startswith('https://'):raise ValueError('Use an HTTPS issuer')
  config['auth']['client_id']=ask('OIDC confidential client ID')
  env['EXPERIENCE_OIDC_CLIENT_SECRET']=getpass.getpass('OIDC client secret: ')
  if not config['auth']['client_id'] or not env['EXPERIENCE_OIDC_CLIENT_SECRET']:raise ValueError('OIDC client ID and secret are required')
  for role in ['knowledge-editor','knowledge-reviewer','knowledge-publisher','analytics-viewer','analytics-exporter','knowledge-reader','registration-officer','verification-officer','programme-supervisor']:
   external=ask('IdP role for '+role,role);config['auth']['claim_to_roles'].setdefault(external,[]).append(role)
  print('Register this redirect URI at the IdP: '+config['public_base_url']+'/auth/callback')
 sources=[];connections={}
 if ask('Connect read-only PostgreSQL aggregate sources now? yes/no','no').lower()=='yes':
  for identifier,profile in [('registry','registry-1.2'),('pbms','pbms-3'),('awe','awe'),('bridge','bridge-3')]:
   if ask('Configure '+identifier+'? yes/no','no').lower()!='yes':continue
   print('Built-in '+profile+' queries require the matching client schema. A mismatch is reported as failure, never as zero.')
   host=ask(identifier+' database hostname (reachable from Docker)');port=int(ask('Database port','5432'));db=ask('Database name');user=ask('Dedicated read-only database username');pw=getpass.getpass('Database password: ')
   if not host or not db or not user or not 1<=port<=65535 or any(x in host for x in ['/','@','?','#']):raise ValueError('Invalid database connection settings')
   hostpart='['+host+']' if ':' in host and not host.startswith('[') else host
   ca=ask('CA certificate path INSIDE container (copy CA into config/certs), or system')
   query='sslmode=verify-full'+('&sslrootcert='+quote(ca,safe='/') if ca else '')
   key='SOURCE_'+identifier.upper()+'_DSN';connections[key]='postgresql://'+quote(user,safe='')+':'+quote(pw,safe='')+'@'+hostpart+':'+str(port)+'/'+quote(db,safe='')+'?'+query
   sources.append({'id':identifier,'adapter':'postgres','profile':profile,'dsn_env':key,'enabled':True})
 config['analytics']['sources']=sources;config['seed_mode']='draft'
 candidate=root/'config/.deployment.pending.json';candidate.write_text(json.dumps(config,indent=2),encoding='utf-8')
 try:load_config(candidate)
 finally:candidate.unlink(missing_ok=True)
 config_path.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8');write_env(env_path,env)
 if connections:write_env(root/'config/connectors.env',connections)
 base=config['public_base_url'];tags='\n'.join([f'<link rel="stylesheet" href="{base}/static/help.css">',f'<script defer src="{base}/embed/config.js"></script>']+[f'<script defer src="{base}/static/{name}.js"></script>' for name in ['context-presets','context','shell','help']])
 (root/'config/EMBED-SNIPPET.html').write_text(tags+'\n',encoding='utf-8')
 print('\nConfiguration saved. Starter guides are drafts and are not public.\nLocal entry: http://127.0.0.1:18110/experience/\nConfigured public URL: '+base+'\nInstall the generated config/EMBED-SNIPPET.html into approved native templates. See docs/CLIENT-INTEGRATION.md.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--root',default='/kit');args=parser.parse_args()
 try:configure(args.root)
 except (ValueError,KeyboardInterrupt,EOFError) as exc:print('Setup did not complete: '+str(exc),file=sys.stderr);raise SystemExit(1)
