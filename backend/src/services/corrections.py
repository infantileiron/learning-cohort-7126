from datetime import datetime,timezone
from sqlalchemy import update
from src.models.entities import Correction,DepartmentAssignment,Intervention,Transfer,Cohort
from src.services.departments import resolve_department
def now():return datetime.now(timezone.utc).isoformat(timespec='microseconds')
def register(s,data,note='部门区间登记',correction_id=None,at=None):
 a=DepartmentAssignment(learner=data.learner,department=data.department,valid_from=data.valid_from.isoformat(),valid_to=data.valid_to.isoformat() if data.valid_to else None,registered_at=at or now(),correction_id=correction_id,note=note)
 s.add(a);s.commit();return a
def accept(s,data):
 """受理调岗更正：登记追溯区间（保留更正前认知），更正单置处理中，转交齐全后才生效。"""
 ts=now()
 corr=Correction(learner=data.learner,department=data.department,valid_from=data.valid_from.isoformat(),valid_to=data.valid_to.isoformat() if data.valid_to else None,registered_at=ts,status='processing')
 s.add(corr);s.flush()
 s.add(DepartmentAssignment(learner=corr.learner,department=corr.department,valid_from=corr.valid_from,valid_to=corr.valid_to,registered_at=ts,correction_id=corr.id,note='调岗更正登记'))
 s.commit();return corr
def finalize(s,corr):
 """把更正学员在未签核辅导中的归属转交为最新有效归属；已签核辅导保留原归属。
 幂等：同一更正重试不新增转交；全部转交齐全后更正单置为已生效。"""
 if corr.status=='effective':return corr
 ts=now()
 rows=s.query(DepartmentAssignment).filter_by(learner=corr.learner).all()
 assignments=[dict(id=a.id,department=a.department,valid_from=a.valid_from,valid_to=a.valid_to,registered_at=a.registered_at) for a in rows]
 for iv in s.query(Intervention).filter(Intervention.status=='draft').all():
  att=dict(iv.attributions or {})
  if corr.learner not in att:continue
  cohort=s.get(Cohort,iv.cohort_id)
  first_day=((cohort.result or {}).get('first_days') or {}).get(corr.learner)
  if not first_day:continue
  new_dept=resolve_department(assignments,first_day,ts)
  old_dept=att.get(corr.learner)
  if old_dept==new_dept:continue
  att[corr.learner]=new_dept
  updated=s.execute(update(Intervention).where(Intervention.id==iv.id,Intervention.status=='draft').values(attributions=att)).rowcount
  if not updated:continue
  if not s.query(Transfer).filter_by(correction_id=corr.id,intervention_id=iv.id,learner=corr.learner).first():
   s.add(Transfer(correction_id=corr.id,intervention_id=iv.id,learner=corr.learner,from_department=old_dept,to_department=new_dept,created=ts))
 corr.status='effective';s.commit();return corr
