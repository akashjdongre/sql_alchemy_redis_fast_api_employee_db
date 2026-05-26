from sqlalchemy import Column, Integer, String
from db import Base
from pydantic import BaseModel

class Departments(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100))
    location = Column(String(20))

# class EmpAttendSummary(BaseModel):
#     department_name : str

# class AttendSummaryWrapper(BaseModel):
#     source: str
#     data: EmpAttendSummary
