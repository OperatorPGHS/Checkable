from pydantic import BaseModel
from typing import List
from enum import Enum

class WeekDay(str, Enum):
    MON = "월"
    TUE = "화"
    WED = "수"
    THU = "목"
    FRI = "금"

class StudentCreate(BaseModel):
    student_number: str
    name: str
    password: str
    days: List[WeekDay]
