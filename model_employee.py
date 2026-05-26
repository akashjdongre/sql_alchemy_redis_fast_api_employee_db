from sqlalchemy import Column, Integer, String
from db import Base
from pydantic import BaseModel

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    salary = Column(String(20))
    job_title = Column(String(20))
    department_id = Column(Integer)
    manager_id = Column(Integer)
    status = Column(String(20))
    hire_date = Column(String(20))

class EmployeeResponse(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    email: str
    phone: str

    class Config:
        from_attributes = True

class OneEmployeeResponse(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    salary: float

    class Config:
        from_attributes = True

# SINGLE employee respons  
class EmployeeWrapper(BaseModel):
    source: str
    data: OneEmployeeResponse

# MULTIPLE employee response
class EmployeesWrapper(BaseModel):
    source: str
    data: list[EmployeeResponse]
    count: int


class DeptEmployeeResponse(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    job_title: str
    department_name: str

class DeptEmployeeWrapper(BaseModel):
    source: str
    data: list[DeptEmployeeResponse]

