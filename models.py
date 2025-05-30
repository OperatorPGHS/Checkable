from sqlalchemy import Column, Integer, String, Enum, UniqueConstraint
from database import Base
import enum

class WeekDay(str, enum.Enum):
    MON = "월"
    TUE = "화"
    WED = "수"
    THU = "목"
    FRI = "금"

class StudentNightStudy(Base):
    __tablename__ = "student_nightstudy"
    id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    day = Column(Enum(WeekDay), nullable=False)

    __table_args__ = (
        UniqueConstraint('student_number', 'day', name='unique_student_day'),
    )
