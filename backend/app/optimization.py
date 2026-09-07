import re, time
from ortools.sat.python import cp_model

def roll_value(value):
    parts=re.findall(r'\d+', value or '')
    return int(''.join(parts)) if parts else None
def solve(students, seats, config):
    reasons=[]
    usable=[q for q in seats if q.available]
    if len(usable)<len(students): reasons.append(f'Required seats: {len(students)}; available seats: {len(usable)}')
    for s in students:
        req=(s.accessibility_requirement or '').lower()
        compatible=[q for q in usable if (not req or ('wheelchair' not in req or q.accessible) and ('front' not in req or q.front_row) and ('door' not in req or q.near_door))]
        if not compatible: reasons.append(f'No compatible seat for {s.roll_number}')
    if reasons: return {'status':'INFEASIBLE','message':'No valid seating arrangement exists.','reasons':reasons}
    model=cp_model.CpModel(); x={}
    for i,s in enumerate(students):
        req=(s.accessibility_requirement or '').lower()
        valid=[]
        for j,q in enumerate(usable):
            ok=('wheelchair' not in req or q.accessible) and ('front' not in req or q.front_row) and ('door' not in req or q.near_door)
            if ok: x[i,j]=model.NewBoolVar(f'x_{i}_{j}'); valid.append(x[i,j])
        model.AddExactlyOne(valid)
    for j in range(len(usable)): model.AddAtMostOne(x[i,j] for i in range(len(students)) if (i,j) in x)
    penalties=[]; conflict_vars=[]
    for a in range(len(usable)):
      for b in range(a+1,len(usable)):
        qa,qb=usable[a],usable[b]
        if qa.classroom_id != qb.classroom_id: continue
        dr,dc=abs(qa.row-qb.row),abs(qa.column-qb.column)
        neighbor=(config.horizontal and dr==0 and dc==1) or (config.vertical and dr==1 and dc==0) or (config.diagonal and dr==1 and dc==1)
        if not neighbor: continue
        for i in range(len(students)):
          for k in range(i+1,len(students)):
            if (i,a) not in x or (k,b) not in x or (i,b) not in x or (k,a) not in x: continue
            pair=model.NewBoolVar(f'n_{i}_{k}_{a}_{b}'); model.Add(pair <= x[i,a]); model.Add(pair <= x[k,b]); model.Add(pair >= x[i,a]+x[k,b]-1)
            rev=model.NewBoolVar(f'nr_{i}_{k}_{a}_{b}'); model.Add(rev <= x[i,b]); model.Add(rev <= x[k,a]); model.Add(rev >= x[i,b]+x[k,a]-1)
            same=students[i].department==students[k].department
            near=roll_value(students[i].roll_number) is not None and roll_value(students[k].roll_number) is not None and abs(roll_value(students[i].roll_number)-roll_value(students[k].roll_number))<=config.roll_threshold
            if same: penalties += [config.department_weight*pair, config.department_weight*rev]; conflict_vars += [(pair,'department'),(rev,'department')]
            if near: penalties += [config.roll_weight*pair, config.roll_weight*rev]; conflict_vars += [(pair,'roll'),(rev,'roll')]
    model.Minimize(sum(penalties) if penalties else 0); solver=cp_model.CpSolver(); solver.parameters.max_time_in_seconds=config.time_limit; solver.parameters.num_search_workers=config.workers; solver.parameters.random_seed=config.random_seed
    started=time.time(); status=solver.Solve(model); elapsed=time.time()-started
    label={cp_model.OPTIMAL:'OPTIMAL',cp_model.FEASIBLE:'FEASIBLE',cp_model.INFEASIBLE:'INFEASIBLE',cp_model.UNKNOWN:'UNKNOWN'}.get(status,'UNKNOWN')
    if label not in ('OPTIMAL','FEASIBLE'): return {'status':label,'message':'Solver did not produce a valid arrangement.','reasons':[]}
    assignments=[(students[i],usable[j]) for (i,j),v in x.items() if solver.Value(v)]
    d=sum(solver.Value(v) for v,t in conflict_vars if t=='department'); r=sum(solver.Value(v) for v,t in conflict_vars if t=='roll')
    return {'status':label,'objective_value':int(solver.ObjectiveValue()),'assignments':assignments,'students_assigned':len(assignments),'rooms_used':len({q.classroom_id for _,q in assignments}),'unused_seats':len(usable)-len(assignments),'department_conflicts':d,'roll_number_conflicts':r,'solve_time_seconds':round(elapsed,3)}
