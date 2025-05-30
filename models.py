from sqlalchemy import Column, Date, ForeignKey, Integer, String, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import enum

# 요일 Enum
class WeekdayEnum(str, enum.Enum):
    월 = "월"
    화 = "화"
    수 = "수"
    목 = "목"
    금 = "금"

# 차시 Enum
class PeriodEnum(str, enum.Enum):
    first = '1차시'
    second = '2차시'

# 학생 테이블
class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    password = Column(String(200), nullable=False)
    day = Column(Enum(WeekdayEnum), nullable=False)

    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('student_number', 'day', name='uix_student_day'),
    )

    def __repr__(self):
        return f"<Student(id={self.id}, student_number='{self.student_number}', name='{self.name}')>"

# 출석 테이블
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    day = Column(Enum(WeekdayEnum), nullable=False)
    period = Column(Enum(PeriodEnum), nullable=False)
    date = Column(Date, nullable=False)

    student = relationship("Student", back_populates="attendances")

    __table_args__ = (
        UniqueConstraint('student_id', 'day', 'period', 'date', name='uix_attendance_once'),
    )

    def __repr__(self):
        return f"<Attendance(id={self.id}, student_id={self.student_id}, day='{self.day}', period='{self.period}', date='{self.date}')>"
