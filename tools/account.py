"""Operator-only local account provisioning/reset through container exec."""
import argparse,getpass,json,os,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from werkzeug.security import generate_password_hash
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('username');p.add_argument('--roles',required=True);a=p.parse_args()
 allowed={'knowledge-editor','knowledge-reviewer','knowledge-publisher','analytics-viewer','analytics-exporter','knowledge-reader','registration-officer','verification-officer','programme-supervisor'};roles=a.roles.split(',')
 if not set(roles)<=allowed:raise SystemExit('Unknown role')
 pw=getpass.getpass('New password (12–256 characters): ')
 if not 12<=len(pw)<=256 or pw!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords do not match or are too short')
 with sqlite3.connect(os.environ['EXPERIENCE_DATABASE']) as c:c.execute('INSERT INTO experience_users(subject,name,password_hash,roles) VALUES(?,?,?,?) ON CONFLICT(subject) DO UPDATE SET password_hash=excluded.password_hash,roles=excluded.roles,auth_version=experience_users.auth_version+1',(a.username,a.username,generate_password_hash(pw),json.dumps(roles)))
 print('Local account updated; prior sessions revoked. OpenG2P accounts were not changed.')
