"""SQLite online backup; never backs up or changes OpenG2P databases."""
import argparse,hashlib,json,os,sqlite3
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
def backup(database,directory):
 database=Path(database).resolve();directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
 out=directory/('experience-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite')
 if not database.is_file():raise ValueError('Knowledge database does not exist')
 with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(out)) as dst:
  src.backup(dst)
  # Produce one self-contained archive file, readable from a read-only mount.
  assert dst.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'
  assert dst.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 out.chmod(0o600)
 if hasattr(os,'geteuid') and os.geteuid()==0:os.chown(out,10001,10001)
 (out.with_suffix('.sha256')).write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n',encoding='utf-8');return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--directory',default='/app/backups');args=p.parse_args();print(backup(os.environ.get('EXPERIENCE_DATABASE','/app/data/knowledge.sqlite'),args.directory))
