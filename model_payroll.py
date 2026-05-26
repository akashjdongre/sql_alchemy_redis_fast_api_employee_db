from sqlalchemy import Column, Integer, String, Float
from db import Base
from pydantic import BaseModel

class Payroll(Base):
    __tablename__ = "payroll"

    payroll_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer)
    salary_month = Column(String(20)) 
    basic_salary = Column(Float)
    bonus = Column(Float)
    deductions = Column(Float)
    net_salary = Column(Float)


class PayrollNetSalData(BaseModel):
    employee_id: int
    net_salary: float

class PayrollWrapper(BaseModel):
    source: str
    data: PayrollNetSalData