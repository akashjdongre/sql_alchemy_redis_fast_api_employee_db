from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from db import get_db
from typing import Optional

from model_employee import Employee, EmployeeResponse, EmployeeWrapper, EmployeesWrapper, DeptEmployeeWrapper
from model_attendance import Attendance, AttendSummaryWrapper, EmpAttendSummaryTest
from model_payroll import Payroll, PayrollWrapper
from model_departments import Departments

from redis_config import redis_client
import json
from schemas import EmployeeCreate, EmployeeUpdate, EmployeeAttendSummary, EmployeeSearch

app = FastAPI()


#---------------------------- LOGIN ------------------------------#

@app.get("/login")
def user_login():
	
	data = {
		"msg":"Hello User Login"
	}
	return data

#---------------- Get all employees with pagination -----------------#

@app.get("/employees", response_model=EmployeesWrapper) #-- The returned response MUST match EmployeesWrapper schema
def read_employees(
	    page: int = 1,
	    limit: int = 3,
	    db: Session = Depends(get_db)
	):

    cache_key = f"employees:{page}:{limit}"

    # STEP 1 → Check Redis Cache
    try:
        cached_data = redis_client.get(cache_key)
    except Exception:
        cached_data = None

    if cached_data:
        return {
            "source": "redis-cache",
            "data": json.loads(cached_data),
            "count": len(cached_data)
        }

    # STEP 2 → Fetch From MySQL
    offset = (page - 1) * limit

    employees = db.query(Employee).offset(offset).limit(limit).all()

    # STEP 3 → Store In Redis Cache

    employee_list = []
    for emp in employees:
        employee_list.append({
            "employee_id": emp.employee_id,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "email": emp.email,
            "phone": emp.phone
        })

    try:
        redis_client.set(cache_key, json.dumps(employee_list), ex=60)
    except Exception:
        pass

    return {
        "source": "mysql",
        "data": employee_list,
        "count": len(employee_list)
    }

#---------------------- Get employee by ID ----------------------#

@app.get("/employee/{employee_id}", response_model=EmployeeWrapper)
def read_employee(
    employee_id: int,
    db: Session = Depends(get_db)
	):

    cache_key = f"employee:{employee_id}"

    # STEP 1 → Check For Redis Cache
    try:
        cached_data = redis_client.get(cache_key)
    except Exception:
        cached_data = None

    if cached_data:
        return {
		    "source": "redis-cache",
		    "data": json.loads(cached_data)
		}

    # STEP 2 → Fetch From MySQL
    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee_data = {
        "employee_id": employee.employee_id,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "phone": employee.phone,
        "salary": float(employee.salary),
    }

    # STEP 3 → Store In Redis Cache
    try:
        redis_client.set(cache_key, json.dumps(employee_data), ex=60)
    except Exception:
        pass

    return {
		    "source": "db",
		    "data": employee_data
	}

#------------------------ CREATE EMPLOYEE ------------------------------#

@app.post("/employees")
def create_employee(
		employee: EmployeeCreate,
		db: Session = Depends(get_db)
	):
	
	#----------------- CHECK IF Employee with Email is exist --------------------#

	existing_employee = (
	    db.query(Employee)
	    .filter(Employee.email == employee.email)
	    .first()
	)

	if existing_employee:
		return {
		"error": f"Email '{employee.email}' already exists"
	}

	new_employee = Employee(
			first_name=employee.first_name,
	        last_name=employee.last_name,
	        email=employee.email,
	        phone=employee.phone,
	        job_title=employee.job_title,
	        salary=employee.salary,
	        manager_id=employee.manager_id,
	        status=employee.status,
	        hire_date=employee.hire_date,
	        department_id=employee.department_id
		)
	db.add(new_employee)
	db.commit()
	db.refresh(new_employee)

	return {
		"message": "Employee created successfully",
		"data": new_employee
	}

#------------------------ UPDATE EMPLOYEE ------------------------------#

@app.put("/employees/{emp_id}")
def update_employee(
		emp_id : int,
		emp_update : EmployeeUpdate,
		db: Session = Depends(get_db)
	):
	
	#----------------- CHECK IF Employee with Email is exist --------------------#

	existing_employee = get_employee_or_404(emp_id, db)

	if emp_update.first_name is not None:
		existing_employee.first_name = emp_update.first_name

	if emp_update.last_name is not None:
		existing_employee.last_name = emp_update.last_name

	if emp_update.email is not None:
		existing_employee.email = emp_update.email

	if emp_update.phone is not None:
		existing_employee.phone = emp_update.phone
		
	db.commit()
	db.refresh(existing_employee)

	return {
		"message": "Employee updated successfully",
		"data": existing_employee
	}


#-------------------- DELETE (Soft Delete Employee) --------------------#

@app.delete("/employees/{emp_id}")
def delete_employee(
	emp_id : int,
	db: Session = Depends(get_db)
	):
	
	existing_employee = get_employee_or_404(emp_id, db)
	
	existing_employee.status = 'Inactive'
	db.commit()
	db.refresh(existing_employee)

	return {
		"message": "Employee Deleted (soft) successfully."
	}

#------------- Employee Attendance Summary ----------------#

