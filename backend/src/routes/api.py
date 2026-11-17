import os,json
from datetime import datetime,date,timezone
import redis
from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from src.config.database import db
from src.models.entities import User,Event,Cohort,Intervention,Audit,Correction,DepartmentAssignment,Transfer
from src.schemas.business import Login,EventInput,CohortInput,InterventionInput,NoteInput,AssignmentInput,CorrectionInput
from src.middlewares.auth import current,editor,admin
from src.utils.security import verify,token
from src.services.business import audit,dump
from src.services.interventions import draft
from src.services.corrections import accept,register
from src.services.departments import resolve_department
from src.controllers.business import ensure_cohort,ensure_intervention
router=APIRouter()
def push(queue,job_id,message):
 try:redis.Redis.from_url(os.environ['REDIS_URL']).rpush(queue,job_id)
 except redis.RedisError:raise HTTPException(503,message)
@router.post('/auth/login')
def login(data:Login,s=Depends(db)):
 u=s.query(User).filter_by(email=data.email).first()
 if not u or not verify(data.password,u.password):raise HTTPException(401,'账号或密码错误')
 return {'token':token(u),'user':dump(u)}
@router.get('/me')
def me(u=Depends(current)):return dump(u)
@router.get('/events')
def events(u=Depends(current),s=Depends(db)):return [dump(r) for r in s.query(Event).order_by(Event.id.desc()).all()]
@router.post('/events')
def event(data:EventInput,u=Depends(editor),s=Depends(db)):
 existing=s.query(Event).filter_by(code=data.code).first()
 if existing:
  if all(getattr(existing,k)==v for k,v in data.model_dump().items()):return dump(existing)
  raise HTTPException(409,'同事件编号的内容冲突，请修订原记录或使用新编号')
 r=Event(**data.model_dump());s.add(r)
 try:s.commit()
 except IntegrityError:
  s.rollback();other=s.query(Event).filter_by(code=data.code).first()
  if other and all(getattr(other,k)==v for k,v in data.model_dump().items()):return dump(other)
  raise HTTPException(409,'同事件编号的内容冲突')
 audit(s,u,'录入学习事件 '+r.code);return dump(r)
@router.put('/events/{i}')
def edit_event(i:int,data:EventInput,u=Depends(editor),s=Depends(db)):
 r=s.get(Event,i)
 if not r:raise HTTPException(404,'事件不存在')
 for k,v in data.model_dump().items():setattr(r,k,v)
 try:s.commit()
 except IntegrityError:s.rollback();raise HTTPException(409,'事件编号重复')
 audit(s,u,'修订学习事件 '+str(i));return dump(r)
@router.get('/cohorts')
def cohorts(u=Depends(current),s=Depends(db)):return [dump(r) for r in s.query(Cohort).order_by(Cohort.id.desc()).all()]
@router.post('/cohorts')
def cohort(data:CohortInput,u=Depends(editor),s=Depends(db)):
 cfg=data.model_dump(mode='json')
 cfg['known_at']=cfg.get('known_at') or datetime.now(timezone.utc).isoformat(timespec='microseconds')
 snapshot={'config':cfg,'events':[dump(r) for r in s.query(Event).order_by(Event.id).all()],'assignments':[dump(r) for r in s.query(DepartmentAssignment).order_by(DepartmentAssignment.id).all()]}
 r=Cohort(**cfg,result={'snapshot':snapshot});s.add(r);s.commit()
 try:redis.Redis.from_url(os.environ['REDIS_URL']).rpush('cohort:jobs',r.id)
 except redis.RedisError:r.state='failed';r.error='队列暂不可用，请稍后重试';s.commit();raise HTTPException(503,r.error)
 audit(s,u,'提交留存队列 '+str(r.id));return dump(r)
