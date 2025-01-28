from sqlalchemy.orm import Session
from app.models.parent_child import ParentChild

def create_parent_child(db: Session, parent_id: int, child_id: int):
    link = ParentChild(parent_id=parent_id, child_id=child_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def delete_parent_child(db: Session, link_id: int):
    link = db.query(ParentChild).filter(ParentChild.id == link_id).first()
    if link:
        db.delete(link)
        db.commit()
    return link

def get_children_of_parent(db: Session, parent_id: int):
    return db.query(ParentChild).filter(ParentChild.parent_id == parent_id).all()

def get_parents_of_child(db: Session, child_id: int):
    return db.query(ParentChild).filter(ParentChild.child_id == child_id).all()
