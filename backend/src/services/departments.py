from datetime import datetime,date
def _dt(v):
 d=datetime.fromisoformat(v.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError('时间必须带时区')
 return d
def resolve_department(assignments,on_day,known_at=None):
 """按所选知悉时点还原工号归属：只看待知悉时点(registered_at<=known_at)前登记的区间，
 在覆盖on_day的区间中取登记时间最新者（并列取id最大者）。
 追溯更正的新区间只覆盖其生效段，段外仍由旧登记接管，即追溯拆分；未知归属返回None。"""
 if isinstance(on_day,str):on_day=date.fromisoformat(on_day)
 known=_dt(known_at) if known_at else None
 best=None
 for a in assignments:
  registered=_dt(a['registered_at'])
  if known and registered>known:continue
  start=date.fromisoformat(a['valid_from']);end=date.fromisoformat(a['valid_to']) if a.get('valid_to') else None
  if start<=on_day and (end is None or on_day<=end):
   key=(registered,a.get('id') or 0)
   if best is None or key>best[0]:best=(key,a['department'])
 return best[1] if best else None
