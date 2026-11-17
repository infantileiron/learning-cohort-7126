import os,time,json,logging
from pathlib import Path
import redis
from src.config.database import Session
from src.models.entities import Cohort,Correction
from src.services.analysis import calculate
from src.services.corrections import finalize
r=redis.Redis.from_url(os.environ['REDIS_URL'])
with Session() as recovery:
 for pending in recovery.query(Cohort).filter(Cohort.state.in_(['queued','running'])).all():
  pending.state='queued';r.rpush('cohort:jobs',pending.id)
 for pending in recovery.query(Correction).filter(Correction.status=='processing').all():
  r.rpush('correction:jobs',pending.id)
 recovery.commit()
while True:
 Path('/tmp/heartbeat').touch()
 try:
  item=r.blpop(['cohort:jobs','correction:jobs'],timeout=3)
  if not item:continue
  queue=item[0].decode() if isinstance(item[0],bytes) else item[0]
  if queue=='correction:jobs':
   with Session() as s:
    corr=s.get(Correction,int(item[1]))
    if not corr or corr.status!='processing':continue
    try:finalize(s,corr)
    except Exception:s.rollback();logging.exception('correction %s',corr.id)
   continue
  with Session() as s:
   row=s.get(Cohort,int(item[1]))
   if not row or row.state!='queued':continue
   snapshot=row.result['snapshot'];row.state='running';s.commit()
   try:
    row.result={**calculate(snapshot),'snapshot':snapshot};row.state='done'
    Path('/artifacts/'+str(row.id)+'.json').write_text(json.dumps(row.result,ensure_ascii=False))
   except Exception as e:row.state='failed';row.error=str(e)
   s.commit()
 except Exception:logging.exception('worker');time.sleep(2)