@app.get("/attendance/summary/{emp_id}", response_model=AttendSummaryWrapper)
def attendance_summary_employee(
		emp_id : int,
		db: Session = Depends(get_db)
	):
	
	cache_key = f"attSumEmployee:{emp_id}"

	try:
		cached_data = redis_client.get(cache_key)
	except Exception:
		cached_data = None

	if cached_data:
		return {
			"source":"redis-cache",
			"data":json.loads(cached_data)
		}

	employee = get_employee_or_404(emp_id, db)

	# STEP 2 → Fetch From MySQL

	rows = db.query(
	    Attendance.status,
	    func.count().label("attend_count")
	).filter(
	    Attendance.employee_id == emp_id
	).group_by(
	    Attendance.status
	).all()

	counts = {r.status.lower().replace(" ", "_"): r.attend_count for r in rows}
	attendace_data = {
	    "employee_id": emp_id,
	    "present":  counts.get("present", 0),
	    "absent":   counts.get("absent", 0),
	    "half_day": counts.get("half_day", 0),
	    "late":     counts.get("late", 0),
	}

	# STEP 3 → Store In Redis Cache
	try:
		redis_client.set(cache_key, json.dumps(attendace_data), ex=60)
	except Exception:
		pass

	return {
	 "source": "db",
	 "data": attendace_data
	}

#-------------- Monthly Salary API ------------------#

@app.get("/payroll/monthly/{emp_id}", response_model=PayrollWrapper)
def getEmployeeNetSalary(
	emp_id: int,
    db: Session = Depends(get_db)
	):
	
	cache_key = f"empNetSalary:{emp_id}"
	try:
		cached_data = redis_client.get(cache_key)
	except Exception:
		cached_data = None
	if cached_data:
		return {
			"source":"redis-cache",
			"data":json.loads(cached_data)
		}

	employee = get_employee_or_404(emp_id, db)

	payroll_data = db.query(Payroll).filter(Payroll.employee_id == emp_id).all()

	net_salary = (payroll_data[0].basic_salary + payroll_data[0].bonus) - payroll_data[0].deductions

	payroll_data = {
		"employee_id": emp_id,
		"net_salary": net_salary
	}

	try:
		redis_client.set(cache_key, json.dumps(payroll_data), ex=60)
	except Exception:
		pass

	return {
	    "source": "db",
	    "data": payroll_data
	}


#----------------- Search Employee ---------------------#

@app.get("/employees/search")
def search_employees(
    name: Optional[str] = None,
    email: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
	):	

    query = db.query(Employee)

    filters = []

    if name:
        filters.append(Employee.first_name.ilike(f"%{name}%"))

    if email:
        filters.append(Employee.email.ilike(f"%{email}%"))

    if status:
        filters.append(Employee.status.ilike(f"%{status}%"))

    if filters:
        query = query.filter(or_(*filters))

    search_result = query.all()

    return search_result

#--------------------- Department-wise Employees ----------------------#

@app.get("/departments/{emp_id}/employees", response_model=DeptEmployeeWrapper)
def getDepartmentEmployees(emp_id: int,db: Session = Depends(get_db)):

	cache_key = f"deptEmployee:{emp_id}"

	try:
		cached_data = redis_client.get(cache_key)
	except Exception:
		cached_data = None

	if cached_data:
		return {
			"source":"redis-cache",
			"data":json.loads(cached_data)
		}
	
	result = (
		db.query(
		Employee.first_name,
        Employee.last_name,
        Employee.email,
        Employee.phone,
        Employee.job_title,
        Departments.department_name
		)
		.join(
			Departments,
			Employee.department_id == Departments.department_id
		)
		.filter(
			Employee.department_id == emp_id
		)
		.all()
	)


	empSearchData = [
		{
			"first_name": r.first_name,
			"last_name": r.last_name,
			"email": r.email,
			"phone": r.phone,
			"job_title": r.job_title,
			"department_name": r.department_name,
		}
		for r in result 
	] if len(result) > 0 else { "No Data Found." }


	try:
		redis_client.set(cache_key, json.dumps(empSearchData), ex=60)
	except Exception:
		pass

	return {
		    "source": "db",
		    "data": empSearchData
		}


#------------------- Attendance Percentage API ---------------------#

@app.get("/attendance/percentage/{emp_id}")
def empAttendPerc(emp_id: int, db: Session = Depends(get_db)):

	employee = get_employee_or_404(emp_id, db)

	cache_key = f"attendEmpPerc:{emp_id}"

	try:
		cached_data = redis_client.get(cache_key)
	except Exception:
		cached_data = None
	if cached_data:
		return {
			"source":"redis-cache",
			"data":json.loads(cached_data)
		}

	attendData = db.query(Attendance.employee_id,Attendance.status,Attendance.attendance_date).filter(Attendance.employee_id == emp_id ).all()

	total_work_days = [ data[2] for data in attendData]
	present_days = [ data[1] for data in attendData if data[1]=="Present"]

	attend_perc = ( (len(present_days) / len(total_work_days)) * 100 )

	attend_data = {
		"employee_id": emp_id,
		"total_work_days": len(total_work_days),
		"total_present_days": len(present_days),
		"attendance_percentage": round(attend_perc,2)
	}

	try:
		redis_client.set(cache_key, json.dumps(attend_data), ex=60)
	except Exception:
		pass

	return {
	    "source": "db",
	    "data": attend_data
	}


#-------------- Validate Employee with emp_id If exist -------------#

def get_employee_or_404(emp_id: int, db: Session):

    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == emp_id)
        .first()
    )
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee