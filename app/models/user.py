from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base
from app.models.parent_child import ParentChild
from app.models.teacher_student import TeacherStudent

class RoleEnum(enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"
    parent = "parent"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)

    # For parent-child
    parent_links = relationship(
        "ParentChild",
        foreign_keys=[ParentChild.parent_id],
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    child_links = relationship(
        "ParentChild",
        foreign_keys=[ParentChild.child_id],
        back_populates="child",
        cascade="all, delete-orphan"
    )

    # For teacher-student
    teacher_links = relationship(
        "TeacherStudent",
        foreign_keys=[TeacherStudent.teacher_id],
        back_populates="teacher",
        cascade="all, delete-orphan"
    )
    student_links = relationship(
        "TeacherStudent",
        foreign_keys=[TeacherStudent.student_id],
        back_populates="student",
        cascade="all, delete-orphan"
    )

    # For attendance
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")
    # For embedding
    embeddings = relationship("UserEmbedding", back_populates="user", cascade="all, delete-orphan")