@router.get('/cohorts/{i}')
def detail(i:int,u=Depends(current),s=Depends(db)):return dump(ensure_cohort(s,i))
@router.get('/cohorts/{i}/export')
def export(i:int,u=Depends(current),s=Depends(db)):
 r=ensure_cohort(s,i)
 if r.state!='done':raise HTTPException(409,'计算成功后才能导出')
 return Response(json.dumps(dump(r),ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="learning-cohort-{i}.json"'})
@router.get('/interventions')
def interventions(u=Depends(current),s=Depends(db)):return [dump(r) for r in s.query(Intervention).order_by(Intervention.id.desc()).all()]
@router.post('/interventions')
def intervention(data:InterventionInput,u=Depends(editor),s=Depends(db)):
 r=draft(s,ensure_cohort(s,data.cohort_id),data);audit(s,u,'生成干预清单 '+str(r.id));return dump(r)
@router.put('/interventions/{i}')
def edit_intervention(i:int,data:NoteInput,u=Depends(editor),s=Depends(db)):
 r=ensure_intervention(s,i)
 if r.status!='draft':raise HTTPException(409,'已签核清单不可修改')
 r.note=data.note;s.commit();audit(s,u,'修订干预说明 '+str(i));return dump(r)
@router.post('/interventions/{i}/approve')
def approve(i:int,u=Depends(admin),s=Depends(db)):
 ensure_intervention(s,i)
 updated=s.execute(update(Intervention).where(Intervention.id==i,Intervention.status=='draft').values(status='approved')).rowcount
 if not updated:raise HTTPException(409,'已签核，不可重复签核')
 s.commit();audit(s,u,'签核干预清单 '+str(i));return dump(ensure_intervention(s,i))
@router.get('/interventions/{i}/export')
def action_export(i:int,u=Depends(current),s=Depends(db)):
 r=ensure_intervention(s,i);return dump(r)
@router.get('/assignments')
def assignments(learner:str|None=None,u=Depends(current),s=Depends(db)):
 q=s.query(DepartmentAssignment).order_by(DepartmentAssignment.learner,DepartmentAssignment.registered_at,DepartmentAssignment.id)
 if learner:q=q.filter_by(learner=learner)
 return [dump(r) for r in q.all()]
@router.post('/assignments')
def assignment(data:AssignmentInput,u=Depends(editor),s=Depends(db)):
 r=register(s,data);audit(s,u,'登记部门区间 '+r.learner+' '+r.department);return dump(r)
@router.get('/attribution')
def attribution(learner:str,day:date,known_at:str|None=None,u=Depends(current),s=Depends(db)):
 rows=[dump(r) for r in s.query(DepartmentAssignment).filter_by(learner=learner).order_by(DepartmentAssignment.registered_at,DepartmentAssignment.id).all()]
 if known_at:
  try:known=datetime.fromisoformat(known_at.replace('Z','+00:00'))
  except ValueError:raise HTTPException(422,'知悉时点格式无效')
  if known.tzinfo is None:raise HTTPException(422,'知悉时点必须带时区，例如+08:00')
  known=known.astimezone(timezone.utc).isoformat(timespec='microseconds')
 else:known=datetime.now(timezone.utc).isoformat(timespec='microseconds')
 now=datetime.now(timezone.utc).isoformat(timespec='microseconds')
 return {'learner':learner,'day':day.isoformat(),'known_at':known,'department':resolve_department(rows,day,known),'current_department':resolve_department(rows,day,now),'history':rows}
@router.get('/corrections')
def corrections(u=Depends(current),s=Depends(db)):
 out=[]
 for c in s.query(Correction).order_by(Correction.id.desc()).all():
  d=dump(c);d['transfers']=[dump(t) for t in s.query(Transfer).filter_by(correction_id=c.id).order_by(Transfer.id).all()];out.append(d)
 return out
@router.post('/corrections')
def correction(data:CorrectionInput,u=Depends(editor),s=Depends(db)):
 r=accept(s,data)
 try:redis.Redis.from_url(os.environ['REDIS_URL']).rpush('correction:jobs',r.id)
 except redis.RedisError:raise HTTPException(503,'更正已受理为处理中；任务队列暂不可用，请稍后重试转交')
 audit(s,u,'受理调岗更正 '+str(r.id)+' '+r.learner);return dump(r)
@router.post('/corrections/{i}/retry')
def retry_correction(i:int,u=Depends(editor),s=Depends(db)):
 r=s.get(Correction,i)
 if not r:raise HTTPException(404,'更正单不存在')
 if r.status=='effective':return dump(r)
 push('correction:jobs',r.id,'任务队列暂不可用，请稍后重试')
 audit(s,u,'重试调岗更正 '+str(i));return dump(r)
@router.get('/audits')
def audits(u=Depends(admin),s=Depends(db)):return [dump(r) for r in s.query(Audit).order_by(Audit.id.desc()).limit(100)]
