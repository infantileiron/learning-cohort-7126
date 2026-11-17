from datetime import datetime,date,timezone,timedelta
from pydantic import BaseModel,Field,field_validator,model_validator
from typing import Literal
class Login(BaseModel):email:str;password:str
class EventInput(BaseModel):
 code:str=Field(min_length=1,max_length=60)
 learner:str=Field(min_length=1,max_length=60)
 occurred_at:str
 course:Literal['数据素养','服务沟通','安全规范']
 note:str=Field(default='',max_length=1000)
 @field_validator('occurred_at')
 @classmethod
 def timestamp(cls,v):
  d=datetime.fromisoformat(v.replace('Z','+00:00'))
  if d.tzinfo is None:raise ValueError('事件时间必须带时区，例如+08:00')
  return d.astimezone(timezone.utc).isoformat(timespec='seconds')
def awareness_time(v):
 if v in (None,''):return None
 d=datetime.fromisoformat(v.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError('知悉时点必须带时区，例如+08:00')
 d=d.astimezone(timezone.utc)
 if d>datetime.now(timezone.utc)+timedelta(minutes=5):raise ValueError('知悉时点不能晚于当前时间')
 return d.isoformat(timespec='microseconds')
class CohortInput(BaseModel):
 name:str=Field(min_length=2,max_length=100)
 start_week:date;end_week:date;as_of:date
 horizon:int=Field(default=5,ge=1,le=8)
 known_at:str|None=None
 @field_validator('known_at')
 @classmethod
 def awareness(cls,v):return awareness_time(v)
 @model_validator(mode='after')
 def windows(self):
  if self.start_week.weekday()!=0 or self.end_week.weekday()!=0:raise ValueError('队列起止周必须是ISO周一')
  if self.start_week>self.end_week or self.end_week>self.as_of:raise ValueError('起周≤止周≤截至日')
  if (self.end_week-self.start_week).days>365:raise ValueError('小型项目队列窗口最多一年')
  return self
class AssignmentInput(BaseModel):
 learner:str=Field(min_length=1,max_length=60)
 department:Literal['客服一部','客服二部','运营支持部','数据洞察组']
 valid_from:date
 valid_to:date|None=None
 @model_validator(mode='after')
 def window(self):
  if self.valid_to and self.valid_to<self.valid_from:raise ValueError('生效止日不能早于生效起日')
  return self
class CorrectionInput(AssignmentInput):pass
class InterventionInput(BaseModel):
 cohort_id:int=Field(gt=0)
 cohort_week:str=Field(min_length=10,max_length=10)
 week_index:int=Field(ge=1,le=8)
 note:str=Field(min_length=8,max_length=2000)
class NoteInput(BaseModel):note:str=Field(min_length=8,max_length=2000)
