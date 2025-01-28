from sqlalchemy.orm import Session
from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate

def get_attendance(db: Session, attendance_id: int):
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()

def get_attendances(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Attendance).offset(skip).limit(limit).all()

def create_attendance(db: Session, attendance: AttendanceCreate):
    db_attendance = Attendance(
        user_id=attendance.user_id,
        time_in=attendance.time_in,
        time_out=attendance.time_out
    )
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def update_attendance(db: Session, db_attendance: Attendance, updates: AttendanceUpdate):
    if updates.time_in is not None:
        db_attendance.time_in = updates.time_in
    if updates.time_out is not None:
        db_attendance.time_out = updates.time_out
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def delete_attendance(db: Session, db_attendance: Attendance):
    db.delete(db_attendance)
    db.commit()
