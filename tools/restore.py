"""Offline restore helper. Stop both kit services before invoking this command."""
import argparse,hashlib,os,sqlite3,uuid,shutil
from contextlib import closing
from pathlib import Path
def restore(source,destination,services_stopped=False):
 if not services_stopped:raise ValueError('Stop experience and collector first; pass --services-stopped only after stopping them')
 source=Path(source).resolve();destination=Path(destination).resolve()
 if source==destination or not source.is_file():raise ValueError('Choose an existing backup file, separate from the active database')
 checksum=source.with_suffix('.sha256')
 if checksum.exists() and checksum.read_text().split()[0]!=hashlib.sha256(source.read_bytes()).hexdigest():raise ValueError('Backup checksum does not match')
 if any(Path(str(source)+suffix).exists() and Path(str(source)+suffix).stat().st_size for suffix in ['-wal','-journal']):raise ValueError('Use a closed, self-contained backup, not a live database with sidecar transactions')
 destination.parent.mkdir(parents=True,exist_ok=True);temp=destination.parent/('.restore-'+uuid.uuid4().hex+'.sqlite');staged=destination.parent/('.source-'+uuid.uuid4().hex+'.sqlite')
 try:
  # Stage the closed backup so legacy WAL headers can create lock files without
  # requiring write access to the original backup or its mounted directory.
  shutil.copyfile(source,staged)
  with closing(sqlite3.connect(staged)) as src:
   if src.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Backup is not healthy')
   src.execute('SELECT COUNT(*) FROM km_articles').fetchone()
   with closing(sqlite3.connect(temp)) as dst:src.backup(dst)
  temp.chmod(0o600)
  if hasattr(os,'geteuid') and os.geteuid()==0:os.chown(temp,10001,10001)
  os.replace(temp,destination)
  for suffix in ['-wal','-shm']:Path(str(destination)+suffix).unlink(missing_ok=True)
 finally:
  temp.unlink(missing_ok=True)
  for suffix in ['','-wal','-shm']:Path(str(staged)+suffix).unlink(missing_ok=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--backup',required=True);p.add_argument('--services-stopped',action='store_true');a=p.parse_args();restore(a.backup,os.environ['EXPERIENCE_DATABASE'],a.services_stopped);print('Knowledge database restored. Restart both kit services and run the health check.')
