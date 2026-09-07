from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from .database import Base, engine, get_db
from .models import Student, Classroom, Seat, Exam, Arrangement, Assignment
from .schemas import *
from .optimization import solve
import csv, io, json

Base.metadata.create_all(engine)
app=FastAPI(title='Exam Seating API')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])
def one(db, cls, id):
 o=db.get(cls,id)
 if not o: raise HTTPException(404,detail='Record not found')
 return o
def student_out(s): return StudentOut.model_validate(s,from_attributes=True)
def classroom_out(c): return ClassroomOut(id=c.id,name=c.name,building=c.building,floor=c.floor,rows=c.rows,columns=c.columns,seats=[SeatOut.model_validate(x,from_attributes=True) for x in c.seats])
def exam_out(e): return ExamOut(id=e.id,name=e.name,scheduled_at=e.scheduled_at,student_ids=[s.id for s in e.students],classroom_ids=[c.id for c in e.classrooms])
@app.get('/health')
def health(): return {'ok':True}
@app.get('/api/students',response_model=list[StudentOut])
def students(search:str|None=None,db:Session=Depends(get_db)):
 q=db.query(Student)
 if search: q=q.filter((Student.name.contains(search)) | (Student.roll_number.contains(search)))
 return [student_out(x) for x in q.order_by(Student.roll_number).all()]
@app.post('/api/students',response_model=StudentOut,status_code=201)
def add_student(data:StudentIn,db:Session=Depends(get_db)):
 s=Student(**data.model_dump()); db.add(s)
 try: db.commit(); db.refresh(s)
 except IntegrityError: db.rollback(); raise HTTPException(409,detail='Roll number already exists')
 return student_out(s)
@app.get('/api/students/{id}',response_model=StudentOut)
def get_student(id:int,db:Session=Depends(get_db)): return student_out(one(db,Student,id))
@app.put('/api/students/{id}',response_model=StudentOut)
def update_student(id:int,data:StudentIn,db:Session=Depends(get_db)):
 s=one(db,Student,id)
 for k,v in data.model_dump().items(): setattr(s,k,v)
 db.commit(); return student_out(s)
@app.delete('/api/students/{id}',status_code=204)
def delete_student(id:int,db:Session=Depends(get_db)): db.delete(one(db,Student,id));db.commit()
@app.get('/api/classrooms',response_model=list[ClassroomOut])
def classrooms(db:Session=Depends(get_db)): return [classroom_out(x) for x in db.query(Classroom).options(joinedload(Classroom.seats)).all()]
@app.post('/api/classrooms',response_model=ClassroomOut,status_code=201)
def add_classroom(data:ClassroomIn,db:Session=Depends(get_db)):
 c=Classroom(**data.model_dump());db.add(c);db.flush()
 for r in range(1,c.rows+1):
  for col in range(1,c.columns+1): db.add(Seat(classroom_id=c.id,row=r,column=col,front_row=r==1))
 db.commit();db.refresh(c);return classroom_out(c)
@app.get('/api/classrooms/{id}',response_model=ClassroomOut)
def get_classroom(id:int,db:Session=Depends(get_db)): return classroom_out(one(db,Classroom,id))
@app.put('/api/classrooms/{id}',response_model=ClassroomOut)
def update_classroom(id:int,data:ClassroomIn,db:Session=Depends(get_db)):
 c=one(db,Classroom,id)
 if (c.rows,c.columns)!=(data.rows,data.columns): raise HTTPException(400,detail='Create a new room to change grid dimensions')
 for k,v in data.model_dump().items():setattr(c,k,v)
 db.commit();return classroom_out(c)
@app.delete('/api/classrooms/{id}',status_code=204)
def delete_classroom(id:int,db:Session=Depends(get_db)): db.delete(one(db,Classroom,id));db.commit()
@app.put('/api/classrooms/{classroom_id}/seats/{seat_id}',response_model=SeatOut)
def update_seat(classroom_id:int,seat_id:int,data:SeatIn,db:Session=Depends(get_db)):
 q=one(db,Seat,seat_id)
 if q.classroom_id!=classroom_id: raise HTTPException(404,detail='Seat not in classroom')
 for k,v in data.model_dump().items():setattr(q,k,v)
 db.commit();return SeatOut.model_validate(q,from_attributes=True)
