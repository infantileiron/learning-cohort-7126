from datetime import datetime,date,timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
import hashlib,json
from src.services.departments import resolve_department
TZ=ZoneInfo('Asia/Shanghai')
def monday(day):return day-timedelta(days=day.weekday())
def calculate(snapshot):
 cfg=snapshot['config'];as_of=date.fromisoformat(cfg['as_of']);start=date.fromisoformat(cfg['start_week']);end=date.fromisoformat(cfg['end_week']);horizon=cfg['horizon']
 known_at=cfg.get('known_at');assignments=snapshot.get('assignments',[])
 weeks=defaultdict(set);first_day={};future=0
 for event in snapshot['events']:
  ts=datetime.fromisoformat(event['occurred_at'].replace('Z','+00:00'))
  if ts.tzinfo is None:raise ValueError('事件缺少时区')
  day=ts.astimezone(TZ).date()
  if day>as_of:future+=1;continue
  weeks[event['learner']].add(monday(day))
  if event['learner'] not in first_day or day<first_day[event['learner']]:first_day[event['learner']]=day
 if not weeks:raise ValueError('截至日以前没有有效学习事件，请核对时间和输入')
 first={learner:min(ws) for learner,ws in weeks.items()}
 cohorts=defaultdict(list)
 for learner,week in first.items():
  if start<=week<=end:cohorts[week].append(learner)
 if not cohorts:raise ValueError('所选首学周没有队列；不会将窗口前老学员重置为新学员')
 by_learner=defaultdict(list)
 for a in assignments:by_learner[a['learner']].append(a)
 attribution={learner:resolve_department(by_learner.get(learner,[]),first_day[learner],known_at) for members in cohorts.values() for learner in members}
 rows=[]
 for week in sorted(cohorts):
  members=sorted(cohorts[week]);cells=[];departments=defaultdict(int);unknown=0
  for learner in members:
   if attribution[learner] is None:unknown+=1
   else:departments[attribution[learner]]+=1
  for i in range(horizon+1):
   target=week+timedelta(weeks=i);mature=target+timedelta(days=6)<=as_of
   active=sorted(x for x in members if target in weeks[x])
   cells.append(dict(week_index=i,target_week=target.isoformat(),mature=mature,active=len(active) if mature else None,rate=len(active)/len(members) if mature else None,visited=active if mature else [],missing=[x for x in members if x not in active] if mature else []))
  rows.append(dict(cohort_week=week.isoformat(),iso_label=f'{week.isocalendar().year}-W{week.isocalendar().week:02}',size=len(members),members=members,departments=dict(sorted(departments.items())),unknown=unknown,cells=cells))
 learners=sum(r['size'] for r in rows);dept_totals=defaultdict(int);unknown_learners=[]
 for learner,dept in attribution.items():
  if dept is None:unknown_learners.append(learner)
  else:dept_totals[dept]+=1
 reconciliation=dict(department_totals=dict(sorted(dept_totals.items())),attributed=sum(dept_totals.values()),unknown_count=len(unknown_learners),unknown_learners=sorted(unknown_learners),cohort_learners=learners,site_learners=len(weeks),balanced=sum(dept_totals.values())+len(unknown_learners)==learners)
 return dict(rows=rows,learners=learners,unique_learners_before_cutoff=len(weeks),future_events_excluded=future,event_count=len(snapshot['events']),week_hits=sum(len(v) for v in weeks.values()),as_of=cfg['as_of'],timezone='Asia/Shanghai',known_at=known_at,attribution=attribution,first_days={learner:first_day[learner].isoformat() for learner in attribution},reconciliation=reconciliation,checksum=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),method='按Asia/Shanghai业务日归入ISO周一；先用截至日以前全部历史找首学周，再筛选队列范围。分母=该首学周唯一学员数；每人每周回访最多计1次。目标周周日≤截至日才成熟；未成熟显示null，成熟无回访显示0。未成熟列禁止生成干预。队列分母按首学日所属部门固定，后续周回访沿用该部门；归属按方案知悉时点还原登记记录，未知归属单列并与队列总人数对账。已冻结结果不受后续调岗更正影响。')
