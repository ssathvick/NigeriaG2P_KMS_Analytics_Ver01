"""Read-only aggregate collectors. No credential or source error text is logged."""
import argparse,json,math,os,re,sqlite3,time,signal,threading
from contextlib import closing
from datetime import datetime,timezone,timedelta
from urllib.parse import urlparse
from app import load_config,ROOT
from analytics import init_tables

PROFILES={
 'registry-1.2':{'records':"SELECT 'Individuals',COUNT(*) FROM g2p_register_individuals UNION ALL SELECT 'Households',COUNT(*) FROM g2p_register_households",'change_request_status':"SELECT COALESCE(approval_status,'Unknown'),COUNT(*) FROM g2p_register_change_requests GROUP BY 1"},
 'pbms-3':{'programme_status':"SELECT COALESCE(program_status,'Unknown'),COUNT(*) FROM g2p_program_definition GROUP BY 1",'beneficiary_list_status':"SELECT COALESCE(list_workflow_status,'Unknown'),COUNT(*) FROM g2p_beneficiary_list GROUP BY 1",'instruction_process_status':"SELECT COALESCE(disbursement_batch_creation_status,'Unknown'),COUNT(*) FROM g2p_beneficiary_list GROUP BY 1"},
 'awe':{'request_status':"SELECT COALESCE(status,'Unknown'),COUNT(*) FROM approval_request GROUP BY 1"},
 'bridge-3':{'instruction_records':"SELECT 'Instruction records (not settlement)',COUNT(*) FROM disbursements",'bank_dispatch_status':"SELECT COALESCE(sponsor_bank_dispatch_status,'Unknown'),COUNT(*) FROM disbursement_batch_control GROUP BY 1"}}
def normalize(items):
 if not isinstance(items,list) or len(items)>500:raise ValueError('Expected at most 500 aggregate rows')
 result=[]
 for row in items:
  if not isinstance(row,dict) or set(row)-{'metric','label','value'}:raise ValueError('Aggregate schema violation')
  metric=row['metric'];label=row['label'];value=row['value']
  if not isinstance(metric,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',metric) or not isinstance(label,str) or len(label)>160:raise ValueError('Invalid metric or label')
  if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or value<0:raise ValueError('Metrics must be finite non-negative numbers')
  result.append({'metric':metric,'label':label,'value':value})
 return result
def collect_source(source):
 if source['adapter']=='https-json':
  import requests
  p=urlparse(source['url'])
  if p.scheme!='https' or p.username or p.password or p.fragment:raise ValueError('Source must be a credential-free HTTPS URL')
  if p.hostname not in source.get('allowed_hosts',[]):raise ValueError('Source host is not allowlisted')
  headers={'Accept':'application/json'};key=source.get('token_env')
  if key:
   if not os.environ.get(key):raise ValueError('Source token is missing')
   headers['Authorization']='Bearer '+os.environ[key]
  with requests.get(source['url'],headers=headers,timeout=(8,15),allow_redirects=False,stream=True) as res:
   if res.status_code!=200:raise ValueError('Source request failed')
   body=bytearray()
   for part in res.iter_content(65536):
    body.extend(part)
    if len(body)>1048576:raise ValueError('Aggregate response exceeds 1 MiB')
   payload=json.loads(body)
  if not isinstance(payload,dict) or set(payload)!= {'metrics'}:raise ValueError('Expected a metrics-only payload')
  return normalize(payload['metrics'])
 if source['adapter']!='postgres':raise ValueError('Unknown adapter')
 import psycopg
 from psycopg import sql
 dsn=os.environ.get(source['dsn_env'],'')
 if not dsn:raise ValueError('Missing read-only source DSN')
 from psycopg.conninfo import conninfo_to_dict
 if conninfo_to_dict(dsn).get('sslmode')!='verify-full':raise ValueError('PostgreSQL source requires sslmode=verify-full')
 rows=[]
 with psycopg.connect(dsn,connect_timeout=8,options='-c default_transaction_read_only=on -c statement_timeout=10000 -c search_path=public') as conn:
  with conn.cursor() as cur:
   cur.execute('SET TRANSACTION READ ONLY')
   if source.get('profile')=='approved-view':
    schema=source.get('schema','reporting');view=source['view']
    if not all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',x) for x in [schema,view]):raise ValueError('Invalid view identifier')
    cur.execute(sql.SQL('SELECT metric,label,value FROM {}.{} LIMIT 501').format(sql.Identifier(schema),sql.Identifier(view)))
    rows=[dict(zip(['metric','label','value'],[a,b,float(v)])) for a,b,v in cur.fetchall()]
   else:
    for metric,query in PROFILES[source['profile']].items():
     cur.execute(query)
     for label,value in cur.fetchall():
      if value is not None:rows.append({'metric':metric,'label':str(label),'value':float(value)})
 return normalize(rows)
def refresh(config,database,stop_event=None):
 results={}
 with closing(sqlite3.connect(database,timeout=20)) as c,c:
  init_tables(c)
  for source in config['analytics'].get('sources',[]):
   if stop_event is not None and stop_event.is_set():break
   if not source.get('enabled'):continue
   now=datetime.now(timezone.utc).isoformat()
   try:
    values=collect_source(source)
    c.execute("INSERT INTO analytics_source_cache VALUES(?,?,?,?,NULL) ON CONFLICT(source) DO UPDATE SET refreshed_at=excluded.refreshed_at,payload=excluded.payload,last_attempt=excluded.last_attempt,error=NULL",(source['id'],now,json.dumps(values),now));results[source['id']]='ok'
   except Exception:
    c.execute("INSERT INTO analytics_source_cache VALUES(?,?,?,?,'refresh_failed') ON CONFLICT(source) DO UPDATE SET last_attempt=excluded.last_attempt,error='refresh_failed'",(source['id'],'','[]',now));results[source['id']]='failed'
  c.execute('DELETE FROM analytics_events WHERE at<?',((datetime.now(timezone.utc)-timedelta(days=90)).isoformat(),));c.execute('DELETE FROM analytics_daily WHERE day<?',((datetime.now(timezone.utc)-timedelta(days=366)).date().isoformat(),))
 return results
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--loop',action='store_true');args=parser.parse_args()
 stop=threading.Event()
 signal.signal(signal.SIGTERM,lambda *_:stop.set())
 signal.signal(signal.SIGINT,lambda *_:stop.set())
 while not stop.is_set():
  config=load_config();results=refresh(config,os.environ.get('EXPERIENCE_DATABASE',str(ROOT/'data/knowledge.sqlite')),stop_event=stop);print(json.dumps({'sources':results}),flush=True)
  if not args.loop:raise SystemExit(int(any(v=='failed' for v in results.values())))
  stop.wait(max(60,int(config['analytics'].get('refresh_seconds',900))))
