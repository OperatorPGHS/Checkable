from sqlalchemy import Column, Integer, String, Enum, UniqueConstraint
from database import Base
import enum

class WeekdayEnum(str, enum.Enum):
    월 = "월"
    화 = "화"
    수 = "수"
    목 = "목"
    금 = "금"

class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    password = Column(String(200), nullable=False)
    day = Column(Enum(WeekdayEnum), nullable=False)

    __table_args__ = (
        UniqueConstraint('student_number', 'day', name='uix_student_day'),
    )
