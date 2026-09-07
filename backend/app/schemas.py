from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
class StudentIn(BaseModel): roll_number:str; name:str; department:str; year:Optional[str]=None; section:Optional[str]=None; accessibility_requirement:Optional[str]=None
class StudentOut(StudentIn): id:int
class SeatIn(BaseModel): row:int=Field(ge=1); column:int=Field(ge=1); available:bool=True; accessible:bool=False; front_row:bool=False; near_door:bool=False
class SeatOut(SeatIn): id:int; classroom_id:int
class ClassroomIn(BaseModel): name:str; building:Optional[str]=None; floor:Optional[str]=None; rows:int=Field(gt=0,le=100); columns:int=Field(gt=0,le=100)
class ClassroomOut(ClassroomIn): id:int; seats:list[SeatOut]=[]
class ExamIn(BaseModel): name:str; scheduled_at:Optional[datetime]=None; student_ids:list[int]=[]; classroom_ids:list[int]=[]
class ExamOut(BaseModel): id:int; name:str; scheduled_at:Optional[datetime]=None; student_ids:list[int]=[]; classroom_ids:list[int]=[]
class GenerateIn(BaseModel): exam_id:int; department_weight:int=10; roll_weight:int=5; spacing_weight:int=0; utilization_weight:int=0; roll_threshold:int=5; minimum_spacing:int=0; horizontal:bool=True; vertical:bool=True; diagonal:bool=False; time_limit:float=10; workers:int=4; random_seed:int=0
