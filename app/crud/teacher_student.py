from sqlalchemy.orm import Session
from app.models.teacher_student import TeacherStudent

def create_teacher_student(db: Session, teacher_id: int, student_id: int):
    link = TeacherStudent(teacher_id=teacher_id, student_id=student_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def delete_teacher_student(db: Session, link_id: int):
    link = db.query(TeacherStudent).filter(TeacherStudent.id == link_id).first()
    if link:
        db.delete(link)
        db.commit()
    return link

def get_students_of_teacher(db: Session, teacher_id: int):
    return db.query(TeacherStudent).filter(TeacherStudent.teacher_id == teacher_id).all()

def get_teachers_of_student(db: Session, student_id: int):
    return db.query(TeacherStudent).filter(TeacherStudent.student_id == student_id).all()
