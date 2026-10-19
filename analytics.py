"""Knowledge governance, privacy-limited usage, and configured aggregate sources."""
import csv,hashlib,io,json,uuid
from datetime import datetime,timezone,timedelta,date
from flask import g,request,abort,redirect

def init_tables(c):
 c.executescript('''CREATE TABLE IF NOT EXISTS analytics_events(event_id TEXT PRIMARY KEY,event_name TEXT NOT NULL,article INTEGER,version INTEGER,module TEXT NOT NULL,session_key TEXT NOT NULL,result_count INTEGER,helpful INTEGER,at TEXT NOT NULL);
 CREATE INDEX IF NOT EXISTS analytics_event_time ON analytics_events(at);
 CREATE TABLE IF NOT EXISTS analytics_daily(day TEXT NOT NULL,module TEXT NOT NULL,event_name TEXT NOT NULL,events INTEGER NOT NULL,zero_results INTEGER NOT NULL,helpful INTEGER NOT NULL,PRIMARY KEY(day,module,event_name));
 CREATE TABLE IF NOT EXISTS analytics_source_cache(source TEXT PRIMARY KEY,refreshed_at TEXT NOT NULL,payload TEXT NOT NULL,last_attempt TEXT NOT NULL,error TEXT);
 CREATE TABLE IF NOT EXISTS analytics_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);''')

def install(r):
 app=r.app;prefix=r.PREFIX;cfg=r.config['analytics']
 with r.db() as c:
  init_tables(c);c.execute('INSERT OR IGNORE INTO analytics_metadata VALUES(?,?)',('tracking_started_at',r.stamp()))
 def require(export=False):
  r.require_user()
  if not set(g.user.get('roles',[])).intersection(cfg['export_roles' if export else 'view_roles']):abort(403,'Your account is not authorised for this analytics action')
 def record(name,module='',article=None,version=None,result_count=None,helpful=None,event_id=None):
  now=r.stamp();sid=hashlib.sha256(g.sid.encode()).hexdigest();day=now[:10]
  with r.db() as c:
   c.execute('BEGIN IMMEDIATE')
   if c.execute('SELECT COUNT(*) FROM analytics_events WHERE session_key=? AND at>?',(sid,(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat())).fetchone()[0]>=120:return False
   if event_id and c.execute('SELECT 1 FROM analytics_events WHERE event_id=?',(event_id,)).fetchone():return False
   if name=='feedback_submitted' and c.execute("SELECT 1 FROM analytics_events WHERE session_key=? AND article=? AND version=? AND event_name='feedback_submitted' AND substr(at,1,10)=?",(sid,article,version,day)).fetchone():return False
   c.execute('INSERT INTO analytics_events VALUES(?,?,?,?,?,?,?,?,?)',(event_id or str(uuid.uuid4()),name,article,version,module,sid,result_count,helpful,now))
   c.execute('''INSERT INTO analytics_daily VALUES(?,?,?,1,?,?) ON CONFLICT(day,module,event_name) DO UPDATE SET events=events+1,zero_results=zero_results+excluded.zero_results,helpful=helpful+excluded.helpful''',(day,module,name,int(name=='search_completed' and result_count==0),int(helpful==1)))
   c.execute('DELETE FROM analytics_events WHERE at<?',((datetime.now(timezone.utc)-timedelta(days=90)).isoformat(),));c.execute('DELETE FROM analytics_daily WHERE day<?',((date.today()-timedelta(days=366)).isoformat(),))
  return True
 r.analytics_search=lambda module,count:record('search_completed',module=module,result_count=count)

 @app.get(prefix+'/knowledge/articles/<int:aid>')
 def article(aid):
  row=r.one("SELECT * FROM km_articles WHERE id=? AND published IS NOT NULL AND status!='archived'",(aid,))
  if not row:abort(404)
  content=json.loads(row['published'])
  if not r.km_can_read(content):abort(404)
  record('guide_opened',content['module'],aid,row['published_version'])
  return r.page('article.html',article=row,content=content,event_id=str(uuid.uuid4()),feedback=request.args.get('feedback')=='recorded')
 @app.post(prefix+'/api/analytics/feedback')
 def feedback():
  try:aid=int(request.form['article_id']);version=int(request.form['version']);event_id=str(uuid.UUID(request.form['event_id']));helpful=int(request.form['helpful'])
  except (KeyError,ValueError,TypeError):abort(400,'Invalid feedback fields')
  if helpful not in [0,1]:abort(400)
  row=r.one("SELECT * FROM km_articles WHERE id=? AND published IS NOT NULL AND status!='archived'",(aid,))
  if not row or row['published_version']!=version:abort(409,'Reload the current published version')
  content=json.loads(row['published'])
  if not r.km_can_read(content):abort(404)
  recorded=record('feedback_submitted',content['module'],aid,version,helpful=helpful,event_id=event_id)
  return redirect(prefix+'/knowledge/articles/'+str(aid)+'?feedback='+('recorded' if recorded else 'already-recorded'))

 def report():
  today=datetime.now(timezone.utc).date()
  try:
   start=date.fromisoformat(request.args.get('start',(today-timedelta(days=29)).isoformat()));end=date.fromisoformat(request.args.get('end',today.isoformat()))
  except ValueError:abort(400,'Dates must be YYYY-MM-DD')
  if start>end or (end-start).days>366:abort(400,'Choose a date range of at most 367 days')
  module=request.args.get('module','')
  if module and module not in __import__('knowledge_management').MODULES:abort(400,'Unknown module')
  where=' AND module=?' if module else '';args=[start.isoformat(),end.isoformat()]+([module] if module else [])
  usage=r.rows('SELECT event_name,SUM(events) AS events,SUM(zero_results) AS zero_results,SUM(helpful) AS helpful FROM analytics_daily WHERE day>=? AND day<=?'+where+' GROUP BY event_name',args)
  governance=r.rows("SELECT module,status,COUNT(*) AS articles,SUM(CASE WHEN published IS NOT NULL AND status!='archived' THEN 1 ELSE 0 END) AS live FROM km_articles"+(' WHERE module=?' if module else '')+' GROUP BY module,status',[module] if module else [])
  cache={row['source']:row for row in r.rows('SELECT * FROM analytics_source_cache')};sources=[]
  for source in cfg.get('sources',[]):
   row=cache.get(source['id']);state='Disabled' if not source.get('enabled') else 'Not collected';metrics=[];stamp=''
   if source.get('enabled') and row:
    stamp=row['refreshed_at'];metrics=json.loads(row['payload'])
    try:age=(datetime.now(timezone.utc)-datetime.fromisoformat(stamp)).total_seconds()
    except (ValueError,TypeError):age=10**10
    state='Refresh failed — last valid values retained' if row['error'] else 'Stale' if age>cfg.get('stale_seconds',1800) else 'Current'
   sources.append({'id':source['id'],'status':state,'refreshed_at':stamp,'metrics':metrics})
  return {'generated_at':r.stamp(),'filters':{'start':str(start),'end':str(end),'module':module},'governance':governance,'usage':usage,'sources':sources,'tracking_started_at':r.one("SELECT value FROM analytics_metadata WHERE key='tracking_started_at'")['value'],'scope':'Current knowledge governance; UTC dates filter usage only. Backend aggregates have independent source scope. No settled-payment claims.'}
 @app.get(prefix+'/analytics')
 def dashboard():
  require();return r.page('analytics.html',report=report(),modules=__import__('knowledge_management').MODULES,can_export=bool(set(g.user['roles'])&set(cfg['export_roles'])))
 @app.get(prefix+'/api/analytics')
 def api():require();return report()
 @app.get(prefix+'/api/analytics/export.csv')
 def export():
  require(True);data=report();out=io.StringIO(newline='');writer=csv.writer(out);writer.writerow(['source','metric','label','value','as_of','status'])
  def safe(x):
   t=str(x);return "'"+t if t.startswith(('=','+','-','@','\t','\r')) else t
  for row in data['governance']:
   for metric in ['articles','live']:writer.writerow(['knowledge',metric,safe(row['module']+'/'+row['status']),row[metric],data['generated_at'],'current snapshot'])
  for row in data['usage']:writer.writerow(['knowledge',safe(row['event_name']),'events',row['events'],data['filters']['start']+'/'+data['filters']['end'],'UTC date window'])
  for source in data['sources']:
   for row in source['metrics']:writer.writerow([safe(source['id']),safe(row['metric']),safe(row['label']),row['value'],source['refreshed_at'],source['status']])
  return app.response_class(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=experience-aggregates.csv'})
