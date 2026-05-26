from sqlalchemy import Column, Integer, String
from db import Base
from pydantic import BaseModel

class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer)
    attendance_date = Column(String(20)) 
    check_in = Column(String(100))
    check_out = Column(String(100))
    status = Column(String(20))

class EmpAttendSummary(BaseModel):
    employee_id: int
    present: int
    absent: int
    half_day: int
    late: int

class AttendSummaryWrapper(BaseModel):
    source: str
    data: EmpAttendSummary

class EmpAttendSummaryTest(BaseModel):
    employee_id: int
    total_work_days: int
    total_present_days: int
    attendance_percentage: float

class AttendPercentWrapper(BaseModel):
    source: str
    data: EmpAttendSummaryTest