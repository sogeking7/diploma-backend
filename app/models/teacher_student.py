from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class TeacherStudent(Base):
    __tablename__ = "teacher_student_relationships"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Indicate which foreign key belongs to teacher vs. student
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="teacher_links")
    student = relationship("User", foreign_keys=[student_id], back_populates="student_links")
