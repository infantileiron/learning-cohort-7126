from sqlalchemy import Column,Integer,String,JSON,Text,ForeignKey,UniqueConstraint
from src.config.database import Base
class User(Base):
 __tablename__='users'
 id=Column(Integer,primary_key=True);email=Column(String(100),unique=True,nullable=False);password=Column(String(200));role=Column(String(20))
class Event(Base):
 __tablename__='events'
 id=Column(Integer,primary_key=True);code=Column(String(60),unique=True,nullable=False);learner=Column(String(60),nullable=False,index=True);occurred_at=Column(String(40),nullable=False);course=Column(String(40));note=Column(Text,default='')
class Cohort(Base):
 __tablename__='cohorts'
 id=Column(Integer,primary_key=True);name=Column(String(100));start_week=Column(String(10));end_week=Column(String(10));as_of=Column(String(10));horizon=Column(Integer);known_at=Column(String(40));state=Column(String(20),default='queued');result=Column(JSON,nullable=True);error=Column(Text,default='')
class Intervention(Base):
 __tablename__='interventions'
 id=Column(Integer,primary_key=True);cohort_id=Column(Integer,ForeignKey('cohorts.id'));cohort_week=Column(String(10));week_index=Column(Integer);note=Column(Text);members=Column(JSON);attributions=Column(JSON,nullable=True);status=Column(String(20),default='draft')
class Correction(Base):
 __tablename__='corrections'
 id=Column(Integer,primary_key=True);learner=Column(String(60),nullable=False,index=True);department=Column(String(60),nullable=False);valid_from=Column(String(10),nullable=False);valid_to=Column(String(10),nullable=True);registered_at=Column(String(40),nullable=False);status=Column(String(20),default='processing')
class DepartmentAssignment(Base):
 __tablename__='department_assignments'
 id=Column(Integer,primary_key=True);learner=Column(String(60),nullable=False,index=True);department=Column(String(60),nullable=False);valid_from=Column(String(10),nullable=False);valid_to=Column(String(10),nullable=True);registered_at=Column(String(40),nullable=False);correction_id=Column(Integer,ForeignKey('corrections.id'),nullable=True);note=Column(Text,default='')
class Transfer(Base):
 __tablename__='transfers'
 id=Column(Integer,primary_key=True);correction_id=Column(Integer,ForeignKey('corrections.id'),nullable=False);intervention_id=Column(Integer,ForeignKey('interventions.id'),nullable=False);learner=Column(String(60),nullable=False);from_department=Column(String(60),nullable=True);to_department=Column(String(60),nullable=True);created=Column(String(40))
 __table_args__=(UniqueConstraint('correction_id','intervention_id','learner',name='uq_transfer'),)
class Audit(Base):
 __tablename__='audits'
 id=Column(Integer,primary_key=True);actor=Column(String(100));action=Column(String(200));created=Column(String(40))
