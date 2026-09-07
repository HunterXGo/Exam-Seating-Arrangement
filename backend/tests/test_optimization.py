from types import SimpleNamespace as O
from app.optimization import solve, roll_value
def seat(i,r,c,available=True,accessible=False): return O(id=i,classroom_id=1,row=r,column=c,available=available,accessible=accessible,front_row=r==1,near_door=False)
def student(i,dept='CSE',req=None): return O(id=i,roll_number=f'CSE23{i:03}',department=dept,accessibility_requirement=req)
def config(): return O(department_weight=10,roll_weight=5,roll_threshold=5,horizontal=True,vertical=True,diagonal=False,time_limit=2,workers=1,random_seed=1)
def test_basic_assignment(): assert solve([student(i) for i in range(4)],[seat(i,i//2+1,i%2+1) for i in range(4)],config())['students_assigned']==4
def test_insufficient_capacity(): assert solve([student(i) for i in range(2)],[seat(1,1,1)],config())['status']=='INFEASIBLE'
def test_unavailable_never_used():
 r=solve([student(1)],[seat(1,1,1,False),seat(2,1,2)],config()); assert r['assignments'][0][1].id==2
def test_accessibility():
 r=solve([student(1,req='wheelchair')],[seat(1,1,1),seat(2,1,2,accessible=True)],config()); assert r['assignments'][0][1].id==2
def test_roll_parse(): assert roll_value('CSE-A-23001')==23001 and roll_value('NONE') is None