@app.get('/api/exams',response_model=list[ExamOut])
def exams(db:Session=Depends(get_db)): return [exam_out(x) for x in db.query(Exam).all()]
@app.post('/api/exams',response_model=ExamOut,status_code=201)
def add_exam(data:ExamIn,db:Session=Depends(get_db)):
 e=Exam(name=data.name,scheduled_at=data.scheduled_at);e.students=[one(db,Student,x) for x in data.student_ids];e.classrooms=[one(db,Classroom,x) for x in data.classroom_ids];db.add(e);db.commit();db.refresh(e);return exam_out(e)
@app.get('/api/exams/{id}',response_model=ExamOut)
def get_exam(id:int,db:Session=Depends(get_db)): return exam_out(one(db,Exam,id))
@app.put('/api/exams/{id}',response_model=ExamOut)
def update_exam(id:int,data:ExamIn,db:Session=Depends(get_db)):
 e=one(db,Exam,id);e.name=data.name;e.scheduled_at=data.scheduled_at;e.students=[one(db,Student,x) for x in data.student_ids];e.classrooms=[one(db,Classroom,x) for x in data.classroom_ids];db.commit();return exam_out(e)
@app.delete('/api/exams/{id}',status_code=204)
def delete_exam(id:int,db:Session=Depends(get_db)): db.delete(one(db,Exam,id));db.commit()
@app.post('/api/seating/generate')
def generate(data:GenerateIn,db:Session=Depends(get_db)):
 e=one(db,Exam,data.exam_id); seats=[s for c in e.classrooms for s in c.seats]; result=solve(e.students,seats,data)
 if result['status'] not in ('OPTIMAL','FEASIBLE'): return result
 old=db.query(Arrangement).filter_by(exam_id=e.id).first()
 if old: db.delete(old);db.flush()
 a=Arrangement(exam_id=e.id,status=result['status'],objective_value=result['objective_value'],statistics=json.dumps({k:v for k,v in result.items() if k!='assignments'}));db.add(a);db.flush()
 for s,q in result['assignments']: db.add(Assignment(arrangement_id=a.id,student_id=s.id,seat_id=q.id))
 db.commit(); return {k:v for k,v in result.items() if k!='assignments'}
@app.get('/api/seating/{exam_id}')
def arrangement(exam_id:int,db:Session=Depends(get_db)):
 a=db.query(Arrangement).filter_by(exam_id=exam_id).first()
 if not a: raise HTTPException(404,detail='No arrangement generated')
 rows=[]
 for x in a.assignments:
  s=one(db,Student,x.student_id);q=one(db,Seat,x.seat_id);c=one(db,Classroom,q.classroom_id);rows.append({'student':student_out(s).model_dump(),'classroom':c.name,'seat_id':q.id,'row':q.row,'column':q.column})
 return {'statistics':json.loads(a.statistics),'assignments':rows}
@app.delete('/api/seating/{exam_id}',status_code=204)
def delete_arrangement(exam_id:int,db:Session=Depends(get_db)):
 a=db.query(Arrangement).filter_by(exam_id=exam_id).first()
 if a:db.delete(a);db.commit()
@app.get('/api/seating/{exam_id}/export')
def export(exam_id:int,db:Session=Depends(get_db)):
 data=arrangement(exam_id,db);out=io.StringIO(); w=csv.writer(out);w.writerow(['Student Name','Roll Number','Department','Classroom','Seat','Row','Column'])
 for x in data['assignments']: w.writerow([x['student']['name'],x['student']['roll_number'],x['student']['department'],x['classroom'],f"R{x['row']}C{x['column']}",x['row'],x['column']])
 return StreamingResponse(iter([out.getvalue()]),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename=seating-{exam_id}.csv'})
