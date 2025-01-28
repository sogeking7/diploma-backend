from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas
from app.crud import (
    get_attendance,
    get_attendances,
    create_attendance,
    update_attendance,
    delete_attendance
)
from app.api.dependencies import get_db, get_current_active_user
from app.models import User, Attendance, ParentChild, TeacherStudent
from app.models.user import RoleEnum
from datetime import datetime, time
from app.schemas import AttendanceOut

router = APIRouter()

@router.get("/attendances/today/teacher", response_model=list[AttendanceOut])
def get_todays_attendances_for_students(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Get today's attendances (00:00 to 23:59) for a teacher's students.
    """
    # Verify the user is a teacher
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this endpoint."
        )

    # Get the current date (from 00:00 to 23:59)
    today = datetime.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())  # 00:00
    end_of_day = datetime.combine(today, datetime.max.time())  # 23:59

    # Query for the students assigned to the current teacher
    students = (
        db.query(User.id)
        .join(TeacherStudent, TeacherStudent.student_id == User.id)
        .filter(TeacherStudent.teacher_id == current_user.id)
        .all()
    )

    if not students:
        return []  # If there are no students, return an empty list

    student_ids = [student.id for student in students]

    # Query for today's attendances for the teacher's students
    attendances = (
        db.query(Attendance)
        .filter(
            Attendance.user_id.in_(student_ids),
            Attendance.time_in >= start_of_day,
            Attendance.time_in <= end_of_day
        )
        .all()
    )

    # Map attendances to students
    attendance_map = {attendance.user_id: attendance for attendance in attendances}

    # Build the response, including students with no attendance
    result = []
    for student_id in student_ids:
        if student_id in attendance_map:
            result.append(attendance_map[student_id])
        else:
            # Add a default object for students with no attendance
            result.append({
                "id": None,
                "user_id": student_id,
                "time_in": None,
                "time_out": None,
                "created_at": None
            })

    return result


@router.get("/attendances/today", response_model=list[AttendanceOut])
def get_todays_attendances_for_children(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Get today's attendances (00:00 to 23:59) for a parent's children.
    """
    # Verify the user is a parent
    if current_user.role != RoleEnum.parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint."
        )

    # Get the current date (from 00:00 to 23:59)
    today = datetime.now().date()
    start_of_day = datetime.combine(today, time.min)  # 00:00
    end_of_day = datetime.combine(today, time.max)  # 23:59

    # Query for the children of the current parent
    children = (
        db.query(User.id, User.first_name, User.last_name)
        .join(ParentChild, ParentChild.child_id == User.id)
        .filter(ParentChild.parent_id == current_user.id)
        .all()
    )

    if not children:
        return []  # If there are no children, return an empty list

    # Create a dictionary to track attendances for each child
    attendance_records = {child.id: None for child in children}

    # Query for today's attendances for the parent's children
    attendances = (
        db.query(Attendance)
        .filter(
            Attendance.user_id.in_([child.id for child in children]),
            Attendance.time_in >= start_of_day,
            Attendance.time_in <= end_of_day
        )
        .all()
    )

    # Map attendances to the dictionary
    for attendance in attendances:
        attendance_records[attendance.user_id] = attendance

    # Build the final response
    result = []
    for child in children:
        if attendance_records[child.id] is None:
            # If no attendance, return an object with null times
            result.append({
                "id": None,  # No attendance record ID
                "user_id": child.id,
                "time_in": None,
                "time_out": None
            })
        else:
            # Otherwise, include the attendance record
            result.append(attendance_records[child.id])

    return result


@router.get("/child/{child_id}/attendance")
def get_child_attendance(
        child_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # Could be parent or admin
):
    # Check if current_user is a parent of the requested child
    if current_user.role == RoleEnum.parent:
        link = db.query(ParentChild).filter_by(parent_id=current_user.id, child_id=child_id).first()
        if not link:
            raise HTTPException(status_code=403, detail="You are not a parent of this child.")

    # Optionally allow admin or teachers
    # If role=teacher, we might check a teacher-student relationship
    # or if role=admin, skip the relationship check.

    # Now fetch attendance
    attendance_records = db.query(Attendance).filter(Attendance.user_id == child_id).all()
    return attendance_records


@router.get("/student/{student_id}/attendance")
def get_student_attendance(
        student_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    # If teacher, verify the teacher-student link
    if current_user.role == RoleEnum.teacher:
        link = db.query(TeacherStudent).filter_by(teacher_id=current_user.id, student_id=student_id).first()
        if not link:
            raise HTTPException(status_code=403, detail="You are not a teacher of this student.")

    # If admin, skip check or do a different check as needed
    # If role=admin, typically they can see all

    attendance_records = db.query(Attendance).filter(Attendance.user_id == student_id).all()
    return attendance_records


@router.post("/", response_model=schemas.AttendanceOut, status_code=status.HTTP_201_CREATED)
def create_attendance_endpoint(attendance: schemas.AttendanceCreate, db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_active_user)):
    """
    Create a new attendance record.
    """
    # Optional: Verify that the current user is allowed to create attendance for the specified user_id

    if current_user.id != attendance.user_id and current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create attendance for this user."
        )
    db_attendance = create_attendance(db=db, attendance=attendance)
    return db_attendance


@router.get("/", response_model=List[schemas.AttendanceOut])
def read_attendances(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_active_user)):
    """
    Retrieve a list of attendance records.
    """
    # Optional: Filter attendances based on user role
    if current_user.role != RoleEnum.admin:
        attendances = db.query(Attendance).filter(Attendance.user_id == current_user.id).offset(skip).limit(limit).all()
    else:
        attendances = get_attendances(db=db, skip=skip, limit=limit)
    return attendances


@router.get("/{attendance_id}", response_model=schemas.AttendanceOut)
def read_attendance(attendance_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_active_user)):
    """
    Retrieve a specific attendance record by ID.
    """
    db_attendance = get_attendance(db=db, attendance_id=attendance_id)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance record not found.")

    # Optional: Restrict access to the owner or admin
    if current_user.role != RoleEnum.admin and db_attendance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    return db_attendance


@router.put("/{attendance_id}", response_model=schemas.AttendanceOut)
def update_attendance_endpoint(attendance_id: int, updates: schemas.AttendanceUpdate,
                               db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_active_user)):
    """
    Update an existing attendance record.
    """
    db_attendance = get_attendance(db=db, attendance_id=attendance_id)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance record not found.")

    # Optional: Restrict access to the owner or admin
    if current_user.role != RoleEnum.admin and db_attendance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    updated_attendance = update_attendance(db=db, db_attendance=db_attendance, updates=updates)
    return updated_attendance


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance_endpoint(attendance_id: int, db: Session = Depends(get_db),
                               current_user: User = Depends(get_current_active_user)):
    """
    Delete an attendance record.
    """
    db_attendance = get_attendance(db=db, attendance_id=attendance_id)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance record not found.")

    # Optional: Restrict deletion to admin users
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    delete_attendance(db=db, db_attendance=db_attendance)
    return
