from datetime import date
from pydantic import BaseModel, EmailStr, Field, PastDate
from typing import Optional

class EmployeeCreate(BaseModel):
    first_name: str = Field(..., min_length=3, max_length=50)
    last_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone: str = Field(...,pattern=r"\d{10}$")
    job_title: str = Field(..., min_length=5, max_length=100)
    salary: float = Field(..., gt=0) # ... field is required | gt=0   salary must be greater than 0 
    department_id: int
    manager_id: int | None = None
    status: str = "active",
    hire_date: PastDate

class EmployeeUpdate(BaseModel):
    first_name : Optional[str] = Field(None, min_length=3, max_length=50)
    last_name : Optional[str] = Field(None, min_length=3, max_length=50)
    email : Optional[EmailStr] = None
    phone : Optional[str] = Field(None, pattern=r"\d{10}$")
    job_title : Optional[str] = Field(None, min_length=5, max_length=100)
    salary : Optional[float] = Field(None, gt=0) 

class EmployeeAttendSummary(BaseModel):
    status : Optional[str] = Field(None, min_length=3, max_length=50)

class EmployeeSearch(BaseModel):
    name : Optional[str] = Field(None, min_length=3, max_length=50)
    department : Optional[str] = Field(None, min_length=3, max_length=50)
    status : Optional[str] = Field(None, min_length=3, max_length=50)
