"""Wait for the application-created SQLite schema before starting the sidecar."""
import os,sqlite3,subprocess,sys,time
from contextlib import closing
from pathlib import Path
database=Path(os.environ['EXPERIENCE_DATABASE'])
for attempt in range(120):
 try:
  if database.is_file():
   with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as c:
    if c.execute("SELECT 1 FROM sqlite_master WHERE name='analytics_daily'").fetchone():break
 except sqlite3.Error:pass
 time.sleep(2)
else:raise SystemExit('Application analytics schema not ready after 240 seconds')
os.execv(sys.executable,[sys.executable,str(Path(__file__).resolve().parents[1]/'collector.py'),'--loop'])
