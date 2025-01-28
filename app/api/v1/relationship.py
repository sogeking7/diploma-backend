from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_active_admin  # A dependency that checks if user is admin
from app.crud.parent_child import create_parent_child
from app.crud.teacher_student import create_teacher_student

router = APIRouter()

@router.post("/add-parent-child", status_code=status.HTTP_201_CREATED)
def add_parent_child_relationship(
    parent_id: int,
    child_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_admin)  # Only admin can do this
):
    link = create_parent_child(db, parent_id=parent_id, child_id=child_id)
    return {"message": "Parent-Child relationship created", "relationship_id": link.id}

@router.post("/add-teacher-student", status_code=status.HTTP_201_CREATED)
def add_teacher_student_relationship(
    teacher_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_admin)
):
    link = create_teacher_student(db, teacher_id=teacher_id, student_id=student_id)
    return {"message": "Teacher-Student relationship created", "relationship_id": link.id}
